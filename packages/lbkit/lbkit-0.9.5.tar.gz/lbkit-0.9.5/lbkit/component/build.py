"""组件构建"""
import os
import yaml
import shlex
import re
import json
from multiprocessing import Pool
import traceback
from argparse import ArgumentParser
from jsonschema import validate, ValidationError
from git import Repo
from git.exc import InvalidGitRepositoryError
from mako.lookup import TemplateLookup
from lbkit.misc import load_yml_with_json_schema_validate, get_json_schema_file, load_json_schema
from lbkit import errors
from lbkit.codegen.codegen import CodeGen, history_versions
from lbkit.tools import Tools
from lbkit.log import Logger
from lbkit.build_conan_parallel import BuildConanParallel
from lbkit.codegen.codegen import Version

tools = Tools()
log = tools.log
lb_cwd = os.path.split(os.path.realpath(__file__))[0]


class DeployComponent():
    def __init__(self, package_ref, package_id, rootfs_dir):
        self.package_ref = package_ref
        self.package_id = package_id
        self.rootfs_dir = rootfs_dir

    def run(self):
        if self.package_ref.startswith("deploy"):
            return
        cmd = f"conan cache path {self.package_ref}:{self.package_id}"
        package_folder = tools.run(cmd).stdout.strip()
        log.info(f">>>> deploy {self.package_ref}")
        cmd = f"cp -rT {package_folder}/ {self.rootfs_dir}"
        cnt = 10
        while cnt > 0:
            try:
                cnt -= 1
                tools.exec(cmd)
                return
            except Exception as e:
                if cnt == 0:
                    log.warn("Copy failed, msg: " + str(e))
                    raise e
                log.info("Copy {self.package_ref} failed, try again")


