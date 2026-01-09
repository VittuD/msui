import math


def polar(cx, cy, r, deg):
    rad = math.radians(deg)
    return (cx + int(r * math.cos(rad)),
            cy - int(r * math.sin(rad)))  # pygame y-down


def draw_dial_visual(canvas, visual_rect, value_0_100: int, ring_col, accent_col, theme):
    """
    Draws the 270° symmetric dial + fill inside visual_rect.
    visual_rect = (x, y, w, h)
    """
    x, y, w, h = visual_rect

    # dial radius based on available space
    r = min(w, h) // 2 - 2
    cx = x + w // 2
    cy = y + h // 2 + 2  # tiny downward bias tends to look nicer

    # outer circle
    canvas.circle((cx, cy), r, ring_col, width=2)

    start_deg = theme.DIAL_START_DEG                 # 225
    sweep = theme.DIAL_SWEEP_DEG                     # 270
    end_deg = start_deg - sweep                      # -45 (315)
    # pygame arc expects radians CCW from start->stop; we want the big arc from end->start
    canvas.arc((cx - r, cy - r, 2 * r, 2 * r),
               math.radians(end_deg),
               math.radians(start_deg),
               ring_col, width=2)

    # value to angle (clockwise across top)
    v = max(0, min(100, int(value_0_100)))
    ang = start_deg - sweep * (v / 100.0)

    # filled ticks from start -> ang
    a = start_deg
    step = theme.DIAL_STEP_DEG
    while a >= ang:
        p1 = polar(cx, cy, r - 2, a)
        p2 = polar(cx, cy, r - 10, a)
        canvas.line(p1, p2, accent_col, width=3)
        a -= step

    # indicator
    pend = polar(cx, cy, r - 8, ang)
    canvas.line((cx, cy), pend, accent_col, width=3)
