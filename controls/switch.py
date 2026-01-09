from dataclasses import dataclass
from typing import Tuple
from msui.controls.base import Control


@dataclass
class SwitchControl(Control):
    """
    2-3 way toggle switch (vertical silhouette).
    Stored as int index in effect.params[key]:
      0 -> A (top)
      1 -> B (middle)
      2 -> C (bottom)

    Visual:
      A: lever+knob from top to socket
      B: socket only (double circle)
      C: vertical flip of A
    """
    options: Tuple[str, ...] = ("A", "B", "C")  # 2 or 3 options recommended

    def _n(self) -> int:
        return max(1, len(self.options))

    def _get_index(self, effect) -> int:
        n = self._n()
        idx = int(effect.params.get(self.key, 0))
        return max(0, min(n - 1, idx))

    def value_text(self, effect) -> str:
        if not self.options:
            return "-"
        return self.options[self._get_index(effect)]

    def adjust(self, delta: int, effect):
        """
        Clamp (no wrap):
          - UP should move toward A (top)
          - DOWN should move toward C (bottom)

        Global input sends UP = +1, DOWN = -1, so we invert delta here.
        """
        if not self.options or delta == 0:
            return

        n = self._n()
        idx = self._get_index(effect)

        idx = idx - int(delta)  # invert so UP goes toward 0 (A)
        idx = max(0, min(n - 1, idx))

        effect.params[self.key] = idx

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

        # Capsule “socket”
        sock_w = max(18, int(w * 0.42))
        sock_h = max(28, int(h * 0.62))
        sx = cx - sock_w // 2
        sy = cy - sock_h // 2
        sr = sock_w // 2

        # Outer + inner outline
        canvas.round_rect((sx, sy, sock_w, sock_h), radius=sr, color=ring, fill=False, width=3)
        canvas.round_rect(
            (sx + 3, sy + 3, sock_w - 6, sock_h - 6),
            radius=max(2, sr - 3),
            color=ring,
            fill=False,
            width=2,
        )

        # Determine visual mode
        if n <= 1:
            mode = "B"
        elif n == 2:
            mode = "A" if idx == 0 else "C"
        else:
            mode = ("A", "B", "C")[min(2, idx)]

        # Helper: normal socket rings (used in A/C)
        def draw_socket_normal():
            socket_r = max(6, int(sock_w * 0.20))
            canvas.circle((cx, cy), socket_r, ring, width=3)
            canvas.circle((cx, cy), max(2, socket_r - 3), ring, width=2)

        if mode == "B":
            # Stronger "top view" socket:
            #  - filled neutral donut (so it reads at a glance)
            #  - thick accent ring
            #  - larger accent pip
            socket_r = max(8, int(sock_w * 0.25))

            # filled neutral disc behind rings
            canvas.circle((cx, cy), socket_r, ring, width=0)

            # cut the center out slightly to make a donut impression
            inner_cut = max(2, socket_r - 4)
            canvas.circle((cx, cy), inner_cut, theme.BG, width=0)

            # accent ring on top (thicker)
            canvas.circle((cx, cy), socket_r, accent, width=3)

            # inner ring (neutral)
            canvas.circle((cx, cy), max(2, socket_r - 5), ring, width=2)

            # accent center pip (bigger)
            pip_r = max(3, socket_r // 3)
            canvas.circle((cx, cy), pip_r, accent, width=0)
            # tiny BG dot to give it a "specular" feel
            canvas.circle((cx, cy), max(1, pip_r - 2), theme.BG, width=0)
            return

        # A or C
        draw_socket_normal()

        knob_r = max(7, int(sock_w * 0.24))
        if mode == "A":
            knob_cy = sy - int(knob_r * 0.25)  # above capsule
            stem_start = (cx, knob_cy + (knob_r - 2))
        else:  # "C"
            knob_cy = sy + sock_h + int(knob_r * 0.25)  # below capsule
            stem_start = (cx, knob_cy - (knob_r - 2))

        # Stem to socket center
        canvas.line(stem_start, (cx, cy), accent, width=3)

        # End dot at socket center
        end_dot_r = max(3, knob_r // 3)
        canvas.circle((cx, cy), end_dot_r, accent, width=0)

        # Knob with inner ring
        canvas.circle((cx, knob_cy), knob_r, accent, width=0)
        canvas.circle((cx, knob_cy), max(2, knob_r - 3), theme.BG, width=2)
