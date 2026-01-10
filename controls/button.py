from __future__ import annotations

from dataclasses import dataclass
from msui.controls.base import Control


@dataclass
class ButtonControl(Control):
    """
    Bool param stored in effect.params[self.key] as True/False.
    Visual: LED indicator only (no base), OFF is intentionally very empty.
    """
    true_text: str = "ON"
    false_text: str = "OFF"

    def value_text(self, effect) -> str:
        return self.true_text if bool(effect.params.get(self.key, False)) else self.false_text

    def adjust(self, delta: int, effect):
        if delta == 0:
            return

        cur = bool(effect.params.get(self.key, False))

        if self.clamp:
            effect.params[self.key] = True if delta > 0 else False
        else:
            effect.params[self.key] = not cur

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        _, visual_rect, _ = self.split_tile(rect, theme)

        x, y, w, h = visual_rect
        is_on = bool(effect.params.get(self.key, False))

        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        cx = x + w // 2
        cy = y + h // 2
        led_r = max(theme.BTN_LED_MIN_R, min(w, h) // theme.BTN_LED_DIV)

        if is_on:
            canvas.circle((cx, cy), led_r + theme.BTN_LED_GLOW_PAD, accent, width=theme.BTN_LED_GLOW_W)
            canvas.circle((cx, cy), led_r, accent, width=0)
            canvas.circle((cx, cy), max(2, led_r - 2), theme.BG, width=theme.BTN_LED_LENS_RIM_W)

            spec_r = max(2, led_r // theme.BTN_LED_SPEC_DIV)
            canvas.circle((cx - led_r // 3, cy - led_r // 3), spec_r, theme.FG, width=0)
        else:
            canvas.circle((cx, cy), led_r, ring, width=theme.BTN_LED_RING_W)
            canvas.circle((cx, cy), max(2, led_r - 2), theme.BG, width=0)

        if focused:
            canvas.circle((cx, cy), led_r + theme.BTN_LED_HALO_PAD, accent, width=theme.BTN_LED_HALO_W)

        self.draw_label_and_value(canvas, rect, focused, effect, theme)
