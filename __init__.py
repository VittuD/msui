# msui/__init__.py
"""
Package API.

Expose a stable module-level root logger:
  from msui import log
  log.info("...")

Legacy imports still work:
  from msui.log import get_logger, LogMixin, ...
"""

from __future__ import annotations

from .logger import log

__all__ = ["log"]
