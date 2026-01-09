from dataclasses import dataclass
from msui.controls.base import Control


@dataclass
class TextControl(Control):
    """
    Big text control (encoder-cyclable).
    Stores an int index in effect.params[key], 0..N-1.
    Renders the selected option as big centered text in the visual region.
    """
    options: tuple[str, ...] = ("A", "B")

    def _n(self) -> int:
        return max(1, len(self.options))

    def _get_index(self, effect) -> int:
        if not self.options:
            return 0
        idx = int(effect.params.get(self.key, 0))
        if self.clamp:
            return max(0, min(len(self.options) - 1, idx))
        return idx % len(self.options)
    
    def value_text(self, effect) -> str:
        # bottom text: keep consistent; we’ll show same thing as big text
        if not self.options:
            return "---"
        return self.options[self._get_index(effect)]

    def adjust(self, delta: int, effect):
        if not self.options or delta == 0:
            return
        n = len(self.options)
        idx = self._get_index(effect)
        idx2 = idx + int(delta)
    
        if self.clamp:
            idx2 = max(0, min(n - 1, idx2))
        else:
            idx2 = idx2 % n
    
        effect.params[self.key] = idx2

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        label_rect, visual_rect, _ = self.split_tile(rect, theme)

        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        # label
        lx, ly, _, _ = label_rect
        canvas.text(theme.FONT_S, lx, ly, self.label, ring)

        # big centered text
        vx, vy, vw, vh = visual_rect
        s = self.value_text(effect)

        tw, th = canvas.text_size(theme.FONT_L, s)
        canvas.text(
            theme.FONT_L,
            vx + (vw - tw) // 2,
            vy + (vh - th) // 2,
            s,
            accent if focused else ring,
        )

        # If you want NO bottom value text at all, we simply don't call draw_label_and_value().
