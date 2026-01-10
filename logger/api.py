# msui/logger/api.py
from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from .config import PROFILE, configure, normalize_logger_name
from .runtime import BoundLogger, StructLogger, context


@runtime_checkable
class Logger(Protocol):
    """
    Stable logger API: anything exposed to the rest of the app should conform to this.
    """

    def debug(self, msg: str, *args: Any, **fields: Any) -> None: ...
    def info(self, msg: str, *args: Any, **fields: Any) -> None: ...
    def warning(self, msg: str, *args: Any, **fields: Any) -> None: ...
    def error(self, msg: str, *args: Any, **fields: Any) -> None: ...
    def profile(self, msg: str, *args: Any, **fields: Any) -> None: ...

    # legacy alias in this repo
    def warn(self, msg: str, *args: Any, **fields: Any) -> None: ...

    def exception(self, msg: str, *args: Any, **fields: Any) -> None: ...

    def bind(self, **fields: Any) -> "Logger": ...
    def child(self, name: str) -> "Logger": ...

    def is_enabled(self, level: str) -> bool: ...
    def is_debug_enabled(self) -> bool: ...

    def context(self, **fields: Any) -> Any: ...


def get_logger(name: str = "msui", **ctx: Any) -> Logger:
    """
    Usage:
      log = get_logger(__name__, cls="DialControl")
      log.info("hello", x=1)
    """
    configure()
    full = normalize_logger_name(name)
    base = StructLogger(logging.getLogger(full))
    return BoundLogger(base, dict(ctx))


class LogMixin:
    """
    Inherit this and you get:
      - cls.log  (a Logger bound to module + class)
      - self.log usable too

    Standardizes cls binding here (do not bind cls per log line elsewhere).
    """

    log: Logger

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)

        # Logger name: msui.<module>.<ClassName>
        # Bound fields: cls=<ClassName>
        module_logger = get_logger(cls.__module__)
        cls.log = module_logger.child(cls.__name__).bind(cls=cls.__name__)


# Root logger object usable via:
#   from msui import log
#   log.info(...)
log: Logger = get_logger("msui")

__all__ = [
    "Logger",
    "LogMixin",
    "get_logger",
    "log",
    "context",
    "PROFILE",
]
