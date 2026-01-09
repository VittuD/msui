# msui/core/profiler.py
from __future__ import annotations

import time


class Profiler:
    """
    Small reusable per-second profiler for demos.

    Tracks:
      - loops/s
      - renders/s
      - events/s
      - avg render ms (time spent rendering into canvas)
      - avg present ms (time spent scaling/blitting/flipping)

    Usage:
      prof = Profiler()
      ...
      prof.tick_loop()
      prof.add_events(len(events))
      prof.add_render(render_s, present_s)
      line = prof.maybe_report()
      if line: print(line)
    """

    def __init__(self, print_interval_s: float = 1.0):
        self.print_interval_s = float(print_interval_s)
        self._last_print = time.perf_counter()
        self._reset_window()

    def _reset_window(self) -> None:
        self.loops = 0
        self.renders = 0
        self.events = 0
        self.accum_render_s = 0.0
        self.accum_present_s = 0.0

    def tick_loop(self) -> None:
        self.loops += 1

    def add_events(self, n: int) -> None:
        self.events += int(n)

    def add_render(self, render_s: float, present_s: float) -> None:
        self.renders += 1
        self.accum_render_s += float(render_s)
        self.accum_present_s += float(present_s)

    def maybe_report(self) -> str | None:
        now = time.perf_counter()
        if (now - self._last_print) < self.print_interval_s:
            return None

        avg_render_ms = (self.accum_render_s / max(1, self.renders)) * 1000.0
        avg_present_ms = (self.accum_present_s / max(1, self.renders)) * 1000.0

        line = (
            f"loops={self.loops:4d}/s  renders={self.renders:4d}/s  events={self.events:4d}/s  "
            f"avg_render_ms={avg_render_ms:6.2f}  avg_present_ms={avg_present_ms:6.2f}"
        )

        self._last_print = now
        self._reset_window()
        return line
