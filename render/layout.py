# msui/render/layout.py
from __future__ import annotations

from typing import List, Tuple


Rect = Tuple[int, int, int, int]


def header_rect(theme) -> Rect:
    hx, hy = theme.HEADER_X, theme.HEADER_Y
    hw, hh = theme.W - 2 * theme.HEADER_X, theme.HEADER_H
    return (hx, hy, hw, hh)


def badge_geometry(theme, header_r: Rect, text_w: int, *, icon_h: int, icon_w: int) -> dict:
    """
    Pure layout math for the ACTIVE/BYPASS badge.

    Returns rects/positions:
      - badge_rect
      - icon_rect
      - text_pos (x,y)
    """
    hx, hy, hw, hh = header_r

    gap = 8
    bw = text_w + theme.BADGE_PAD_X * 2 + icon_w + gap
    bx = hx + hw - bw - 6
    by = hy + (hh - theme.BADGE_H) // 2

    ix = bx + theme.BADGE_PAD_X
    iy = by + (theme.BADGE_H - icon_h) // 2

    tx = ix + icon_w + gap
    ty = by + 6

    return {
        "badge_rect": (bx, by, bw, theme.BADGE_H),
        "icon_rect": (ix, iy, icon_w, icon_h),
        "text_pos": (tx, ty),
    }


def page_slots_pos(theme) -> Tuple[int, int]:
    """
    Position for the page slots pill.
    """
    return (theme.HEADER_X, theme.PAGEBOX_Y)


def tile_rects(theme) -> List[Rect]:
    """
    Returns the 3 tile rects for the current row.
    """
    total_w = theme.TILE_W * 3 + theme.TILE_GAP * 2
    start_x = (theme.W - total_w) // 2
    y0 = theme.TILES_Y

    rects: List[Rect] = []
    for i in range(3):
        x0 = start_x + i * (theme.TILE_W + theme.TILE_GAP)
        rects.append((x0, y0, theme.TILE_W, theme.TILE_H))
    return rects
