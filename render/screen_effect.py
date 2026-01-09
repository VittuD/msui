from __future__ import annotations

from msui.core.model import Effect
from msui.render.theme import Theme
from msui.render.icon import Icon
from msui.render import icons as ico
from msui.render.layout import header_rect, badge_geometry, page_slots_pos, tile_rects

ICON_ACTIVE = Icon(ico.badge_active)
ICON_BYPASS = Icon(ico.badge_bypass)


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

    # box size: adapt to number of pages so it fits nicely
    # typical: 3..6 pages => 12px boxes; many pages => smaller
    box_h = max(10, min(14, inner_h))
    box_w = box_h  # square slots

    max_pill_w = theme.W - 2 * theme.HEADER_X  # don't exceed screen content area
    needed_w = pad_x * 2 + n * box_w + (n - 1) * gap

    if needed_w > max_pill_w:
        # shrink boxes to fit
        box_w = max(6, (max_pill_w - pad_x * 2 - (n - 1) * gap) // n)
        box_h = min(box_h, box_w)

    pill_w = pad_x * 2 + n * box_w + (n - 1) * gap

    # pill background
    canvas.round_rect((x, y, pill_w, pill_h), theme.PAGEBOX_RADIUS, theme.HDR, fill=True)

    # slots
    sx = x + pad_x
    sy = y + (pill_h - box_h) // 2

    for i in range(n):
        r = (sx + i * (box_w + gap), sy, box_w, box_h)

        if i == idx:
            # active: filled box + crisp outline
            canvas.round_rect(r, radius=3, color=theme.FG, fill=True)
            canvas.round_rect(r, radius=3, color=theme.FG, fill=False, width=2)
        else:
            # inactive: outline only
            canvas.round_rect(r, radius=3, color=theme.DIM, fill=False, width=2)

    return (x, y, pill_w, pill_h)


def render_effect_editor(canvas, effect: Effect, theme: Theme):
    canvas.fill(theme.BG)

    # ----------------
    # Header bar
    # ----------------
    hr = header_rect(theme)
    hx, hy, hw, hh = hr
    canvas.round_rect(hr, theme.HEADER_RADIUS, theme.HDR, fill=True)
    canvas.text(theme.FONT_L, hx + 10, hy + 6, effect.name, theme.FG)

    # ----------------
    # Badge (Icon + text, monochrome)
    # ----------------
    badge_text = "ACTIVE" if effect.enabled else "BYPASS"
    badge_icon = ICON_ACTIVE if effect.enabled else ICON_BYPASS

    tw, _ = canvas.text_size(theme.FONT_S, badge_text)
    icon_h = theme.BADGE_H - 8
    icon_w = icon_h + 6

    geo = badge_geometry(theme, hr, tw, icon_h=icon_h, icon_w=icon_w)
    br = geo["badge_rect"]
    ir = geo["icon_rect"]
    tx, ty = geo["text_pos"]

    # pill background
    canvas.round_rect(br, theme.BADGE_RADIUS, theme.HDR, fill=True)

    # pill outline: WHITE if active, GREY if bypass
    outline = theme.FG if effect.enabled else theme.DIM
    canvas.round_rect(br, theme.BADGE_RADIUS, outline, fill=False, width=2)

    col = theme.FG if effect.enabled else theme.DIM
    badge_icon.draw(canvas, ir, col, theme)
    canvas.text(theme.FONT_S, tx, ty, badge_text, col)

    # ----------------
    # Page slots (MS-70CDR style)
    # ----------------
    px, py = page_slots_pos(theme)
    draw_page_slots(canvas, px, py, len(effect.pages), effect.page_index, theme)

    # ----------------
    # Tiles row
    # ----------------
    page = effect.current_page()
    rects = tile_rects(theme)

    for i, rect in enumerate(rects):
        focused = (i == effect.control_index)
        page.controls[i].render(canvas, rect, focused, effect, theme)
