# msui/log.py
from __future__ import annotations

import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Mapping, Optional, Protocol, Tuple, runtime_checkable


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
# Ambient Context
# ---------------------------

# ContextVar holding ambient fields to attach to all log lines in the current context.
# IMPORTANT: never mutate the dict in-place; always copy/replace.
_LOG_CTX: ContextVar[Dict[str, Any]] = ContextVar("MSUI_LOG_CTX", default={})


@contextmanager
def context(**fields: Any) -> Iterator[None]:
    """
    Ambient context for structured logging.

    Merge order for emitted fields:
      1) bound fields (via .bind)
      2) ambient context (this ContextVar)
      3) per-call fields (log.info(..., **fields))

    Per-call wins over ambient, ambient wins over bound.
    """
    cur = _LOG_CTX.get()
    if not cur:
        merged = dict(fields)
    else:
        merged = dict(cur)
        merged.update(fields)

    token = _LOG_CTX.set(merged)
    try:
        yield
    finally:
        _LOG_CTX.reset(token)


# ---------------------------
# Protocol (stable interface)
# ---------------------------

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

    # common legacy alias in this repo
    def warn(self, msg: str, *args: Any, **fields: Any) -> None: ...

    def exception(self, msg: str, *args: Any, **fields: Any) -> None: ...

    def bind(self, **fields: Any) -> "Logger": ...
    def child(self, name: str) -> "Logger": ...

    def is_enabled(self, level: str) -> bool: ...
    def is_debug_enabled(self) -> bool: ...

    def context(self, **fields: Any) -> Any: ...


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
# Central noise control
# ---------------------------

