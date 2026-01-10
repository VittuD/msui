# msui/logger/config.py
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict

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
      - record.msui_ctx: dict (bound + ambient)
      - record.msui_fields: dict (per-call fields)
    """

    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "ts": _iso_utc(record.created),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }

        ctx = getattr(record, "msui_ctx", None)
        if isinstance(ctx, dict) and ctx:
            payload.update(ctx)

        fields = getattr(record, "msui_fields", None)
        if isinstance(fields, dict) and fields:
            payload.update(fields)

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
# Configuration / helpers
# ---------------------------

_CONFIGURED = False


def configure() -> None:
    """
    Idempotent logging setup.

    Env vars:
      - MSUI_LOG_LEVEL: DEBUG|INFO|WARN|WARNING|ERROR|PROFILE
      - MSUI_LOG_FORMAT: json|pretty  (default: pretty if TTY else json)
      - MSUI_LOG_NOISE: 0|1 (default: 1)
      - MSUI_LOG_SAMPLING: JSON dict mapping "logger_prefix:msg" -> N (keep 1/N)
          e.g. {"msui.backends.input_pygame:event": 10}
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

    # Replace handlers to avoid duplicates (e.g. reload)
    root.handlers.clear()
    root.addHandler(handler)

    _CONFIGURED = True


def normalize_logger_name(name: str) -> str:
    name = (name or "msui").strip()
    if name == "msui":
        return "msui"
    if name.startswith("msui."):
        return name
    if name.startswith("msui"):
        return name
    return f"msui.{name}"


def level_from_str(level: str) -> int:
    s = (level or "").strip().upper()
    if s == "DEBUG":
        return logging.DEBUG
    if s in ("WARN", "WARNING"):
        return logging.WARNING
    if s == "ERROR":
        return logging.ERROR
    if s == "PROFILE":
        return PROFILE
    return logging.INFO
