# msui/__init__.py
"""
Package API.

This exposes a stable module-level root logger:
  from msui import log
  log.info("...")

(Importing msui.log (the module) still works via `import msui.log` or
`from msui.log import get_logger`, etc.)
"""

from __future__ import annotations

from .log import log

__all__ = ["log"]
