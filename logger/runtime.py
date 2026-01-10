# msui/logger/runtime.py
from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Dict, Iterator, Mapping, Tuple

from .config import PROFILE, level_from_str
from .policies import POLICIES


# ---------------------------
# Ambient Context
# ---------------------------

# IMPORTANT: never mutate the dict in-place; always copy/replace.
_LOG_CTX: ContextVar[Dict[str, Any]] = ContextVar("MSUI_LOG_CTX", default={})


@contextmanager
def context(**fields: Any) -> Iterator[None]:
    """
    Ambient context for structured logging.

    Merge order for emitted fields:
      1) bound fields (via .bind)
      2) ambient context (ContextVar)
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
# Implementation
# ---------------------------

@dataclass(frozen=True)
class StructLogger:
    """
    Thin emitter around stdlib logging.Logger.
    Bound fields/context are handled by BoundLogger.
    """
    _logger: logging.Logger

    @property
    def name(self) -> str:
        return self._logger.name

    def child(self, name: str) -> "StructLogger":
        name = str(name).strip()
        if not name:
            return self
        return StructLogger(logging.getLogger(f"{self._logger.name}.{name}"))

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

        if not POLICIES.should_emit(level=level, logger_name=self._logger.name, msg=msg, fields=per_call_fields):
            return

        extra: Dict[str, Any] = {}
        if bound_ctx:
            extra["msui_ctx"] = dict(bound_ctx)
        if per_call_fields:
            extra["msui_fields"] = dict(per_call_fields)

        self._logger.log(level, msg, *args, extra=extra if extra else None, exc_info=exc_info)


@dataclass(frozen=True)
class BoundLogger:
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
        return self._base.is_enabled_for(level_from_str(level))

    def is_debug_enabled(self) -> bool:
        return self.is_enabled("DEBUG")

    def context(self, **fields: Any):
        return context(**fields)

    def _merged_ctx(self) -> Dict[str, Any]:
        # Merge inside ctx: bound then ambient (ambient overrides bound).
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
