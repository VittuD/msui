from __future__ import annotations

from dataclasses import dataclass
from msui.controls.base import Control
from msui.render.draw import draw_dial_visual


@dataclass
class DialControl(Control):
    vmin: int = 0
    vmax: int = 100
    step: int = 1

    def value_text(self, effect) -> str:
        v = int(effect.params.get(self.key, 0))
        if v < 0:
            return f"-{abs(v):03d}"
        return f"{v:03d}"

    def adjust(self, delta: int, effect):
        if delta == 0:
            return

        before = int(effect.params.get(self.key, 0))
        v = before + (int(delta) * int(self.step))

        if self.clamp:
            v = max(int(self.vmin), min(int(self.vmax), v))
        else:
            lo, hi = int(self.vmin), int(self.vmax)
            if hi < lo:
                lo, hi = hi, lo
            span = (hi - lo) + 1
            if span > 0:
                v = lo + ((v - lo) % span)

        if v != before:
            effect.params[self.key] = v
            self._log_param_change(delta=delta, before=before, after=v)

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        label_rect, visual_rect, value_rect = self.split_tile(rect, theme)

        v = int(effect.params.get(self.key, 0))
        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        draw_dial_visual(canvas, visual_rect, v, self.vmin, self.vmax, ring, accent, theme)

        # Label (top)
        lx, ly, _, _ = label_rect
        canvas.text(theme.FONT_S, lx, ly, self.label, ring)

        # Value (bottom): center the 3 digits always; draw '-' separately to the left
        vx, vy, vw, _ = value_rect
        digits = f"{abs(v):03d}"

        digits_w, _ = canvas.text_size(theme.FONT_M, digits)
        digits_x = vx + (vw - digits_w) // 2

        canvas.text(theme.FONT_M, digits_x, vy, digits, ring)

        if v < 0:
            minus_w, _ = canvas.text_size(theme.FONT_M, "-")
            canvas.text(theme.FONT_M, digits_x - minus_w - theme.DIAL_MINUS_GAP, vy, "-", ring)
