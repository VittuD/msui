# msui/render/icon/filter.py
from __future__ import annotations

from .mirror import mirror
from .primitives import pad_rect, draw_cubic


def filter_lp6(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    mid = y + h // 2
    bot = y + h - 4

    p0 = (x, mid)
    p3 = (x + w - 1, bot)
    p1 = (x + int(w * 0.55), mid)
    p2 = (x + int(w * 0.75), mid + int((bot - mid) * 0.55))
    draw_cubic(canvas, p0, p1, p2, p3, color, width=3)


def filter_bp6(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    zero = y + h // 2
    bot = y + h - 4

    left_pass = x + int(w * 0.42)
    right_pass = x + int(w * 0.58)

    draw_cubic(
        canvas,
        (x, bot),
        (x + int(w * 0.18), bot),
        (x + int(w * 0.30), zero),
        (left_pass, zero),
        color,
        width=3,
        steps=18,
    )

    canvas.line((left_pass, zero), (right_pass, zero), color, width=3)

    draw_cubic(
        canvas,
        (right_pass, zero),
        (x + int(w * 0.70), zero),
        (x + int(w * 0.82), bot),
        (x + w - 1, bot),
        color,
        width=3,
        steps=18,
    )


_filter_hp6 = mirror(filter_lp6, flip="vertical")
_filter_notch6 = mirror(filter_bp6, flip="horizontal", h_mode="below_zero", below_shift=0.65)


def filter_hp6(canvas, rect, color, theme):
    _filter_hp6(canvas, rect, color, theme)


def filter_notch6(canvas, rect, color, theme):
    _filter_notch6(canvas, rect, color, theme)


def filter_ladder(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    zero = y + h // 2
    bot = y + h - 4
    top = y + 3

    knee_x = x + int(w * 0.55)
    canvas.line((x, zero), (knee_x - 6, zero), color, width=3)

    bump_top = zero - max(2, int((zero - top) * 0.33))

    draw_cubic(
        canvas,
        (knee_x - 6, zero),
        (knee_x - 2, zero),
        (knee_x + 2, bump_top),
        (knee_x + 8, zero),
        color,
        width=3,
        steps=10,
    )

    p0 = (knee_x + 8, zero)
    p3 = (x + w - 1, bot)
    p1 = (x + int(w * 0.75), zero)
    p2 = (x + int(w * 0.85), zero + int((bot - zero) * 0.55))
    draw_cubic(canvas, p0, p1, p2, p3, color, width=3)


def filter_pultec(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 6)
    zero = y + h // 2
    top = y + 3
    bot = y + h - 4

    low_bump = zero - max(2, int((zero - top) * 0.55))
    mid_dip = zero + max(2, int((bot - zero) * 0.55))
    high_shelf = zero - max(2, int((zero - top) * 0.40))

    p0 = (x, zero)
    p3 = (x + w - 1, high_shelf)

    p1 = (x + int(w * 0.50), low_bump)
    p2 = (x + int(w * 0.55), mid_dip)

    draw_cubic(canvas, p0, p1, p2, p3, color, width=3, steps=28)
