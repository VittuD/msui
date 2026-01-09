# backends/input.py
from __future__ import annotations

from typing import Protocol, runtime_checkable, List
from msui.core.events import UIEvent


@runtime_checkable
class InputSource(Protocol):
    """
    Stable input interface.

    Backends implement:
      - pump(): read/consume platform events (if needed)
      - get_events(dt_ms): convert current input state into UIEvents
    """

    def pump(self) -> None: ...
    def get_events(self, dt_ms: int) -> List[UIEvent]: ...
