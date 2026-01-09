# backends/canvas.py
from __future__ import annotations

from typing import Protocol, Tuple, TypeAlias, runtime_checkable

# Common geometry / color types used across backends
Point: TypeAlias = Tuple[int, int]
Rect: TypeAlias = Tuple[int, int, int, int]
Color: TypeAlias = Tuple[int, int, int]  # RGB-ish tuple (your Theme already provides tuples)


@runtime_checkable
class Canvas(Protocol):
    """
    Stable drawing interface used by render/ and controls/.

    Any backend (pygame, PIL, framebuffer, etc.) implements this API.
    """

    w: int
    h: int

    def fill(self, color: Color) -> None: ...
    def round_rect(
        self,
        rect: Rect,
        radius: int,
        color: Color,
        *,
        fill: bool = True,
        width: int = 1,
    ) -> None: ...

    def circle(self, center: Point, r: int, color: Color, *, width: int = 1) -> None: ...
    def arc(
        self,
        rect: Rect,
        start_rad: float,
        end_rad: float,
        color: Color,
        *,
        width: int = 1,
    ) -> None: ...

    def line(self, p1: Point, p2: Point, color: Color, *, width: int = 1) -> None: ...

    def text(self, font_key: str, x: int, y: int, s: str, color: Color) -> None: ...
    def text_size(self, font_key: str, s: str) -> Tuple[int, int]: ...
