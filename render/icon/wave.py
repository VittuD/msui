# msui/render/icon/wave.py
from __future__ import annotations

import math

from .primitives import pad_rect, polyline


def wave_sine(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)
    n = max(16, w)

    pts = []
    for i in range(n):
        t = i / (n - 1)
        xx = x + int(t * (w - 1))
        yy = mid - int(math.sin(2 * math.pi * t) * amp)
        pts.append((xx, yy))
    polyline(canvas, pts, color, width=3)


def wave_triangle(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    p0 = (x, mid)
    p1 = (x + w // 4, mid - amp)
    p2 = (x + 3 * w // 4, mid + amp)
    p3 = (x + w - 1, mid)
    polyline(canvas, [p0, p1, p2, p3], color, width=3)


def wave_saw(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    left = x
    right = x + w - 1
    top = mid - amp
    bot = mid + amp

    canvas.line((left, bot), (right, top), color, width=3)
    canvas.line((right, top), (right, bot), color, width=3)


def wave_square(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    left = x
    right = x + w - 1
    top = mid - amp
    bot = mid + amp
    q1 = x + w // 3
    q2 = x + 2 * w // 3

    canvas.line((left, bot), (q1, bot), color, width=3)
    canvas.line((q1, bot), (q1, top), color, width=3)
    canvas.line((q1, top), (q2, top), color, width=3)
    canvas.line((q2, top), (q2, bot), color, width=3)
    canvas.line((q2, bot), (right, bot), color, width=3)
