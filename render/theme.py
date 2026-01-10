# msui/render/theme.py
from __future__ import annotations

from dataclasses import dataclass


def to_rgb565_approx(rgb):
    r, g, b = rgb
    r5 = (r * 31) // 255
    g6 = (g * 63) // 255
    b5 = (b * 31) // 255
    return ((r5 * 255) // 31, (g6 * 255) // 63, (b5 * 255) // 31)


@dataclass(frozen=True, slots=True)
class Theme:
    # ----------------
    # Screen
    # ----------------
    W: int = 240
    H: int = 280
    SCALE: int = 3
    FPS: int = 15

    # ----------------
    # Input timing (relative to FPS)
    # ----------------
    INPUT_FIRST_DELAY_S: float = 0.25
    INPUT_REPEAT_UPDOWN_RATIO: float = 1.0
    INPUT_REPEAT_NAV_RATIO: float = 0.6
    INPUT_REPEAT_PAGE_RATIO: float = 0.4

    # ----------------
    # Fonts (keys; actual pygame fonts live in Canvas)
    # ----------------
    FONT_S: str = "S"
    FONT_M: str = "M"
    FONT_L: str = "L"

    # ----------------
    # Colors
    # ----------------
    BG: tuple = to_rgb565_approx((10, 10, 12))
    FG: tuple = to_rgb565_approx((240, 240, 245))
    DIM: tuple = to_rgb565_approx((130, 130, 140))
    HDR: tuple = to_rgb565_approx((25, 25, 30))
    BAD: tuple = to_rgb565_approx((255, 90, 90))

    ACC_FOCUS: tuple = to_rgb565_approx((80, 200, 255))
    ACC_IDLE: tuple = to_rgb565_approx((200, 200, 210))

    # ----------------
    # Header layout
    # ----------------
    HEADER_X: int = 12
    HEADER_Y: int = 12
    HEADER_H: int = 40
    HEADER_RADIUS: int = 12

    # ----------------
    # Badge
    # ----------------
    BADGE_PAD_X: int = 11
    BADGE_H: int = 26
    BADGE_RADIUS: int = 13

    # ----------------
    # Page box (slots)
    # ----------------
    PAGEBOX_Y: int = 58
    PAGEBOX_H: int = 24
    PAGEBOX_RADIUS: int = 12

    PAGE_SLOTS_PAD_X: int = 10
    PAGE_SLOTS_PAD_Y: int = 5
    PAGE_SLOTS_GAP: int = 4
    PAGE_SLOTS_MIN_BOX: int = 6
    PAGE_SLOTS_MAX_BOX: int = 14
    PAGE_SLOTS_ACTIVE_RADIUS: int = 3
    PAGE_SLOTS_ACTIVE_OUTLINE_W: int = 2
    PAGE_SLOTS_INACTIVE_OUTLINE_W: int = 2

    # ----------------
    # Tiles
    # ----------------
    TILES_Y: int = 125
    TILE_W: int = 70
    TILE_H: int = 110
    TILE_GAP: int = 5
    TILE_RADIUS: int = 14

    TILE_PAD: int = 6
    TILE_LABEL_H: int = 18
    TILE_VALUE_H: int = 22

    # ----------------
    # Dial geometry (270° symmetric, gap at bottom)
    # ----------------
    DIAL_START_DEG: float = 225.0
    DIAL_SWEEP_DEG: float = 270.0
    DIAL_STEP_DEG: float = 3.0

    DIAL_OUTER_CIRCLE_W: int = 2
    DIAL_ARC_W: int = 2
    DIAL_TICK_W: int = 3
    DIAL_TICK_LEN: int = 8
    DIAL_TICK_INSET: int = 2
    DIAL_NEEDLE_W: int = 3
    DIAL_NEEDLE_INSET: int = 6
    DIAL_ZERO_TICK_W: int = 2
    DIAL_ZERO_TICK_LEN: int = 12
    DIAL_CENTER_Y_OFFSET: int = 2
    DIAL_RADIUS_PAD: int = 2

    DIAL_MINUS_GAP: int = 2

    # ----------------
    # Button LED styling (ButtonControl)
    # ----------------
    BTN_LED_MIN_R: int = 7
    BTN_LED_DIV: int = 5            # r ~= min(w,h)//BTN_LED_DIV
    BTN_LED_GLOW_PAD: int = 3
    BTN_LED_GLOW_W: int = 2
    BTN_LED_RING_W: int = 2
    BTN_LED_LENS_RIM_W: int = 2
    BTN_LED_SPEC_DIV: int = 4       # spec radius ~= led_r//BTN_LED_SPEC_DIV
    BTN_LED_HALO_PAD: int = 6
    BTN_LED_HALO_W: int = 1

    # ----------------
    # Switch styling (SwitchControl)
    # ----------------
    SW_OUTER_W: int = 3
    SW_INNER_W: int = 2
    SW_SOCKET_RING_W: int = 3
    SW_SOCKET_INNER_W: int = 2
    SW_STEM_W: int = 3
    SW_END_DOT_DIV: int = 3
    SW_KNOB_INNER_RIM_W: int = 2

    # ----------------
    # Enum icon styling (EnumControl)
    # ----------------
    ENUM_MIDLINE_PAD: int = 6
    ENUM_MIDLINE_W: int = 1
    ENUM_FALLBACK_SCALE: float = 0.55
    ENUM_FALLBACK_RADIUS: int = 10
    ENUM_FALLBACK_W: int = 3
