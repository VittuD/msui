from __future__ import annotations

from msui.core.model import Effect
from msui.render.theme import Theme
from msui.render.icon import Icon
from msui.render import icons as ico
from msui.render.layout import header_rect, badge_geometry, page_slots_pos, tile_rects

from msui.core.dirty import (
    DIRTY_NONE,
    DIRTY_ALL,
    DIRTY_HEADER,
    DIRTY_PAGE,
    DIRTY_TILES,
    DIRTY_TILE0,
    DIRTY_TILE1,
    DIRTY_TILE2,
)

ICON_ACTIVE = Icon(ico.badge_active)
ICON_BYPASS = Icon(ico.badge_bypass)


def _fill_rect(canvas, rect, color):
    """
    Backend-agnostic "clear this rect" using round_rect(radius=0).
    """
    x, y, w, h = rect
    canvas.round_rect((x, y, w, h), radius=0, color=color, fill=True)


def draw_page_slots(canvas, x, y, n_pages: int, page_index: int, theme):
    """
    Draws a rounded 'page indicator' pill containing N small boxes.
    The active page is filled; others are outlines.
    Returns the pill rect (x,y,w,h).
    """
    n = max(1, int(n_pages))
    idx = max(0, min(n - 1, int(page_index)))

    pad_x = 10
    pad_y = 5
    gap = 4

    pill_h = theme.PAGEBOX_H
    inner_h = pill_h - 2 * pad_y

    box_h = max(10, min(14, inner_h))
    box_w = box_h

    max_pill_w = theme.W - 2 * theme.HEADER_X
    needed_w = pad_x * 2 + n * box_w + (n - 1) * gap

    if needed_w > max_pill_w:
        box_w = max(6, (max_pill_w - pad_x * 2 - (n - 1) * gap) // n)
        box_h = min(box_h, box_w)

    pill_w = pad_x * 2 + n * box_w + (n - 1) * gap

    canvas.round_rect((x, y, pill_w, pill_h), theme.PAGEBOX_RADIUS, theme.HDR, fill=True)

    sx = x + pad_x
    sy = y + (pill_h - box_h) // 2

    for i in range(n):
        r = (sx + i * (box_w + gap), sy, box_w, box_h)

        if i == idx:
            canvas.round_rect(r, radius=3, color=theme.FG, fill=True)
            canvas.round_rect(r, radius=3, color=theme.FG, fill=False, width=2)
        else:
            canvas.round_rect(r, radius=3, color=theme.DIM, fill=False, width=2)

    return (x, y, pill_w, pill_h)


def _render_header_and_badge(canvas, effect: Effect, theme: Theme) -> None:
    hr = header_rect(theme)
    hx, hy, hw, hh = hr

    canvas.round_rect(hr, theme.HEADER_RADIUS, theme.HDR, fill=True)
    canvas.text(theme.FONT_L, hx + 10, hy + 6, effect.name, theme.FG)

    badge_text = "ACTIVE" if effect.enabled else "BYPASS"
    badge_icon = ICON_ACTIVE if effect.enabled else ICON_BYPASS

    tw, _ = canvas.text_size(theme.FONT_S, badge_text)
    icon_h = theme.BADGE_H - 8
    icon_w = icon_h + 6

    geo = badge_geometry(theme, hr, tw, icon_h=icon_h, icon_w=icon_w)
    br = geo["badge_rect"]
    ir = geo["icon_rect"]
    tx, ty = geo["text_pos"]

    canvas.round_rect(br, theme.BADGE_RADIUS, theme.HDR, fill=True)

    outline = theme.FG if effect.enabled else theme.DIM
    canvas.round_rect(br, theme.BADGE_RADIUS, outline, fill=False, width=2)

    col = theme.FG if effect.enabled else theme.DIM
    badge_icon.draw(canvas, ir, col, theme)
    canvas.text(theme.FONT_S, tx, ty, badge_text, col)


def _render_page_slots(canvas, effect: Effect, theme: Theme) -> None:
    px, py = page_slots_pos(theme)
    clear_r = (theme.HEADER_X, py, theme.W - 2 * theme.HEADER_X, theme.PAGEBOX_H)
    _fill_rect(canvas, clear_r, theme.BG)

    draw_page_slots(canvas, px, py, len(effect.pages), effect.page_index, theme)


def _render_empty_tile(canvas, rect, theme: Theme) -> None:
    """
    Draw a subtle placeholder for missing tiles (pages with < 3 controls).
    Keeps layout stable without implying focus.
    """
    x, y, w, h = rect

    # subtle outline only (very dim)
    canvas.round_rect((x, y, w, h), theme.TILE_RADIUS, theme.DIM, fill=False, width=1)

    # small centered marker
    s = "---"
    tw, th = canvas.text_size(theme.FONT_M, s)
    canvas.text(
        theme.FONT_M,
        x + (w - tw) // 2,
        y + (h - th) // 2,
        s,
        theme.DIM,
    )


def _render_tile(canvas, effect: Effect, theme: Theme, tile_i: int) -> None:
    rects = tile_rects(theme)
    rect = rects[tile_i]

    _fill_rect(canvas, rect, theme.BG)

    page = effect.current_page()
    if tile_i >= len(page.controls):
        _render_empty_tile(canvas, rect, theme)
        return

    focused = (tile_i == effect.control_index)
    page.controls[tile_i].render(canvas, rect, focused, effect, theme)


def _render_tiles(canvas, effect: Effect, theme: Theme, mask: int) -> None:
    if mask & DIRTY_TILES:
        _render_tile(canvas, effect, theme, 0)
        _render_tile(canvas, effect, theme, 1)
        _render_tile(canvas, effect, theme, 2)
        return

    if mask & DIRTY_TILE0:
        _render_tile(canvas, effect, theme, 0)
    if mask & DIRTY_TILE1:
        _render_tile(canvas, effect, theme, 1)
    if mask & DIRTY_TILE2:
        _render_tile(canvas, effect, theme, 2)


def render_effect_editor(canvas, effect: Effect, theme: Theme, dirty_mask: int = DIRTY_ALL) -> None:
    """
    Incremental renderer:
      - DIRTY_ALL: full redraw (clears screen)
      - DIRTY_HEADER: redraw header+badge
      - DIRTY_PAGE: redraw page slots
      - DIRTY_TILES: redraw all tiles (and empty placeholders)
      - DIRTY_TILE0/1/2: redraw individual tiles
    """
    if dirty_mask == DIRTY_NONE:
        return

    if dirty_mask == DIRTY_ALL:
        canvas.fill(theme.BG)
        _render_header_and_badge(canvas, effect, theme)
        _render_page_slots(canvas, effect, theme)
        _render_tiles(canvas, effect, theme, DIRTY_TILES)
        return

    if dirty_mask & DIRTY_HEADER:
        hr = header_rect(theme)
        _fill_rect(canvas, hr, theme.BG)
        _render_header_and_badge(canvas, effect, theme)

    if dirty_mask & DIRTY_PAGE:
        _render_page_slots(canvas, effect, theme)

    _render_tiles(canvas, effect, theme, dirty_mask)
