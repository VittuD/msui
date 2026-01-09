from dataclasses import dataclass
from msui.controls.base import Control
from msui.render.draw import draw_dial_visual


@dataclass
class DialControl(Control):
    vmin: int = 0
    vmax: int = 100
    step: int = 1

    def adjust(self, delta: int, effect):
        v = int(effect.params.get(self.key, 0))
        v += int(delta) * self.step
        v = max(self.vmin, min(self.vmax, v))
        effect.params[self.key] = v

    def render(self, canvas, rect, focused: bool, effect, theme):
        # Tile frame + label/value in consistent layout
        self.draw_tile_frame(canvas, rect, focused, theme)
        label_rect, visual_rect, value_rect = self.split_tile(rect, theme)

        # Dial visual in middle
        v = int(effect.params.get(self.key, 0))
        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        draw_dial_visual(canvas, visual_rect, v, ring, accent, theme)

        # Label + value text
        self.draw_label_and_value(canvas, rect, focused, effect, theme)
