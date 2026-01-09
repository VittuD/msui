from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Control:
    key: str
    label: str
    clamp: bool = True   # True=clamp, False=wrap/rollover when applicable

    # Every control is a "tile": label top, visual middle, value bottom
    def render(self, canvas, rect, focused: bool, effect, theme):
        raise NotImplementedError

    def adjust(self, delta: int, effect):
        # default: no-op
        return

    def value_text(self, effect) -> str:
        # default numeric-ish formatting (Dial overrides; others override)
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


# -------------------------
# Shared base: Bool control
# -------------------------

@dataclass
class BoolControl(Control):
    """
    Common behavior for boolean parameters stored in effect.params[self.key] as True/False.

    clamp=True:
      - delta > 0 => True
      - delta < 0 => False

    clamp=False (wrap/toggle):
      - any non-zero delta toggles
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


# --------------------------------
# Shared base: Indexed option control
# --------------------------------

@dataclass
class IndexedControl(Control):
    """
    Common behavior for controls that store an int index into `options`
    in effect.params[self.key].

    clamp=True: clamp to [0..n-1]
    clamp=False: wrap modulo n

    delta_sign:
      - +1 default: UP(+delta) increments index
      - -1 e.g. SwitchControl: UP(+delta) decrements index (toward top)
    """
    options: Tuple[str, ...] = ("A", "B")
    empty_text: str = "-"
    delta_sign: int = 1

    def _n(self) -> int:
        return max(1, len(self.options))

    def _get_index(self, effect) -> int:
        if not self.options:
            return 0
        idx = int(effect.params.get(self.key, 0))
        if self.clamp:
            return max(0, min(len(self.options) - 1, idx))
        return idx % len(self.options)

    def _set_index(self, effect, idx: int) -> None:
        if not self.options:
            effect.params[self.key] = 0
            return

        n = len(self.options)
        if self.clamp:
            idx = max(0, min(n - 1, int(idx)))
        else:
            idx = int(idx) % n

        effect.params[self.key] = idx

    def value_text(self, effect) -> str:
        if not self.options:
            return self.empty_text
        return self.options[self._get_index(effect)]

    def adjust(self, delta: int, effect):
        if not self.options or delta == 0:
            return
        idx = self._get_index(effect)
        idx2 = idx + (self.delta_sign * int(delta))
        self._set_index(effect, idx2)
