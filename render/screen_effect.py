from msui.core.model import Effect
from msui.render.theme import Theme
from msui.render.icon import Icon
from msui.render import icons as ico

ICON_ACTIVE = Icon(ico.badge_active)
ICON_BYPASS = Icon(ico.badge_bypass)


def render_effect_editor(canvas, effect: Effect, theme: Theme):
    canvas.fill(theme.BG)

    # Header bar
    hx, hy = theme.HEADER_X, theme.HEADER_Y
    hw, hh = theme.W - 2 * theme.HEADER_X, theme.HEADER_H
    canvas.round_rect((hx, hy, hw, hh), theme.HEADER_RADIUS, theme.HDR, fill=True)
    canvas.text(theme.FONT_L, hx + 10, hy + 6, effect.name, theme.FG)

    # Badge (Icon + text, monochrome)
    badge_text = "ACTIVE" if effect.enabled else "BYPASS"
    badge_icon = ICON_ACTIVE if effect.enabled else ICON_BYPASS

    tw, _ = canvas.text_size(theme.FONT_S, badge_text)
    icon_h = theme.BADGE_H - 8
    icon_w = icon_h + 6
    gap = 8

    bw = tw + theme.BADGE_PAD_X * 2 + icon_w + gap
    bx = hx + hw - bw - 6
    by = hy + (hh - theme.BADGE_H) // 2

    # pill background
    canvas.round_rect((bx, by, bw, theme.BADGE_H), theme.BADGE_RADIUS, theme.HDR, fill=True)

    # pill outline: WHITE if active, GREY if bypass
    outline = theme.FG if effect.enabled else theme.DIM
    canvas.round_rect((bx, by, bw, theme.BADGE_H), theme.BADGE_RADIUS, outline, fill=False, width=2)

    col = theme.FG if effect.enabled else theme.DIM

    ix = bx + theme.BADGE_PAD_X
    iy = by + (theme.BADGE_H - icon_h) // 2
    badge_icon.draw(canvas, (ix, iy, icon_w, icon_h), col, theme)

    tx = ix + icon_w + gap
    canvas.text(theme.FONT_S, tx, by + 6, badge_text, col)

    # Page box
    page_text = f"PAGE {effect.page_index+1}/{len(effect.pages)}"
    p_tw, _ = canvas.text_size(theme.FONT_S, page_text)
    p_w = p_tw + theme.PAGEBOX_PAD_X * 2

    px = theme.HEADER_X
    py = theme.PAGEBOX_Y
    canvas.round_rect((px, py, p_w, theme.PAGEBOX_H), theme.PAGEBOX_RADIUS, theme.HDR, fill=True)
    canvas.text(theme.FONT_S, px + theme.PAGEBOX_PAD_X, py + theme.PAGEBOX_PAD_Y, page_text, theme.DIM)

    # Tiles row
    page = effect.current_page()

    total_w = theme.TILE_W * 3 + theme.TILE_GAP * 2
    start_x = (theme.W - total_w) // 2
    y0 = theme.TILES_Y

    for i in range(3):
        x0 = start_x + i * (theme.TILE_W + theme.TILE_GAP)
        rect = (x0, y0, theme.TILE_W, theme.TILE_H)
        focused = (i == effect.control_index)
        page.controls[i].render(canvas, rect, focused, effect, theme)
