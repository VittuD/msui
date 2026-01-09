def to_rgb565_approx(rgb):
    r, g, b = rgb
    r5 = (r * 31) // 255
    g6 = (g * 63) // 255
    b5 = (b * 31) // 255
    return ((r5 * 255) // 31, (g6 * 255) // 63, (b5 * 255) // 31)


class Theme:
    # Screen
    W = 240
    H = 280
    SCALE = 3
    FPS = 30

    # Input timing (relative to FPS)
    INPUT_FIRST_DELAY_S = 0.25          # seconds before repeating starts
    INPUT_REPEAT_UPDOWN_RATIO = 1.0     # repeats per second = FPS * ratio
    INPUT_REPEAT_NAV_RATIO = 0.6
    INPUT_REPEAT_PAGE_RATIO = 0.4
    
    # Fonts (keys; actual pygame fonts live in Canvas)
    FONT_S = "S"
    FONT_M = "M"
    FONT_L = "L"

    # Colors
    BG = to_rgb565_approx((10, 10, 12))
    FG = to_rgb565_approx((240, 240, 245))
    DIM = to_rgb565_approx((130, 130, 140))
    HDR = to_rgb565_approx((25, 25, 30))
    BAD = to_rgb565_approx((255, 90, 90))

    ACC_FOCUS = to_rgb565_approx((80, 200, 255))
    ACC_IDLE = to_rgb565_approx((200, 200, 210))

    # Header layout
    HEADER_X = 12
    HEADER_Y = 12
    HEADER_H = 40
    HEADER_RADIUS = 12

    # Badge
    BADGE_PAD_X = 11
    BADGE_H = 26
    BADGE_RADIUS = 13

    # Page box
    PAGEBOX_Y = 58
    PAGEBOX_H = 24
    PAGEBOX_RADIUS = 12
    PAGEBOX_PAD_X = 14
    PAGEBOX_PAD_Y = 6

    # Tiles
    TILES_Y = 125
    TILE_W = 70
    TILE_H = 110
    TILE_GAP = 5
    TILE_RADIUS = 14

    TILE_PAD = 6
    TILE_LABEL_H = 18
    TILE_VALUE_H = 22

    # Dial geometry (270° symmetric, gap at bottom)
    DIAL_START_DEG = 225.0
    DIAL_SWEEP_DEG = 270.0
    DIAL_STEP_DEG = 3.0
