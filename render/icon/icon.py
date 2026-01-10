# msui/render/icon/icon.py
from __future__ import annotations

from dataclasses import dataclass
from .types import IconFn


@dataclass(frozen=True)
class Icon:
    fn: IconFn

    def draw(self, canvas, rect, color, theme) -> None:
        self.fn(canvas, rect, color, theme)
