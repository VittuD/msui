from __future__ import annotations

from dataclasses import dataclass
from msui.controls.base import IndexedControl


@dataclass
class TextControl(IndexedControl):
    """
    Big text control (encoder-cyclable).
    Stores an int index in effect.params[key], 0..N-1.
    Renders the selected option as big centered text in the visual region.
    """
    options: tuple[str, ...] = ("A", "B")
    empty_text: str = "---"
    delta_sign: int = 1

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
