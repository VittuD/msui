# backends/input_pygame.py
from __future__ import annotations

import pygame

from msui.backends.input import InputSource
from msui.core.events import (
    UIEvent,
    NAV_LEFT,
    NAV_RIGHT,
    PAGE_PREV,
    PAGE_NEXT,
    VALUE_DELTA,
    TOGGLE_BYPASS,
    QUIT,
)
from msui.log import LogMixin


class AccelRepeater(LogMixin):
    """
    Deterministic (dt-based) key repeater.

    - Fires immediately on press.
    - Then repeats after first_delay, at repeat interval.
    - Optional acceleration for UP/DOWN via step_for_hold(held_s).

    This avoids dependence on wall clock jitter and behaves consistently
    across machines/fps hiccups as long as dt_ms is provided.
    """

    def __init__(self, first_delay_ms: int = 250, repeat_ms: int = 60, accel: bool = True, *, name: str = "key"):
        self.name = str(name)
        self.first_delay_s = max(0.0, float(first_delay_ms) / 1000.0)
        self.repeat_s = max(0.001, float(repeat_ms) / 1000.0)
        self.accel = bool(accel)

        self._was_down = False
        self._held_s = 0.0
        self._since_fire_s = 0.0

        self.log.debug(
            "repeater_init",
            name=self.name,
            first_delay_ms=int(first_delay_ms),
            repeat_ms=int(repeat_ms),
            accel=self.accel,
        )

    def step_for_hold(self, held_s: float) -> int:
        if not self.accel:
            return 1
        if held_s < 0.6:
            return 1
        if held_s < 1.2:
            return 2
        if held_s < 2.0:
            return 5
        return 10

    def reset(self) -> None:
        self._was_down = False
        self._held_s = 0.0
        self._since_fire_s = 0.0

    def update(self, is_down: bool, dt_s: float) -> tuple[bool, int]:
        dt_s = max(0.0, float(dt_s))

        if not is_down:
            if self._was_down:
                # Edge: released (debug only)
                self.log.debug("repeater_release", name=self.name, held_s=round(self._held_s, 3))
            self.reset()
            return False, 0

        # down
        if not self._was_down:
            # edge: fire immediately
            self._was_down = True
            self._held_s = 0.0
            self._since_fire_s = 0.0
            self.log.debug("repeater_press", name=self.name)
            return True, 1

        # held
        self._held_s += dt_s
        self._since_fire_s += dt_s

        if self._held_s >= self.first_delay_s and self._since_fire_s >= self.repeat_s:
            # Fire at most once per frame to keep event rates stable.
            self._since_fire_s = 0.0
            step = self.step_for_hold(self._held_s)
            return True, step

        return False, 0


class PygameInput(LogMixin, InputSource):
    """
    Pygame-based input handler with deterministic dt-based repeat + acceleration.
    Implements the stable InputSource interface.

    Stable API:
      - pump()
      - get_events(dt_ms)

    Back-compat:
      - pump_pygame_events() alias for pump()
    """

    def __init__(self, theme):
        fps = max(1.0, float(getattr(theme, "FPS", 60)))
        first_delay_s = float(getattr(theme, "INPUT_FIRST_DELAY_S", 0.25))
        first_delay_ms = int(max(0.0, first_delay_s) * 1000)

        def ratio_to_repeat_ms(ratio: float, *, max_hz: float | None = None) -> int:
            hz = fps * max(0.0, float(ratio))
            if max_hz is not None:
                hz = min(hz, max_hz)
            if hz <= 0.0:
                return 10**9  # effectively never
            return max(1, int(1000.0 / hz))

        updown_ms = ratio_to_repeat_ms(getattr(theme, "INPUT_REPEAT_UPDOWN_RATIO", 1.0), max_hz=20.0)
        nav_ms = ratio_to_repeat_ms(getattr(theme, "INPUT_REPEAT_NAV_RATIO", 0.6), max_hz=12.0)
        page_ms = ratio_to_repeat_ms(getattr(theme, "INPUT_REPEAT_PAGE_RATIO", 0.4), max_hz=8.0)

        # Named repeaters for nicer logs
        self.rep_left = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=nav_ms, accel=False, name="LEFT")
        self.rep_right = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=nav_ms, accel=False, name="RIGHT")
        self.rep_a = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=page_ms, accel=False, name="A")
        self.rep_d = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=page_ms, accel=False, name="D")

        self.rep_up = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=updown_ms, accel=True, name="UP")
        self.rep_down = AccelRepeater(first_delay_ms=first_delay_ms, repeat_ms=updown_ms, accel=True, name="DOWN")

        self._quit = False
        self._toggle_bypass_pressed = False

        self.log.info(
            "input_init",
            backend="pygame",
            fps=fps,
            first_delay_ms=first_delay_ms,
            updown_repeat_ms=updown_ms,
            nav_repeat_ms=nav_ms,
            page_repeat_ms=page_ms,
        )

    # --- stable interface ---
    def pump(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self._quit = True
                self.log.info("quit_event", source="pygame.QUIT")
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._quit = True
                    self.log.info("quit_event", source="ESCAPE")

    # --- back-compat alias ---
    def pump_pygame_events(self) -> None:
        self.pump()

    def get_events(self, dt_ms: int):
        if self._quit:
            return [UIEvent(QUIT)]

        dt_s = max(0.0, float(dt_ms)) / 1000.0
        events: list[UIEvent] = []
        keys = pygame.key.get_pressed()

        # space (edge triggered)
        if keys[pygame.K_SPACE]:
            if not self._toggle_bypass_pressed:
                self._toggle_bypass_pressed = True
                events.append(UIEvent(TOGGLE_BYPASS))
                self.log.debug("event", type=TOGGLE_BYPASS)
        else:
            self._toggle_bypass_pressed = False

        fired, _ = self.rep_left.update(keys[pygame.K_LEFT], dt_s)
        if fired:
            events.append(UIEvent(NAV_LEFT))
            self.log.debug("event", type=NAV_LEFT)

        fired, _ = self.rep_right.update(keys[pygame.K_RIGHT], dt_s)
        if fired:
            events.append(UIEvent(NAV_RIGHT))
            self.log.debug("event", type=NAV_RIGHT)

        fired, _ = self.rep_a.update(keys[pygame.K_a], dt_s)
        if fired:
            events.append(UIEvent(PAGE_PREV))
            self.log.debug("event", type=PAGE_PREV)

        fired, _ = self.rep_d.update(keys[pygame.K_d], dt_s)
        if fired:
            events.append(UIEvent(PAGE_NEXT))
            self.log.debug("event", type=PAGE_NEXT)

        # UP: +delta
        fired, step = self.rep_up.update(keys[pygame.K_UP], dt_s)
        if fired:
            events.append(UIEvent(VALUE_DELTA, delta=step))
            self.log.debug("event", type=VALUE_DELTA, delta=step)

        # DOWN: -delta
        fired, step = self.rep_down.update(keys[pygame.K_DOWN], dt_s)
        if fired:
            events.append(UIEvent(VALUE_DELTA, delta=-step))
            self.log.debug("event", type=VALUE_DELTA, delta=-step)

        return events
