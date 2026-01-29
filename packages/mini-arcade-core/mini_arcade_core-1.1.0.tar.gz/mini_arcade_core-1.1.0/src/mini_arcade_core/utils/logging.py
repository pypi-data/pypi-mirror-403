"""
Logging utilities for Mini Arcade Core.
Provides a console logger with colored output and class/function context.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional


def _classname_from_locals(locals_: dict) -> Optional[str]:
    """Retrieve the class name from locals dict, if available."""
    self_obj = locals_.get("self")
    if self_obj is not None:
        return type(self_obj).__name__
    cls_obj = locals_.get("cls")
    if isinstance(cls_obj, type):
        return cls_obj.__name__
    return None


class EnsureClassName(logging.Filter):
    """
    Populate record.classname by finding the *emitting* frame:
    match by (pathname, funcName) and read self/cls from its locals.
    Falls back to "-" when not in a class context.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # record_factory ensures classname exists, but allow explicit override
        if getattr(record, "classname", None) not in (None, "-"):
            return True

        target_path = record.pathname
        target_func = record.funcName

        # Justification: Seems pretty obvious here.
        # pylint: disable=protected-access
        f = sys._getframe()
        # pylint: enable=protected-access

        for _ in range(200):
            if f is None:
                break
            code = f.f_code
            if code.co_filename == target_path and code.co_name == target_func:
                record.classname = _classname_from_locals(f.f_locals) or "-"
                return True
            f = f.f_back

        record.classname = "-"
        return True


class ConsoleColorFormatter(logging.Formatter):
    """
    Console formatter with ANSI colors by log level.
    """

    COLORS = {
        logging.DEBUG: "\033[96m",  # Cyan
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[95m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.COLORS["RESET"])
        msg = super().format(record)
        return f"{color}{msg}{self.COLORS['RESET']}"


LOGGER_FORMAT = (
    "%(asctime)s [%(levelname)-8.8s] [%(name)s] "
    "%(module)s.%(classname)s.%(funcName)s: "
    "%(message)s (%(filename)s:%(lineno)d)"
)


def _enable_windows_ansi():
    """
    Best-effort enable ANSI escape sequences on Windows terminals.
    Newer Windows 10/11 terminals usually support this already.
    """
    if os.name != "nt":
        return
    try:
        # Enables VT100 sequences in some consoles; harmless if unsupported
        # Justification: Importing ctypes only on Windows is acceptable.
        # pylint: disable=import-outside-toplevel
        import ctypes

        # pylint: enable=import-outside-toplevel

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            # ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    # Justification: We want to catch all exceptions here.
    # pylint: disable=broad-exception-caught
    except Exception:
        # If it fails, we just keep going without breaking logging.
        pass
    # pylint: enable=broad-exception-caught


def _install_record_factory_defaults():
    """
    Ensure every LogRecord has `classname` so formatters never crash.
    Safe to call multiple times; we keep the current factory chain.
    """
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        if not hasattr(record, "classname"):
            record.classname = "-"
        return record

    logging.setLogRecordFactory(record_factory)


def configure_logging(level: int = logging.DEBUG):
    """
    Configure logging once for the whole app (root logger).
    Call this early (app entrypoint). Safe to call multiple times.
    """
    _enable_windows_ansi()
    _install_record_factory_defaults()

    root = logging.getLogger()
    root.setLevel(level)

    # Avoid duplicate handlers if reloaded/imported multiple times
    # We tag our handler so we can find it reliably.
    handler_tag = "_mini_arcade_core_console_handler"

    for h in list(root.handlers):
        if getattr(h, handler_tag, False):
            # Already configured
            return

    console = logging.StreamHandler(stream=sys.stdout)
    setattr(console, handler_tag, True)

    console.setFormatter(ConsoleColorFormatter(LOGGER_FORMAT))
    console.addFilter(EnsureClassName())

    # Important: don’t leave any basicConfig handlers around if someone called it earlier
    # We remove only the plain StreamHandlers that don't have our tag.
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler) and not getattr(
            h, handler_tag, False
        ):
            root.removeHandler(h)

    root.addHandler(console)


configure_logging()
logger = logging.getLogger("mini-arcade-core")
