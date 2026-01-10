# msui/render/draw.py
from __future__ import annotations

import math


def polar(cx, cy, r, deg):
    rad = math.radians(deg)
    return (cx + int(r * math.cos(rad)),
            cy - int(r * math.sin(rad)))  # pygame y-down


def draw_dial_visual(canvas, visual_rect, value: int, vmin: int, vmax: int, ring_col, accent_col, theme):
    """
    Draws the 270° symmetric dial + fill inside visual_rect.
    Supports arbitrary ranges and shows a 0 marker when range crosses 0.
    """
    x, y, w, h = visual_rect

    r = min(w, h) // 2 - theme.DIAL_RADIUS_PAD
    cx = x + w // 2
    cy = y + h // 2 + theme.DIAL_CENTER_Y_OFFSET

    start_deg = theme.DIAL_START_DEG
    sweep = theme.DIAL_SWEEP_DEG
    end_deg = start_deg - sweep

    # outer circle + arc
    canvas.circle((cx, cy), r, ring_col, width=theme.DIAL_OUTER_CIRCLE_W)
    canvas.arc(
        (cx - r, cy - r, 2 * r, 2 * r),
        math.radians(end_deg),
        math.radians(start_deg),
        ring_col,
        width=theme.DIAL_ARC_W,
    )

    # normalize value into [0..1]
    if vmax == vmin:
        t = 0.0
    else:
        t = (int(value) - int(vmin)) / float(int(vmax) - int(vmin))
    t = max(0.0, min(1.0, t))

    ang = start_deg - sweep * t

    # fill ticks from start -> ang
    a = start_deg
    step = theme.DIAL_STEP_DEG
    while a >= ang:
        p1 = polar(cx, cy, r - theme.DIAL_TICK_INSET, a)
        p2 = polar(cx, cy, r - theme.DIAL_TICK_INSET - theme.DIAL_TICK_LEN, a)
        canvas.line(p1, p2, accent_col, width=theme.DIAL_TICK_W)
        a -= step

    # indicator needle
    pend = polar(cx, cy, r - theme.DIAL_NEEDLE_INSET, ang)
    canvas.line((cx, cy), pend, accent_col, width=theme.DIAL_NEEDLE_W)

    # 0 marker (only if range crosses 0)
    if int(vmin) < 0 < int(vmax):
        t0 = (0 - int(vmin)) / float(int(vmax) - int(vmin))
        t0 = max(0.0, min(1.0, t0))
        a0 = start_deg - sweep * t0

        p1 = polar(cx, cy, r - 1, a0)
        p2 = polar(cx, cy, r - 1 - theme.DIAL_ZERO_TICK_LEN, a0)
        canvas.line(p1, p2, ring_col, width=theme.DIAL_ZERO_TICK_W)
