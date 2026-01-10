# msui/log.py
from __future__ import annotations

import os
import sys
from typing import Any


_LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}
_level = _LEVELS.get(os.getenv("MSUI_LOG_LEVEL", "INFO").upper(), 20)


def _emit(prefix: str, *args: Any) -> None:
    print(prefix, *args, file=sys.stdout, flush=True)


def debug(*args: Any) -> None:
    if _level <= 10:
        _emit("[DBG]", *args)


def info(*args: Any) -> None:
    if _level <= 20:
        _emit("[INF]", *args)


def warn(*args: Any) -> None:
    if _level <= 30:
        _emit("[WRN]", *args)


def error(*args: Any) -> None:
    if _level <= 40:
        _emit("[ERR]", *args)


def profile(*args: Any) -> None:
    """
    Convenience channel for perf prints.
    Enabled whenever INFO is enabled (default).
    """
    if _level <= 20:
        _emit("[PRF]", *args)
