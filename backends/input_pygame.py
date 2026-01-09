import pygame
import time
from msui.core.events import UIEvent, NAV_LEFT, NAV_RIGHT, PAGE_PREV, PAGE_NEXT, VALUE_DELTA, TOGGLE_BYPASS, QUIT


class AccelRepeater:
    """
    Fires immediately, then repeats after delay.
    For UP/DOWN: accelerates step sizes with hold duration.
    For others: accel=False keeps step=1.
    """
    def __init__(self, first_delay_ms=250, repeat_ms=60, accel=True):
        self.first_delay = first_delay_ms / 1000.0
        self.repeat = repeat_ms / 1000.0
        self.accel = accel
        self.down_since = None
        self.last_fire = None

    def step_for_hold(self, held_s: float) -> int:
        if not self.accel:
            return 1
        if held_s < 0.6:  return 1
        if held_s < 1.2:  return 2
        if held_s < 2.0:  return 5
        return 10

    def update(self, is_down: bool):
        now = time.time()
        if is_down:
            if self.down_since is None:
                self.down_since = now
                self.last_fire = now
                return True, 1
            held = now - self.down_since
            if held >= self.first_delay and (now - self.last_fire) >= self.repeat:
                self.last_fire = now
                return True, self.step_for_hold(held)
            return False, 0

        self.down_since = None
        self.last_fire = None
        return False, 0


class PygameInput:
    """
    Maps keyboard to UI events:
      LEFT/RIGHT: select control
      UP: +1 (accelerating)
      DOWN: -1 (accelerating)
      A/D: prev/next page (repeat, no accel)
      SPACE: toggle bypass
      ESC / window close: quit
    """
    def __init__(self):
        self.rep_left  = AccelRepeater(first_delay_ms=250, repeat_ms=120, accel=False)
        self.rep_right = AccelRepeater(first_delay_ms=250, repeat_ms=120, accel=False)
        self.rep_a     = AccelRepeater(first_delay_ms=300, repeat_ms=180, accel=False)
        self.rep_d     = AccelRepeater(first_delay_ms=300, repeat_ms=180, accel=False)

        self.rep_up    = AccelRepeater(first_delay_ms=250, repeat_ms=60, accel=True)
        self.rep_down  = AccelRepeater(first_delay_ms=250, repeat_ms=60, accel=True)

        self._quit = False
        self._toggle_bypass_pressed = False

    def pump_pygame_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self._quit = True
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self._quit = True

    def get_events(self, dt_ms: int):
        if self._quit:
            return [UIEvent(QUIT)]

        events = []
        keys = pygame.key.get_pressed()

        # space (edge triggered)
        if keys[pygame.K_SPACE]:
            if not self._toggle_bypass_pressed:
                self._toggle_bypass_pressed = True
                events.append(UIEvent(TOGGLE_BYPASS))
        else:
            self._toggle_bypass_pressed = False

        fired, _ = self.rep_left.update(keys[pygame.K_LEFT])
        if fired:
            events.append(UIEvent(NAV_LEFT))

        fired, _ = self.rep_right.update(keys[pygame.K_RIGHT])
        if fired:
            events.append(UIEvent(NAV_RIGHT))

        fired, _ = self.rep_a.update(keys[pygame.K_a])
        if fired:
            events.append(UIEvent(PAGE_PREV))

        fired, _ = self.rep_d.update(keys[pygame.K_d])
        if fired:
            events.append(UIEvent(PAGE_NEXT))

        # UP: +delta
        fired, step = self.rep_up.update(keys[pygame.K_UP])
        if fired:
            events.append(UIEvent(VALUE_DELTA, delta=step))

        # DOWN: -delta
        fired, step = self.rep_down.update(keys[pygame.K_DOWN])
        if fired:
            events.append(UIEvent(VALUE_DELTA, delta=-step))

        return events
