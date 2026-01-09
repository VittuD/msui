from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Union

from msui.controls.base import IndexedControl
from msui.render.icon import Icon, IconFn

IconLike = Union[Icon, IconFn]


@dataclass
class EnumControl(IndexedControl):
    """
    Enum param stored as int index in effect.params[self.key] (0..N-1).
    Renders a waveform/icon instead of dots.

    - options: tuple of display strings (shown as value text)
    - icons: tuple of functions, one per option: icon(canvas, rect, color, theme)
    """
    options: Tuple[str, ...] = ("A", "B", "C")
    icons: Optional[Tuple[IconLike, ...]] = None
    empty_text: str = "-"          # kept consistent with previous fallback
    delta_sign: int = 1            # UP(+delta) -> next option

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        _, visual_rect, _ = self.split_tile(rect, theme)

        idx = self._get_index(effect)
        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        # optional midline to “ground” the wave icon (subtle)
        vx, vy, vw, vh = visual_rect
        mid_y = vy + vh // 2
        canvas.line((vx + 6, mid_y), (vx + vw - 6, mid_y), ring, width=1)

        # draw icon if provided and valid
        if self.icons and len(self.icons) == len(self.options) and self.options:
            icon_obj = self.icons[idx]
            if isinstance(icon_obj, Icon):
                icon_obj.draw(canvas, visual_rect, accent, theme)
            else:
                icon_obj(canvas, visual_rect, accent, theme)
        else:
            # fallback: show a simple marker box if icons missing
            bw = int(vw * 0.55)
            bh = int(vh * 0.55)
            bx = vx + (vw - bw) // 2
            by = vy + (vh - bh) // 2
            canvas.round_rect((bx, by, bw, bh), radius=10, color=accent, fill=False, width=3)

        self.draw_label_and_value(canvas, rect, focused, effect, theme)
