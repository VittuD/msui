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
    """
    options: Tuple[str, ...] = ("A", "B", "C")
    icons: Optional[Tuple[IconLike, ...]] = None

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        _, visual_rect, _ = self.split_tile(rect, theme)

        idx = self._get_index(effect)
        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        # optional midline to “ground” the wave icon (subtle)
        vx, vy, vw, vh = visual_rect
        mid_y = vy + vh // 2
        canvas.line(
            (vx + theme.ENUM_MIDLINE_PAD, mid_y),
            (vx + vw - theme.ENUM_MIDLINE_PAD, mid_y),
            ring,
            width=theme.ENUM_MIDLINE_W,
        )

        if self.icons and len(self.icons) == len(self.options):
            icon_obj = self.icons[idx]
            if isinstance(icon_obj, Icon):
                icon_obj.draw(canvas, visual_rect, accent, theme)
            else:
                icon_obj(canvas, visual_rect, accent, theme)
        else:
            bw = int(vw * theme.ENUM_FALLBACK_SCALE)
            bh = int(vh * theme.ENUM_FALLBACK_SCALE)
            bx = vx + (vw - bw) // 2
            by = vy + (vh - bh) // 2
            canvas.round_rect(
                (bx, by, bw, bh),
                radius=theme.ENUM_FALLBACK_RADIUS,
                color=accent,
                fill=False,
                width=theme.ENUM_FALLBACK_W,
            )

        self.draw_label_and_value(canvas, rect, focused, effect, theme)
