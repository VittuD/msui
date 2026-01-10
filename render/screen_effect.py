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

from msui.log import get_logger

log = get_logger(__name__)

ICON_ACTIVE = Icon(ico.badge_active)
ICON_BYPASS = Icon(ico.badge_bypass)

# Known bits we actually interpret here (DIRTY_ALL is a convenience constant).
_KNOWN_DIRTY_BITS = (
    DIRTY_NONE
    | DIRTY_HEADER
    | DIRTY_PAGE
    | DIRTY_TILES
    | DIRTY_TILE0
    | DIRTY_TILE1
    | DIRTY_TILE2
)


def _fill_rect(canvas, rect, color):
    x, y, w, h = rect
    canvas.round_rect((x, y, w, h), radius=0, color=color, fill=True)


def draw_page_slots(canvas, x, y, n_pages: int, page_index: int, theme):
    n = max(1, int(n_pages))
    idx = max(0, min(n - 1, int(page_index)))

    pad_x = theme.PAGE_SLOTS_PAD_X
    pad_y = theme.PAGE_SLOTS_PAD_Y
    gap = theme.PAGE_SLOTS_GAP

    pill_h = theme.PAGEBOX_H
    inner_h = pill_h - 2 * pad_y

    box_h = max(10, min(theme.PAGE_SLOTS_MAX_BOX, inner_h))
    box_w = box_h

    max_pill_w = theme.W - 2 * theme.HEADER_X
    needed_w = pad_x * 2 + n * box_w + (n - 1) * gap

    if needed_w > max_pill_w:
        box_w = max(theme.PAGE_SLOTS_MIN_BOX, (max_pill_w - pad_x * 2 - (n - 1) * gap) // n)
        box_h = min(box_h, box_w)

    pill_w = pad_x * 2 + n * box_w + (n - 1) * gap

    canvas.round_rect((x, y, pill_w, pill_h), theme.PAGEBOX_RADIUS, theme.HDR, fill=True)

    sx = x + pad_x
    sy = y + (pill_h - box_h) // 2

    for i in range(n):
        r = (sx + i * (box_w + gap), sy, box_w, box_h)

        if i == idx:
            canvas.round_rect(r, radius=theme.PAGE_SLOTS_ACTIVE_RADIUS, color=theme.FG, fill=True)
            canvas.round_rect(
                r,
                radius=theme.PAGE_SLOTS_ACTIVE_RADIUS,
                color=theme.FG,
                fill=False,
                width=theme.PAGE_SLOTS_ACTIVE_OUTLINE_W,
            )
        else:
            canvas.round_rect(
                r,
                radius=theme.PAGE_SLOTS_ACTIVE_RADIUS,
                color=theme.DIM,
                fill=False,
                width=theme.PAGE_SLOTS_INACTIVE_OUTLINE_W,
            )

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
    x, y, w, h = rect
    canvas.round_rect((x, y, w, h), theme.TILE_RADIUS, theme.DIM, fill=False, width=1)
    s = "---"
    tw, th = canvas.text_size(theme.FONT_M, s)
    canvas.text(theme.FONT_M, x + (w - tw) // 2, y + (h - th) // 2, s, theme.DIM)


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
    if dirty_mask == DIRTY_NONE:
        return

    # Debug-only: helpful and not a duplicate of input/control logs.
    unknown = int(dirty_mask) & ~_KNOWN_DIRTY_BITS
    if unknown:
        log.warn("unknown_dirty_bits", dirty_mask=int(dirty_mask), unknown=int(unknown))

    redraw_header = bool(dirty_mask & DIRTY_HEADER) or dirty_mask == DIRTY_ALL
    redraw_page = bool(dirty_mask & DIRTY_PAGE) or dirty_mask == DIRTY_ALL
    redraw_tiles = (
        bool(dirty_mask & DIRTY_TILES)
        or bool(dirty_mask & (DIRTY_TILE0 | DIRTY_TILE1 | DIRTY_TILE2))
        or dirty_mask == DIRTY_ALL
    )

    # Avoid naming collisions: "page" should be page index/context, not a boolean.
    log.debug(
        "render_effect_editor",
        dirty_mask=int(dirty_mask),
        redraw_header=redraw_header,
        redraw_page=redraw_page,
        redraw_tiles=redraw_tiles,
    )

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
