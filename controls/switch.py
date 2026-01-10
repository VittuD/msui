from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from msui.controls.base import IndexedControl


@dataclass
class SwitchControl(IndexedControl):
    """
    2-3 way toggle switch (vertical silhouette).
    Stored as int index in effect.params[key]:
      0 -> A (top)
      1 -> B (middle)
      2 -> C (bottom)

    Note: UP(+delta) should move toward A (top), so delta_sign = -1.
    """
    options: Tuple[str, ...] = ("A", "B", "C")
    delta_sign: int = -1

    def render(self, canvas, rect, focused: bool, effect, theme):
        self.draw_tile_frame(canvas, rect, focused, theme)
        _, visual_rect, _ = self.split_tile(rect, theme)

        idx = self._get_index(effect)
        n = self._n()

        accent = theme.ACC_FOCUS if focused else theme.ACC_IDLE
        ring = theme.FG if focused else theme.DIM

        self._draw_switch(canvas, visual_rect, idx, n, ring, accent, theme)
        self.draw_label_and_value(canvas, rect, focused, effect, theme)

    @staticmethod
    def _draw_switch(canvas, visual_rect, idx: int, n: int, ring, accent, theme):
        x, y, w, h = visual_rect
        cx = x + w // 2
        cy = y + h // 2

        sock_w = max(18, int(w * 0.42))
        sock_h = max(28, int(h * 0.62))
        sx = cx - sock_w // 2
        sy = cy - sock_h // 2
        sr = sock_w // 2

        canvas.round_rect((sx, sy, sock_w, sock_h), radius=sr, color=ring, fill=False, width=theme.SW_OUTER_W)
        canvas.round_rect(
            (sx + 3, sy + 3, sock_w - 6, sock_h - 6),
            radius=max(2, sr - 3),
            color=ring,
            fill=False,
            width=theme.SW_INNER_W,
        )

        if n <= 1:
            mode = "B"
        elif n == 2:
            mode = "A" if idx == 0 else "C"
        else:
            mode = ("A", "B", "C")[min(2, idx)]

        def draw_socket_normal():
            socket_r = max(6, int(sock_w * 0.20))
            canvas.circle((cx, cy), socket_r, ring, width=theme.SW_SOCKET_RING_W)
            canvas.circle((cx, cy), max(2, socket_r - 3), ring, width=theme.SW_SOCKET_INNER_W)

        if mode == "B":
            socket_r = max(8, int(sock_w * 0.25))
            canvas.circle((cx, cy), socket_r, ring, width=0)
            inner_cut = max(2, socket_r - 4)
            canvas.circle((cx, cy), inner_cut, theme.BG, width=0)

            canvas.circle((cx, cy), socket_r, accent, width=theme.SW_SOCKET_RING_W)
            canvas.circle((cx, cy), max(2, socket_r - 5), ring, width=theme.SW_SOCKET_INNER_W)

            pip_r = max(3, socket_r // 3)
            canvas.circle((cx, cy), pip_r, accent, width=0)
            canvas.circle((cx, cy), max(1, pip_r - 2), theme.BG, width=0)
            return

        draw_socket_normal()

        knob_r = max(7, int(sock_w * 0.24))
        if mode == "A":
            knob_cy = sy - int(knob_r * 0.25)
            stem_start = (cx, knob_cy + (knob_r - 2))
        else:
            knob_cy = sy + sock_h + int(knob_r * 0.25)
            stem_start = (cx, knob_cy - (knob_r - 2))

        canvas.line(stem_start, (cx, cy), accent, width=theme.SW_STEM_W)

        end_dot_r = max(3, knob_r // theme.SW_END_DOT_DIV)
        canvas.circle((cx, cy), end_dot_r, accent, width=0)

        canvas.circle((cx, knob_cy), knob_r, accent, width=0)
        canvas.circle((cx, knob_cy), max(2, knob_r - 3), theme.BG, width=theme.SW_KNOB_INNER_RIM_W)
