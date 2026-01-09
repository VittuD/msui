from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from msui.core.dirty import DIRTY_ALL, DIRTY_NONE


@dataclass
class Page:
    title: str
    controls: list  # expected length 3


@dataclass
class Effect:
    name: str
    pages: List[Page]
    params: Dict[str, Any]

    enabled: bool = True
    page_index: int = 0
    control_index: int = 0  # 0..2

    # UI-only state (selection inside compound controls, etc.)
    ui: Dict[str, Any] = field(default_factory=dict)

    # Dirty mask for incremental rendering
    dirty: int = DIRTY_ALL

    def current_page(self) -> Page:
        return self.pages[self.page_index]

    def current_control(self):
        return self.current_page().controls[self.control_index]

    def mark_dirty(self, mask: int) -> None:
        self.dirty |= int(mask)

    def clear_dirty(self) -> None:
        self.dirty = DIRTY_NONE