def _env_flag(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip().lower()
    return v in ("1", "true", "yes", "on", "y")


def _parse_json_env(name: str) -> dict:
    raw = os.getenv(name, "").strip()
    if not raw:
        return {}
    try:
        obj = json.loads(raw)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


@dataclass(frozen=True)
class _RateLimitRule:
    logger_prefix: str
    msg: str
    level: int
    interval_s: float
    key_fields: Tuple[str, ...] = ("type",)


@dataclass
class _PolicyEngine:
    """
    Central filtering/sampling/rate-limits. Defaults are conservative and only
    target known high-frequency debug chatter (especially pygame input events).
    """
    enabled: bool
    sampling: Dict[str, int]  # key like "msui.backends.input_pygame:event" -> N (keep 1/N)
    rate_limits: Tuple[_RateLimitRule, ...]

    _last_emit: Dict[Tuple[Any, ...], float]
    _counters: Dict[Tuple[Any, ...], int]

    def __init__(self) -> None:
        self.enabled = _env_flag("MSUI_LOG_NOISE", True)

        # Example:
        #   MSUI_LOG_SAMPLING='{"msui.backends.input_pygame:event": 10}'
        self.sampling = {k: int(v) for k, v in _parse_json_env("MSUI_LOG_SAMPLING").items()}

        # Default rate-limits (only DEBUG)
        self.rate_limits = (
            _RateLimitRule(
                logger_prefix="msui.backends.input_pygame",
                msg="event",
                level=logging.DEBUG,
                interval_s=0.25,
                key_fields=("type", "delta"),
            ),
        )

        self._last_emit = {}
        self._counters = {}

    def _match_sampling_n(self, logger_name: str, msg: str) -> int:
        # Most-specific match wins by insertion order; keep it simple.
        for k, n in self.sampling.items():
            if ":" not in k:
                continue
            lp, m = k.split(":", 1)
            if logger_name.startswith(lp) and msg == m:
                return max(1, int(n))
        return 1

    def should_emit(self, *, level: int, logger_name: str, msg: str, fields: Mapping[str, Any]) -> bool:
        # Never interfere with warnings/errors.
        if level >= logging.WARNING:
            return True

        if not self.enabled:
            return True

        now = time.monotonic()

        # Rate limits
        for rule in self.rate_limits:
            if level != rule.level:
                continue
            if not logger_name.startswith(rule.logger_prefix):
                continue
            if msg != rule.msg:
                continue

            key_parts = [rule.logger_prefix, msg]
            for f in rule.key_fields:
                key_parts.append(fields.get(f))
            key = tuple(key_parts)

            last = self._last_emit.get(key)
            if last is not None and (now - last) < rule.interval_s:
                return False
            self._last_emit[key] = now
            break

        # Sampling
        n = self._match_sampling_n(logger_name, msg)
        if n > 1:
            skey = (logger_name, msg, fields.get("type"), fields.get("delta"))
            c = self._counters.get(skey, 0) + 1
            self._counters[skey] = c
            if (c % n) != 0:
                return False

        return True


_POLICIES = _PolicyEngine()


# ---------------------------
# Core logger implementation
# ---------------------------

_CONFIGURED = False


def configure() -> None:
    """
    Idempotent logging setup.

    Env vars:
      - MSUI_LOG_LEVEL: DEBUG|INFO|WARN|WARNING|ERROR|PROFILE
      - MSUI_LOG_FORMAT: json|pretty  (default: pretty if TTY else json)
      - MSUI_LOG_NOISE: 0|1 (default: 1)  enable/disable noise control
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


def _normalize_logger_name(name: str) -> str:
    name = (name or "msui").strip()
    if name == "msui":
        return "msui"
    if name.startswith("msui."):
        return name
    if name.startswith("msui"):
        # e.g. "msui.render" (already ok)
        return name
    return f"msui.{name}"


def _level_from_str(level: str) -> int:
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


@dataclass(frozen=True)
class StructLogger:
    """
    Thin emitter around stdlib logging.Logger.
    It does NOT hold per-instance bound fields; those live in BoundLogger.
    """
    _logger: logging.Logger

    @property
    def name(self) -> str:
        return self._logger.name

    def child(self, name: str) -> "StructLogger":
        name = str(name).strip()
        if not name:
            return self
        full = f"{self._logger.name}.{name}"
        return StructLogger(logging.getLogger(full))

    def is_enabled_for(self, level: int) -> bool:
        return self._logger.isEnabledFor(level)

    def emit(
        self,
        *,
        level: int,
        msg: str,
        args: Tuple[Any, ...],
        bound_ctx: Mapping[str, Any],
        per_call_fields: Mapping[str, Any],
        exc_info: bool = False,
    ) -> None:
        if not self._logger.isEnabledFor(level):
            return

        if not _POLICIES.should_emit(
            level=level,
            logger_name=self._logger.name,
            msg=msg,
            fields=per_call_fields,
        ):
            return

        extra: Dict[str, Any] = {}

        if bound_ctx:
            extra["msui_ctx"] = dict(bound_ctx)
        if per_call_fields:
            extra["msui_fields"] = dict(per_call_fields)

        self._logger.log(level, msg, *args, extra=extra if extra else None, exc_info=exc_info)


@dataclass(frozen=True)
class BoundLogger(Logger):
    """
    Logger wrapper that merges:
      - bound fields (via bind())
      - ambient context (ContextVar)
      - per-call fields
    """
    _base: StructLogger
    _bound: Dict[str, Any]

    def bind(self, **fields: Any) -> "BoundLogger":
        if not fields:
            return self
        merged = dict(self._bound)
        merged.update(fields)
        return BoundLogger(self._base, merged)

    def child(self, name: str) -> "BoundLogger":
        return BoundLogger(self._base.child(name), dict(self._bound))

    def is_enabled(self, level: str) -> bool:
        return self._base.is_enabled_for(_level_from_str(level))

    def is_debug_enabled(self) -> bool:
        return self.is_enabled("DEBUG")

    def context(self, **fields: Any) -> Any:
        return context(**fields)

    def _merged_ctx(self) -> Dict[str, Any]:
        # Merge order inside ctx: bound then ambient.
        # Per-call fields are separate and win in formatter merge.
        amb = _LOG_CTX.get()
        if not self._bound and not amb:
            return {}
        if not amb:
            return dict(self._bound)
        if not self._bound:
            return dict(amb)
        out = dict(self._bound)
        out.update(amb)
        return out

    def _log(self, level: int, msg: str, *args: Any, exc_info: bool = False, **fields: Any) -> None:
        self._base.emit(
            level=level,
            msg=str(msg),
            args=tuple(args),
            bound_ctx=self._merged_ctx(),
            per_call_fields=fields,
            exc_info=exc_info,
        )

    def debug(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **fields)

    def info(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.INFO, msg, *args, **fields)

    def warning(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.WARNING, msg, *args, **fields)

    def warn(self, msg: str, *args: Any, **fields: Any) -> None:
        # legacy alias used in this repo
        self.warning(msg, *args, **fields)

    def error(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.ERROR, msg, *args, **fields)

    def exception(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(logging.ERROR, msg, *args, exc_info=True, **fields)

    def profile(self, msg: str, *args: Any, **fields: Any) -> None:
        self._log(PROFILE, msg, *args, **fields)


def get_logger(name: str = "msui", **ctx: Any) -> Logger:
    """
    Usage:
      log = get_logger(__name__, cls="DialControl")
      log.info("hello", x=1)
    """
    configure()
    full = _normalize_logger_name(name)
    base = StructLogger(logging.getLogger(full))
    return BoundLogger(base, dict(ctx))


# ---------------------------
# Mixin: auto logger per class
# ---------------------------

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


# ---------------------------
# Public root logger (package API)
# ---------------------------

# Root logger object usable via:
#   from msui import log
#   log.info(...)
log: Logger = get_logger("msui")


# ---------------------------
# Back-compat module-level helpers
# ---------------------------

def debug(*args: Any, **fields: Any) -> None:
    log.debug(" ".join(map(str, args)), **fields)


def info(*args: Any, **fields: Any) -> None:
    log.info(" ".join(map(str, args)), **fields)


def warn(*args: Any, **fields: Any) -> None:
    log.warn(" ".join(map(str, args)), **fields)


def error(*args: Any, **fields: Any) -> None:
    log.error(" ".join(map(str, args)), **fields)


def profile(*args: Any, **fields: Any) -> None:
    log.profile(" ".join(map(str, args)), **fields)
