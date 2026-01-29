import os
import sys
import re
import inspect
from loguru import logger
from lbkit.misc import LOG_DIR
from functools import partial


class Logger:
    _configured = False
    _logfile = None
    _lock = False

    def __init__(self, logfile=None):
        if logfile:
            if not re.match('^[a-zA-Z0-9_.-]*[a-zA-Z0-9]$', logfile):
                raise Exception("The logname parameter is in an incorrect format.")
            self.logfile = os.path.join(LOG_DIR, logfile)
        else:
            self.logfile = None
        self.logenv = os.environ.get("LOG")

        self._configure_loguru()
        self._configure_logfile()
        self._logger = logger

    def _configure_logfile(self):
        # Configure loguru with logfile only once for all Logger instances
        if not self.logfile or Logger._logfile or Logger._lock:
            return

        Logger._lock = True
        Logger._logfile = self.logfile
        logger.add(
            self.logfile,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} {extra[file]}:{extra[fileno]} - <level>{message}</level>",
            rotation="20 MB",
            retention="30 days",
            compression="zip",
            level="DEBUG",
            colorize=None
        )
        Logger._lock = False

    def _configure_loguru(self):
        """Configure loguru handlers (called only once)"""

        # Configure loguru only once for all Logger instances
        if Logger._configured or Logger._lock:
            return
        Logger._lock = True

        # Remove default handler
        logger.remove()

        # Determine log level and format
        if self.logenv is None:
            level = "INFO"
            format_str = "<level>{message}</level>"
        else:
            format_str = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} {extra[file]}:{extra[fileno]} - <level>{message}</level>"
            if self.logenv == "info":
                level = "INFO"
            elif self.logenv == "warn":
                level = "WARNING"
            elif self.logenv == "error":
                level = "ERROR"
            else:
                level = "DEBUG"

        # Add handler for non-error messages (stdout)
        logger.add(
            sys.stdout,
            format=format_str,
            level=level,
            filter=lambda record: record["level"].no < 40 and "tofile" not in record["extra"],  # < ERROR level
            colorize=None
        )

        # Add handler for error messages (stderr)
        logger.add(
            sys.stderr,
            format=format_str,
            level="ERROR",
            filter= lambda record: "tofile" not in record["extra"],
            colorize=None
        )
        Logger._configured = True
        Logger._lock = False

    @staticmethod
    def _patch_with_args(record, file, fileno):
        record["extra"]["file"] = file
        record["extra"]["fileno"] = fileno

    def _patch_logger(self, uptrace, **kwargs):
        uptrace = uptrace
        file = kwargs.get("file", None)
        fileno = kwargs.get("fileno", 0)
        if not file:
            stack = inspect.stack()[uptrace + 1]
            file = os.path.basename(stack.filename)
            fileno = stack.lineno
        patcher = partial(self._patch_with_args, file=file, fileno=fileno)
        return self._logger.opt(depth=uptrace).patch(patcher)

    def _format_message(self, msg, *args):
        """Format message with prefix, location, and color"""
        # Format message with args if provided
        if args:
            msg = msg % args
        return msg

    def logger(self):
        return self._logger

    def error(self, msg, *args, **kwargs):
        uptrace = kwargs.pop("uptrace", 0) + 1
        formatted_msg = self._format_message(msg, *args)
        self._patch_logger(uptrace, **kwargs).error(formatted_msg)

    def debug(self, msg, *args, **kwargs):
        uptrace = kwargs.pop("uptrace", 0) + 1
        formatted_msg = self._format_message(msg, *args)
        self._patch_logger(uptrace, **kwargs).debug(formatted_msg)

    def info(self, msg, *args, **kwargs):
        uptrace = kwargs.pop("uptrace", 0) + 1
        formatted_msg = self._format_message(msg, *args)
        self._patch_logger(uptrace, **kwargs).info(formatted_msg)

    def warn(self, msg, *args, **kwargs):
        uptrace = kwargs.pop("uptrace", 0) + 1
        formatted_msg = self._format_message(msg, *args)
        self._patch_logger(uptrace, **kwargs).warning(formatted_msg)

    def success(self, msg, *args, **kwargs):
        uptrace = kwargs.pop("uptrace", 0) + 1
        formatted_msg = self._format_message(msg, *args)
        self._patch_logger(uptrace, **kwargs).success(formatted_msg)
