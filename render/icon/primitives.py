# msui/render/icon/primitives.py
from __future__ import annotations

from typing import List

from .types import Point, Rect


def pad_rect(rect: Rect, pad: int) -> Rect:
    x, y, w, h = rect
    return (x + pad, y + pad, max(1, w - 2 * pad), max(1, h - 2 * pad))


def polyline(canvas, pts: List[Point], color, width: int = 2) -> None:
    for i in range(len(pts) - 1):
        canvas.line(pts[i], pts[i + 1], color, width=width)


def _bezier3(p0: Point, p1: Point, p2: Point, p3: Point, t: float) -> Point:
    u = 1.0 - t
    x = (u * u * u) * p0[0] + 3 * (u * u) * t * p1[0] + 3 * u * (t * t) * p2[0] + (t * t * t) * p3[0]
    y = (u * u * u) * p0[1] + 3 * (u * u) * t * p1[1] + 3 * u * (t * t) * p2[1] + (t * t * t) * p3[1]
    return (int(x), int(y))


def draw_cubic(
    canvas,
    p0: Point,
    p1: Point,
    p2: Point,
    p3: Point,
    color,
    width: int = 3,
    steps: int = 24,
) -> None:
    steps = max(2, int(steps))
    pts = [_bezier3(p0, p1, p2, p3, i / (steps - 1)) for i in range(steps)]
    polyline(canvas, pts, color, width=width)


def arrow(canvas, x1: int, y1: int, x2: int, y2: int, color, w: int = 2) -> None:
    canvas.line((x1, y1), (x2, y2), color, width=w)

    dx = x2 - x1
    dy = y2 - y1
    if abs(dx) + abs(dy) == 0:
        return

    hs = 4
    px, py = -dy, dx

    # clamp for tiny icons
    px = 1 if px > 0 else (-1 if px < 0 else 0)
    py = 1 if py > 0 else (-1 if py < 0 else 0)

    canvas.line((x2, y2), (x2 - 2 - px * hs // 2, y2 - py * hs // 2), color, width=w)
    canvas.line((x2, y2), (x2 - 2 + px * hs // 2, y2 + py * hs // 2), color, width=w)
