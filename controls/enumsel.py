from dataclasses import dataclass
from typing import Callable, Optional, Tuple
from msui.controls.base import Control

IconFn = Callable[[object, tuple, tuple, object], None]
# signature: icon(canvas, rect, color, theme)

@dataclass
class EnumControl(Control):
    """
    Enum param stored as int index in effect.params[self.key] (0..N-1).
    Renders a waveform/icon instead of dots.

    - options: tuple of display strings (shown as value text)
    - icons: tuple of functions, one per option: icon(canvas, rect, color, theme)
    """
    options: Tuple[str, ...] = ("A", "B", "C")
    icons: Optional[Tuple[IconFn, ...]] = None

    def _n(self):
        return max(1, len(self.options))

    def _get_index(self, effect) -> int:
        idx = int(effect.params.get(self.key, 0))
        if len(self.options) == 0:
            return 0
        return idx % len(self.options)

    def value_text(self, effect) -> str:
        if not self.options:
            return "-"
        return self.options[self._get_index(effect)]

    def adjust(self, delta: int, effect):
        if not self.options or delta == 0:
            return
        idx = self._get_index(effect)
        idx = (idx + int(delta)) % len(self.options)
        effect.params[self.key] = idx

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
        if self.icons and len(self.icons) == len(self.options):
            icon_fn = self.icons[idx]
            icon_fn(canvas, visual_rect, accent, theme)
        else:
            # fallback: show a simple marker box if icons missing
            bw = int(vw * 0.55)
            bh = int(vh * 0.55)
            bx = vx + (vw - bw) // 2
            by = vy + (vh - bh) // 2
            canvas.round_rect((bx, by, bw, bh), radius=10, color=accent, fill=False, width=3)

        self.draw_label_and_value(canvas, rect, focused, effect, theme)
