# msui/log.py
from __future__ import annotations

import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional


# ---------------------------
# Levels
# ---------------------------

PROFILE = 15  # between DEBUG(10) and INFO(20)
logging.addLevelName(PROFILE, "PROFILE")


def _logger_profile(self: logging.Logger, msg: str, *args: Any, **kwargs: Any) -> None:
    if self.isEnabledFor(PROFILE):
        self._log(PROFILE, msg, args, **kwargs)


if not hasattr(logging.Logger, "profile"):
    logging.Logger.profile = _logger_profile  # type: ignore[attr-defined]


# ---------------------------
# Formatters
# ---------------------------

def _iso_utc(ts: float) -> str:
    # 2026-01-10T12:34:56.789Z
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


class JsonFormatter(logging.Formatter):
    """
    Emits one JSON object per line.

    We store structured data under:
      - record.msui_ctx: dict (logger context, e.g. component/class)
      - record.msui_fields: dict (per-call fields)
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": _iso_utc(record.created),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        # Context (static)
        ctx = getattr(record, "msui_ctx", None)
        if isinstance(ctx, dict) and ctx:
            payload.update(ctx)

        # Fields (per call)
        fields = getattr(record, "msui_fields", None)
        if isinstance(fields, dict) and fields:
            payload.update(fields)

        # Exception
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class PrettyFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = _iso_utc(record.created)
        base = f"{ts} {record.levelname:<7} {record.name}: {record.getMessage()}"

        ctx = getattr(record, "msui_ctx", None)
        fields = getattr(record, "msui_fields", None)

        extras: Dict[str, Any] = {}
        if isinstance(ctx, dict):
            extras.update(ctx)
        if isinstance(fields, dict):
            extras.update(fields)

        if extras:
            base += "  " + json.dumps(extras, ensure_ascii=False)

        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)

        return base


# ---------------------------
# Structured logger wrapper
# ---------------------------

@dataclass(frozen=True)
class StructLogger:
    _logger: logging.Logger
    _ctx: Dict[str, Any]

    def bind(self, **ctx: Any) -> "StructLogger":
        c = dict(self._ctx)
        c.update(ctx)
        return StructLogger(self._logger, c)

    def _log(self, level: int, msg: str, *args: Any, exc_info: bool = False, **fields: Any) -> None:
        if not self._logger.isEnabledFor(level):
            return

        extra = {
            "msui_ctx": self._ctx,
            "msui_fields": fields,
        }
        self._logger.log(level, msg, *args, extra=extra, exc_info=exc_info)

    def debug(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **fields)

    def info(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.INFO, msg, *args, **fields)

    def warn(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.WARNING, msg, *args, **fields)

    def error(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.ERROR, msg, *args, **fields)

    def exception(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.ERROR, msg, *args, exc_info=True, **fields)

    def profile(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(PROFILE, msg, *args, **fields)


# ---------------------------
# Configuration / factory
# ---------------------------

_CONFIGURED = False


def configure() -> None:
    """
    Idempotent logging setup.

    Env vars:
      - MSUI_LOG_LEVEL: DEBUG|INFO|WARN|WARNING|ERROR|PROFILE
      - MSUI_LOG_FORMAT: json|pretty  (default: pretty if TTY else json)
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_str = os.getenv("MSUI_LOG_LEVEL", "INFO").upper().strip()
    fmt_str = os.getenv("MSUI_LOG_FORMAT", "").lower().strip()

    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARN": logging.WARNING,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "PROFILE": PROFILE,
    }
    level = level_map.get(level_str, logging.INFO)

    if not fmt_str:
        fmt_str = "pretty" if sys.stdout.isatty() else "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if fmt_str == "pretty":
        handler.setFormatter(PrettyFormatter())
    else:
        handler.setFormatter(JsonFormatter())

    root = logging.getLogger("msui")
    root.setLevel(level)
    root.propagate = False

    # Replace handlers to avoid duplicates on reload
    root.handlers.clear()
    root.addHandler(handler)

    _CONFIGURED = True


def get_logger(name: str = "msui", **ctx: Any) -> StructLogger:
    """
    Usage:
      log = get_logger(__name__, component="controls", cls="DialControl")
      log.info("hello", x=1)
    """
    configure()
    base = logging.getLogger(name if name.startswith("msui") else f"msui.{name}")
    return StructLogger(base, dict(ctx))


# ---------------------------
# Mixin: auto logger per class
# ---------------------------

class LogMixin:
    """
    Inherit this and you get:
      - cls.log  (a StructLogger bound to module+class)
      - self.log usable too

    Example:
      class Foo(LogMixin):
          def bar(self):
              self.log.debug("hi", n=123)
    """

    log: StructLogger

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.log = get_logger(f"{cls.__module__}.{cls.__name__}", cls=cls.__name__)


# ---------------------------
# Back-compat helpers (your existing calls)
# ---------------------------

# Module logger for simple calls (log.info("x"))
_default = get_logger("msui")


def debug(*args: Any, **fields: Any) -> None:
    _default.debug(" ".join(map(str, args)), **fields)


def info(*args: Any, **fields: Any) -> None:
    _default.info(" ".join(map(str, args)), **fields)


def warn(*args: Any, **fields: Any) -> None:
    _default.warn(" ".join(map(str, args)), **fields)


def error(*args: Any, **fields: Any) -> None:
    _default.error(" ".join(map(str, args)), **fields)


def profile(*args: Any, **fields: Any) -> None:
    # kept same semantics: enabled whenever INFO is enabled, unless user sets PROFILE explicitly
    _default.profile(" ".join(map(str, args)), **fields)
