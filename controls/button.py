from __future__ import annotations

from dataclasses import dataclass
from msui.controls.base import BoolControl


@dataclass
class ButtonControl(BoolControl):
    """
    Bool param stored in effect.params[self.key] as True/False.
    Visual: LED indicator only (no base), OFF is intentionally very empty.
    Inherits clamp/toggle behavior + value_text from BoolControl.
    """

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        _, visual_rect, _ = self.split_tile(rect, theme)

        x, y, w, h = visual_rect
        is_on = bool(effect.params.get(self.key, False))

        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        # LED centered in the visual region
        cx = x + w // 2
        cy = y + h // 2
        led_r = max(7, min(w, h) // 5)

        if is_on:
            # Outer glow ring
            canvas.circle((cx, cy), led_r + 3, accent, width=2)
            # LED body
            canvas.circle((cx, cy), led_r, accent, width=0)
            # Inner rim to add "lens" feel
            canvas.circle((cx, cy), max(2, led_r - 2), theme.BG, width=2)
            # Specular highlight dot
            canvas.circle((cx - led_r // 3, cy - led_r // 3), max(2, led_r // 4), theme.FG, width=0)
        else:
            # OFF: very empty lens ring
            canvas.circle((cx, cy), led_r, ring, width=2)
            canvas.circle((cx, cy), max(2, led_r - 2), theme.BG, width=0)

        # Focus halo (subtle)
        if focused:
            canvas.circle((cx, cy), led_r + 6, accent, width=1)

        self.draw_label_and_value(canvas, rect, focused, effect, theme)