class BuildComponent():
    def __init__(self, args_parser: ArgumentParser, args=None):
        self.cwd = os.getcwd()
        Logger("build_comp.log")
        self.deploy_success = True
        self.options = args_parser.parse_args(args)
        self.options.build_type = self.options.build_type.capitalize()
        if self.options.channel is None or self.options.channel.strip() == "":
            raise errors.ArgException("请正确指定-c, --channel指定conan包的channel通道")
        self.channel = self.options.channel
        self.build_type = self.options.build_type
        self.profile = self.options.profile
        self.profile_build = self.options.profile_build
        self.verbose = False if self.options.summary else True
        self.from_source = self.options.from_source
        # 当前组件及其依赖将被部署到rootfs目录
        self.rootfs_dir = os.path.join(self.cwd, ".temp", "rootfs")
        tools.makedirs(self.rootfs_dir, True, True)
        self.conan_index = os.path.join(self.cwd, ".temp", "conan-index")
        tools.makedirs(self.conan_index, True, True)
        self.enable_tar_source = self.options.tar_source
        self.source_file = os.path.join(self.cwd, ".temp", "source.tar.gz")
        self.graphfile = os.path.join(self.cwd, ".temp", "graph.info")
        self.lockfile = os.path.join(self.cwd, ".temp", "conan.lock")
        self.orderfile = os.path.join(self.cwd, ".temp", "graph.order")
        # 当组件构建完成后可以获取到包id, 初始化时置空
        self.package_id = None

        self.pkg = None
        self.base_cmd = ""

        self.codegen_version = Version(self.options.codegen_version)
        os.environ["CODEGEN_VERSION"] = self.codegen_version.str
        self.gen_conaninfo()
        # 此场景发布的包名不带@user/channel
        if self.user != "litebmc" or self.channel != "release":
            self.base_cmd += f" --user {self.user} --channel {self.channel}"

        self.base_cmd += f" -pr {self.profile} -s build_type={self.build_type} -r " + self.options.remote
        self.base_cmd += f" -pr:b {self.profile_build}"
        if self.options.cov:
            self.base_cmd += f" -o {self.name}/*:gcov=True"
        if self.options.test:
            self.base_cmd += f" -o {self.name}/*:test=True"
        for pkg_option in self.options.pkg_options:
            self.base_cmd += " -o " + pkg_option
        self.base_cmd += f" -o */*:codegen_version={self.options.codegen_version}"
        if self.name == "lb_base":
            self.base_cmd += f" -o */*:compatible_required={self.codegen_version.info.lb_base_compatible_required}"

    @staticmethod
    def _check_conanfile_if_tracked():
        """检查conanfile.py是否被git跟踪"""
        tracked = False
        try:
            repo = Repo(".")
            for entry in repo.commit().tree.traverse():
                if entry.path == "conanfile.py":
                    tracked = True
                    break
        except InvalidGitRepositoryError:
            log.debug("Invalid git repository")
            return
        if tracked:
            raise Exception("conanfile.py is being tracked by git. You can untrack it by executing the command `git rm --f conanfile.py`")

    def get_package_version(self):
        """
        从CMakeLists.txt读取版本号，格式需要满足正则表达式：project\((.*)VERSION ([0-9][1-9]*.[0-9][1-9]*.[0-9][1-9]*)\)
        示例: project(gcom LANGUAGES C VERSION 0.1.0)
        """
        try:
            with open("CMakeLists.txt", "r") as fp:
                content = fp.read()
            version = re.search("project\((.*)VERSION ([0-9][1-9]*.[0-9][1-9]*.[0-9][1-9]*)\)", content).group(2)
            return version.strip()
        except Exception as e:
            print(str(e))
            return None

    def tar_source(self, tar_path):
        """
        将self.cwd目录下未被git跟踪的文件使用tar命令压缩到tar_path

        :param tar_path: tar压缩包路径
        """
        untracked_files = [".temp"]
        if os.path.exists("test_package/test_interface"):
            untracked_files.append("test_package/test_interface")
        if os.path.exists("conanfile.py"):
            untracked_files.append("conanfile.py")
        if os.path.exists("__pycache__"):
            untracked_files.append("__pycache__")
        if os.path.exists(".git"):
            untracked_files.append(".git")
        if os.path.exists(".gitignore"):
            untracked_files.append(".gitignore")

        try:
            repo = Repo(self.cwd)
            # 获取未被跟踪的文件
            untracked_files.extend(repo.untracked_files)
        except InvalidGitRepositoryError:
            raise errors.LiteBmcException(f"{self.cwd} is not a valid git repository")

        # 构建tar命令，使用-C指定工作目录
        cmd_parts = ["tar", "--format=gnu", "-czf", tar_path, f"--transform=s|^.|{self.version}|", "-C", self.cwd]
        for file in untracked_files:
            cmd_parts.append("--exclude=" + file)
        cmd_parts.append(".")
        cmd = " ".join(shlex.quote(part) for part in cmd_parts)

        tools.exec(cmd, verbose=True)
        log.info(f"Archived {len(untracked_files)} untracked files to {tar_path}")

    def gen_conaninfo(self):
        package_yml = os.path.join(self.cwd, "metadata/package.yml")
        if not os.path.isfile(package_yml):
            raise FileNotFoundError("metadata/package.yml文件不存在")
        # 验证失败时抛异常，此处不用处理，由外层处理
        pkg = load_yml_with_json_schema_validate(package_yml, "/usr/share/litebmc/schema/cdf.v1.json")
        log.info(f"validate {package_yml} successfully")

        self.user = pkg.get("user")
        if self.user is None:
            raise errors.PackageConfigException("metadata/package.yml未正确配置user字段")
        # 构建命令未指定channel时从package.yml中读取
        pkg["channel"] = self.channel
        pkg["version"] = self.get_package_version()
        # 从package.yml加载基础信息
        self.name = pkg.get("name")
        self.version = pkg.get("version")
        self.tar_source(self.source_file)
        pkg["source_url"] = self.source_file
        pkg["sha256"] = tools.file_digest_sha256(self.source_file)
        pkg["enable_tar_source"] = self.enable_tar_source
        pkg["source_dir"] = self.cwd
        self.pkg = pkg

        self.package = self.name + "/" + self.version
        if self.user != "litebmc" or self.channel != "release":
            self.package += "@" + self.user + "/" + self.channel
        # 准备部署依赖
        requires = pkg.get("requires")
        deps = []
        if requires is not None:
            if self.options.test:
                for rt in requires.get("test", []):
                    deps.append(rt)
            for rt in requires.get("compile", []):
                deps.append(rt)

        for dep in deps:
            option = dep.get("option", {})
            conan = dep.get("conan").split("/")[0]
            for k, v in option.items():
                self.base_cmd += f" -o {conan}/*:{k}={v}"

        # 检查git是是否跟踪conanfile.py
        self._check_conanfile_if_tracked()
        conanfile = os.path.join(self.conan_index, "conanfile.py")

        # 使用litebmc.conanfile.mako模板生成基础litebmc公共conanfile
        lookup = TemplateLookup(directories=os.path.join(lb_cwd, "template"))
        template = lookup.get_template("conanbase.mako")
        conandata = template.render(lookup=lookup, pkg=pkg,
                                    codegen_version=self.codegen_version,
                                    codegen_history=history_versions)
        # 写入文件
        fp = open(conanfile, "w")
        fp.write(conandata)
        fp.close()

    def upload(self):
        log.success(f"start upload {self.package}")
        cmd = "conan upload {}# -r {}".format(
            self.package, self.options.remote)
        if self.options.upload_recipe:
            cmd += " --only-recipe"
        tools.exec(cmd, verbose=True)

    def _copy_failed(self, result):
        print(result)
        self.deploy_success = False

    def deploy(self, graphfile):
        with open(graphfile, "r") as fp:
            graph = json.load(fp)
        nodes = graph.get("graph", {}).get("nodes", {})
        pool = Pool()
        for id, info in nodes.items():
            ref = info.get("ref")
            id = info.get("package_id")
            context = info.get("context")
            if context != "host":
                continue
            if ref.startswith(self.package):
                self.package_id = id
            dep = DeployComponent(ref, id, self.rootfs_dir)
            pool.apply_async(dep.run, error_callback=self._copy_failed)
        pool.close()
        pool.join()

    def build(self):
        log.info(os.getcwd())
        os.chdir(self.conan_index)
        export_cmd = "conan export . "
        if self.user != "litebmc" or self.channel != "release":
            export_cmd += f"--user={self.user} --channel={self.channel}"
        tools.exec(export_cmd, verbose=True)

        graph_cmd = f"conan graph build-order . {self.base_cmd} --order-by=recipe -f json --out-file={self.orderfile}"
        if self.from_source:
            graph_cmd += " --build='*'"
        else:
            graph_cmd += " --build=missing"
        graph_cmd += f" --lockfile-out={self.lockfile}"
        tools.exec(graph_cmd, verbose=True)
        bcp = BuildConanParallel(self.orderfile, self.lockfile, self.options.remote)
        bcp.build()
        cmd = f"conan create {self.base_cmd} --build='{self.name}/*'"
        tools.exec(cmd, verbose=True)

        graph_cmd = f"conan graph info . {self.base_cmd} -f json --lockfile={self.lockfile}"
        tools.pipe([graph_cmd], out_file=self.graphfile)

        log.success(f"start deploy {self.package} and is's dependency packages")
        self.deploy(self.graphfile)

        if not self.deploy_success:
            raise Exception("Deploy component failed")

        # 设置ROOTFS_DIR环境变量，为DT测试提供相对路径
        os.environ["ROOTFS_DIR"] = self.rootfs_dir
        os.chdir(self.cwd)

    def _validate_odf_object(self, name, obj):
        properties = obj.get("properties")
        # ODF支持properties置空，所以为None时免验证
        if properties is None:
            return True
        intf = name.split("_")[0]
        intf_schema = f"usr/share/litebmc/schema/{intf}.json"
        real_schema = os.path.join(self.rootfs_dir, intf_schema)
        real_schema = os.path.relpath(real_schema, os.getcwd())
        log.info(f"Start validate object {name} with schema {real_schema}")
        if not os.path.exists(real_schema):
            log.error(f"The scheme file {real_schema} of interface not exist, validate object {name} failed")
            return False
        try:
            schema = load_json_schema(real_schema)
            validate(properties, schema)
        except FileNotFoundError as exc:
            log.error(f"validate object {name} failed, schema {real_schema} not exist, message: {str(exc)}\n")
        except ValidationError as exc:
            log.error(f"validate object {name} failed, schema {real_schema}, message: {exc.message}\n")
            if os.environ.get("LOG"):
                print(traceback.format_exc())
            return False
        return True

    def _validate_odf_file(self, file):
        ok = True
        with open(file, "r") as fp:
            odf = yaml.load(fp, yaml.FullLoader)
            objects = odf.get("objects", {})
            for name, obj in objects.items():
                obj_ok = self._validate_odf_object(name, obj)
                if not obj_ok:
                    ok = False
        return ok

    def _validate_odf_files(self):
        log.success("Start validate ODF files")
        ok = True
        for root, _, files in os.walk(self.rootfs_dir):
            for file in files:
                file = os.path.join(root, file)
                file = os.path.relpath(file, self.cwd)
                if not file.endswith(".yaml"):
                    log.debug(f"file {file} not endswith .yaml, skip validate")
                    continue

                schema_file = get_json_schema_file(file, None)
                if schema_file is None:
                    log.debug(f"the file {file} don't has validate 'yaml-language-server:', maybe not a valid odf file, skip it")
                    continue
                basename = os.path.basename(schema_file)
                if not re.match("^odf\\.v[0-9]+\\.json$", basename):
                    log.debug(f"the schema of file not match '^odf\\.v[0-9]+\\.json$', maybe not a valid odf file, skip it")
                    continue
                log.info(f"start validate {file} with schema {schema_file}")
                # 验证全局odf验证
                load_yml_with_json_schema_validate(file, schema_file)
                odf_ok = self._validate_odf_file(file)
                if not odf_ok:
                    ok = False
        if not ok:
            raise errors.OdfValidateException("Validate odf files with error, build failed")

    def conan_test(self):
        # 仅测试远程仓登录状态，如果需要登录的，需要输入账号密码
        log.info("Test the login status of the Conan remote repository")
        log.info("If glib/2.81.0 not found, you must add litebmc repository using the command: conan remote add litebmc  https://litebmc.com/conan/release")
        cmd = "conan search glib/2.81.0"
        if self.options.remote:
            cmd += f' -r {self.options.remote}'
        tools.run(cmd, capture_output=False)

    def run(self):
        cmd = f"conan remove {self.package} -c"
        tools.exec(cmd)
        self.conan_test()
        gen = CodeGen(["-c", "./metadata/package.yml"])
        gen.run()
        # 部署依赖
        self.build()
        # start validate all odf(Object Description file) files
        self._validate_odf_files()
        if self.options.upload_recipe or self.options.upload_package:
            self.upload()
        log.success(f"build {self.package} successfully")

    @staticmethod
    def package_folder(self):
        cmd = f"conan cache path {self.package}#latest:{self.package_id}"
        res = tools.run(cmd, capture_output=True)
        return res.stdout.strip()

    @property
    def build_folder(self):
        cmd = f"conan cache path {self.package}#latest:{self.package_id} --folder=build"
        res = tools.run(cmd, capture_output=True)
        return res.stdout.strip()

    def test(self):
        try:
            self.run()
        except Exception as e:
            log.error(f"build {self.package} failed")
            log.info(e)
            os._exit(-2)
