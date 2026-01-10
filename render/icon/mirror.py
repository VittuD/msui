# msui/render/icon/mirror.py
from __future__ import annotations

import math
from dataclasses import dataclass

from .types import IconFn, Point, Rect


@dataclass
class _MirrorCanvas:
    base: object
    rect: Rect  # (x, y, w, h)
    flip_h: bool         # top<->bottom
    flip_v: bool         # left<->right
    h_mode: str = "literal"      # "literal" | "below_zero"
    below_shift: float = 0.65    # fraction of half-height (only for below_zero)

    def _map_point(self, p: Point) -> Point:
        x0, y0, w, h = self.rect
        x, y = p
        lx = x - x0
        ly = y - y0

        # left<->right
        if self.flip_v:
            lx = (w - 1) - lx

        # top<->bottom
        if self.flip_h:
            if self.h_mode == "literal":
                ly = (h - 1) - ly
            elif self.h_mode == "below_zero":
                # 1) mirror
                ly = (h - 1) - ly
                # 2) shift into bottom half, then clamp
                half = h // 2
                shift = int(half * self.below_shift)
                ly = ly + shift
                if ly < half:
                    ly = half
                if ly > (h - 1):
                    ly = h - 1
            else:
                raise ValueError(f"Unknown h_mode: {self.h_mode}")

        return (x0 + lx, y0 + ly)

    def _map_rect(self, r: Rect) -> Rect:
        x, y, w, h = r
        p1 = self._map_point((x, y))
        p2 = self._map_point((x + w, y + h))
        nx = min(p1[0], p2[0])
        ny = min(p1[1], p2[1])
        nw = abs(p2[0] - p1[0])
        nh = abs(p2[1] - p1[1])
        return (nx, ny, nw, nh)

    def line(self, p1: Point, p2: Point, color, width=1):
        return self.base.line(self._map_point(p1), self._map_point(p2), color, width=width)

    def circle(self, center: Point, r: int, color, width=1):
        return self.base.circle(self._map_point(center), r, color, width=width)

    def round_rect(self, rect: Rect, radius: int, color, fill=True, width=1):
        return self.base.round_rect(self._map_rect(rect), radius, color, fill=fill, width=width)

    def arc(self, rect: Rect, start_rad: float, end_rad: float, color, width=1):
        # best-effort for literal mirror only; prefer polylines in icons
        r2 = self._map_rect(rect)

        def map_ang(a: float) -> float:
            if self.flip_h and self.h_mode == "literal":
                a = -a
            if self.flip_v:
                a = math.pi - a
            return a

        return self.base.arc(r2, map_ang(start_rad), map_ang(end_rad), color, width=width)

    def __getattr__(self, name):
        return getattr(self.base, name)


def mirror(icon_fn: IconFn, flip="horizontal", h_mode="literal", below_shift=0.65) -> IconFn:
    """
    flip:
      - "horizontal": top<->bottom
      - "vertical":   left<->right
      - "both":       both flips
    h_mode (only affects horizontal flip):
      - "literal"
      - "below_zero": mirror then shift into bottom half
    """
    if isinstance(flip, (tuple, list)):
        flip_h = "horizontal" in flip
        flip_v = "vertical" in flip
    else:
        flip_h = flip in ("horizontal", "both")
        flip_v = flip in ("vertical", "both")

    def wrapped(canvas, rect, color, theme):
        mc = _MirrorCanvas(
            canvas,
            rect,
            flip_h=flip_h,
            flip_v=flip_v,
            h_mode=h_mode,
            below_shift=below_shift,
        )
        return icon_fn(mc, rect, color, theme)

    return wrapped
