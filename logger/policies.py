# msui/logger/policies.py
from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple


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
class RateLimitRule:
    logger_prefix: str
    msg: str
    level: int
    interval_s: float
    key_fields: Tuple[str, ...] = ("type",)


class PolicyEngine:
    """
    Central filtering/sampling/rate-limits.

    Defaults are conservative and only target known high-frequency DEBUG chatter.
    """

    def __init__(self) -> None:
        # Master switch: enable/disable noise control
        self.enabled: bool = _env_flag("MSUI_LOG_NOISE", True)

        # Sampling config:
        #   MSUI_LOG_SAMPLING='{"msui.backends.input_pygame:event": 10}'
        self.sampling: Dict[str, int] = {k: int(v) for k, v in _parse_json_env("MSUI_LOG_SAMPLING").items()}

        # Default rate-limits (DEBUG only)
        self.rate_limits: Tuple[RateLimitRule, ...] = (
            RateLimitRule(
                logger_prefix="msui.backends.input_pygame",
                msg="event",
                level=logging.DEBUG,
                interval_s=0.25,
                key_fields=("type", "delta"),
            ),
        )

        self._last_emit: Dict[Tuple[Any, ...], float] = {}
        self._counters: Dict[Tuple[Any, ...], int] = {}

    def _match_sampling_n(self, logger_name: str, msg: str) -> int:
        # Most-specific match wins by iteration order; keep it simple.
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

        # Sampling (keep 1/N)
        n = self._match_sampling_n(logger_name, msg)
        if n > 1:
            skey = (logger_name, msg, fields.get("type"), fields.get("delta"))
            c = self._counters.get(skey, 0) + 1
            self._counters[skey] = c
            if (c % n) != 0:
                return False

        return True


POLICIES = PolicyEngine()
