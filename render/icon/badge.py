# msui/render/icon/badge.py
from __future__ import annotations

from .primitives import pad_rect


def badge_active(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 1)

    pw = max(14, int(w * 0.70))
    ph = max(10, int(h * 0.80))
    px = x + (w - pw) // 2
    py = y + (h - ph) // 2

    canvas.round_rect((px, py, pw, ph), radius=4, color=color, fill=False, width=2)

    canvas.circle((px + int(pw * 0.30), py + int(ph * 0.25)), 2, color, width=0)
    canvas.circle((px + int(pw * 0.70), py + int(ph * 0.25)), 2, color, width=0)

    canvas.circle((px + pw // 2, py + int(ph * 0.70)), 3, color, width=0)


def badge_bypass(canvas, rect, color, theme):
    x, y, w, h = pad_rect(rect, 1)

    pw = max(14, int(w * 0.70))
    ph = max(10, int(h * 0.80))
    px = x + (w - pw) // 2
    py = y + (h - ph) // 2

    canvas.round_rect((px, py, pw, ph), radius=4, color=color, fill=False, width=2)

    canvas.circle((px + int(pw * 0.30), py + int(ph * 0.25)), 2, color, width=0)
    canvas.circle((px + int(pw * 0.70), py + int(ph * 0.25)), 2, color, width=0)

    fsx = px + pw // 2
    fsy = py + int(ph * 0.70)
    canvas.circle((fsx, fsy), 3, color, width=2)
