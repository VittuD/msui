from msui.core.model import Effect
from msui.render.theme import Theme


def render_effect_editor(canvas, effect: Effect, theme: Theme):
    canvas.fill(theme.BG)

    # Header bar
    hx, hy = theme.HEADER_X, theme.HEADER_Y
    hw, hh = theme.W - 2 * theme.HEADER_X, theme.HEADER_H
    canvas.round_rect((hx, hy, hw, hh), theme.HEADER_RADIUS, theme.HDR, fill=True)

    canvas.text(theme.FONT_L, hx + 10, hy + 6, effect.name, theme.FG)

    # Badge on right (monochrome signal-path icon + text)
    badge_text = "ACTIVE" if effect.enabled else "BYPASS"

    tw, _ = canvas.text_size(theme.FONT_S, badge_text)

    icon_h = theme.BADGE_H - 8
    icon_w = icon_h + 10  # slightly wider than tall
    gap = 8

    bw = tw + theme.BADGE_PAD_X * 2 + icon_w + gap
    bx = hx + hw - bw - 6
    by = hy + (hh - theme.BADGE_H) // 2

    # pill background (no color accents)
    canvas.round_rect((bx, by, bw, theme.BADGE_H), theme.BADGE_RADIUS, theme.HDR, fill=True)
    canvas.round_rect((bx, by, bw, theme.BADGE_H), theme.BADGE_RADIUS, theme.DIM, fill=False, width=1)

    col = theme.FG if effect.enabled else theme.DIM

    # --- icon area ---
    ix = bx + theme.BADGE_PAD_X
    iy = by + (theme.BADGE_H - icon_h) // 2

    # endpoints
    left_dot  = (ix + 5, iy + icon_h // 2)
    right_dot = (ix + icon_w - 5, iy + icon_h // 2)
    canvas.circle(left_dot, 2, col, width=0)
    canvas.circle(right_dot, 2, col, width=0)

    # FX block in the middle
    fx_w = max(16, icon_w - 22)
    fx_h = max(10, icon_h - 10)
    fx_x = ix + (icon_w - fx_w) // 2
    fx_y = iy + (icon_h - fx_h) // 2
    canvas.round_rect((fx_x, fx_y, fx_w, fx_h), radius=6, color=col, fill=False, width=2)

    # path
    mid_y = iy + icon_h // 2
    if effect.enabled:
        # straight through the FX block
        canvas.line((left_dot[0] + 3, mid_y), (fx_x, mid_y), col, width=2)
        canvas.line((fx_x + fx_w, mid_y), (right_dot[0] - 3, mid_y), col, width=2)
        # little "through" tick inside block
        canvas.line((fx_x + 4, mid_y), (fx_x + fx_w - 4, mid_y), col, width=2)
    else:
        # bypass route around the block (up and over)
        top_y = iy + 3
        canvas.line((left_dot[0] + 3, mid_y), (fx_x - 2, mid_y), col, width=2)
        canvas.line((fx_x - 2, mid_y), (fx_x - 2, top_y), col, width=2)
        canvas.line((fx_x - 2, top_y), (fx_x + fx_w + 2, top_y), col, width=2)
        canvas.line((fx_x + fx_w + 2, top_y), (fx_x + fx_w + 2, mid_y), col, width=2)
        canvas.line((fx_x + fx_w + 2, mid_y), (right_dot[0] - 3, mid_y), col, width=2)

    # text
    tx = ix + icon_w + gap
    canvas.text(theme.FONT_S, tx, by + 6, badge_text, col)


    # Page box under header (left-aligned)
    page_text = f"PAGE {effect.page_index+1}/{len(effect.pages)}"
    p_tw, _ = canvas.text_size(theme.FONT_S, page_text)
    p_w = p_tw + theme.PAGEBOX_PAD_X * 2

    px = theme.HEADER_X
    py = theme.PAGEBOX_Y
    canvas.round_rect((px, py, p_w, theme.PAGEBOX_H), theme.PAGEBOX_RADIUS, theme.HDR, fill=True)
    canvas.text(theme.FONT_S, px + theme.PAGEBOX_PAD_X, py + theme.PAGEBOX_PAD_Y, page_text, theme.DIM)

    # Tiles row (3 tiles)
    page = effect.current_page()

    total_w = theme.TILE_W * 3 + theme.TILE_GAP * 2
    start_x = (theme.W - total_w) // 2
    y = theme.TILES_Y

    for i in range(3):
        x = start_x + i * (theme.TILE_W + theme.TILE_GAP)
        rect = (x, y, theme.TILE_W, theme.TILE_H)
        focused = (i == effect.control_index)
        page.controls[i].render(canvas, rect, focused, effect, theme)
