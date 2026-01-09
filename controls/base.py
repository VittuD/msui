from dataclasses import dataclass


@dataclass
class Control:
    key: str
    label: str
    clamp: bool = True   # NEW: True=clamp, False=wrap/rollover when applicable

    # Every control is a "tile": label top, visual middle, value bottom
    def render(self, canvas, rect, focused: bool, effect, theme):
        raise NotImplementedError

    def adjust(self, delta: int, effect):
        # default: no-op
        return

    def value_text(self, effect) -> str:
        v = int(effect.params.get(self.key, 0))
        return f"-{abs(v):03d}" if v < 0 else f"{v:03d}"

    # ---- shared tile helpers ----
    @staticmethod
    def split_tile(rect, theme):
        # rect = (x, y, w, h)
        x, y, w, h = rect

        label_h = theme.TILE_LABEL_H
        value_h = theme.TILE_VALUE_H
        pad = theme.TILE_PAD

        label_rect = (x + pad, y + pad, w - 2 * pad, label_h)
        value_rect = (x + pad, y + h - value_h - pad, w - 2 * pad, value_h)
        visual_rect = (
            x + pad,
            y + pad + label_h,
            w - 2 * pad,
            h - 2 * pad - label_h - value_h,
        )
        return label_rect, visual_rect, value_rect

    @staticmethod
    def draw_tile_frame(canvas, rect, focused: bool, theme):
        x, y, w, h = rect
        # subtle outline only for focused to avoid clutter
        if focused:
            canvas.round_rect((x, y, w, h), theme.TILE_RADIUS, theme.FG, fill=False, width=2)

    def draw_label_and_value(self, canvas, rect, focused: bool, effect, theme):
        label_rect, _, value_rect = self.split_tile(rect, theme)

        lx, ly, lw, lh = label_rect
        vx, vy, vw, vh = value_rect

        label_color = theme.FG if focused else theme.DIM
        value_color = theme.FG if focused else theme.DIM

        canvas.text(theme.FONT_S, lx, ly, self.label, label_color)

        vtxt = self.value_text(effect)
        tw, _ = canvas.text_size(theme.FONT_M, vtxt)
        canvas.text(theme.FONT_M, vx + (vw - tw) // 2, vy, vtxt, value_color)
