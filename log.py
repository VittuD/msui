# msui/log.py
from __future__ import annotations

from typing import Any

# Re-export the stable public API from msui.logger
from msui.logger import Logger, LogMixin, PROFILE, context, get_logger, log

__all__ = [
    "Logger",
    "LogMixin",
    "PROFILE",
    "context",
    "get_logger",
    "log",
    # helpers
    "debug",
    "info",
    "warn",
    "warning",
    "error",
    "profile",
    "is_debug_enabled",
]


# ---------------------------
# Back-compat module-level helpers
# ---------------------------

def debug(*args: Any, **fields: Any) -> None:
    log.debug(" ".join(map(str, args)), **fields)


def info(*args: Any, **fields: Any) -> None:
    log.info(" ".join(map(str, args)), **fields)


def warn(*args: Any, **fields: Any) -> None:
    log.warn(" ".join(map(str, args)), **fields)


def warning(*args: Any, **fields: Any) -> None:
    # some codebases use warning(), keep it available
    log.warning(" ".join(map(str, args)), **fields)


def error(*args: Any, **fields: Any) -> None:
    log.error(" ".join(map(str, args)), **fields)


def profile(*args: Any, **fields: Any) -> None:
    log.profile(" ".join(map(str, args)), **fields)


def is_debug_enabled() -> bool:
    return log.is_debug_enabled()
