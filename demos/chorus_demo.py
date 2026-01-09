from __future__ import annotations

import time
import pygame

from msui.core.model import Effect, Page
from msui.controls.dial import DialControl
from msui.controls.button import ButtonControl
from msui.controls.enumsel import EnumControl
from msui.controls.switch import SwitchControl
from msui.controls.text import TextControl
from msui.render.theme import Theme
from msui.render import icons as wave_icons
from msui.render.screen_effect import render_effect_editor
from msui.backends.canvas_pygame import PygameCanvas
from msui.backends.input_pygame import PygameInput
from msui.core.events import (
    NAV_LEFT, NAV_RIGHT, PAGE_PREV, PAGE_NEXT, VALUE_DELTA, TOGGLE_BYPASS, QUIT
)
from msui.core.dirty import (
    DIRTY_NONE,
    DIRTY_ALL,
    DIRTY_HEADER,
    DIRTY_PAGE,
    DIRTY_TILES,
    DIRTY_TILE0,
    DIRTY_TILE1,
    DIRTY_TILE2,
)
from msui.core.profiler import Profiler


def build_demo_effect() -> Effect:
    params = {
        # MAIN
        "rate": 0,
        "mode": 0,
        "sync": False,

        # MOD
        "wave": 0,
        "filter": 0,
        "tone": 55,

        # LEVEL
        "pre": 10,
        "post": 70,
        "dry": 90,

        # TUNE
        "detune": 0,
        "bpm": 120,
        "div": 2,
    }

    pages = [
        Page("MAIN", [
            DialControl(key="rate", label="RATE", vmin=-12, vmax=12, step=1),
            SwitchControl(key="mode", label="MODE", options=("A", "B", "C")),
            ButtonControl(key="sync", label="SYNC", true_text="ON", false_text="OFF"),
        ]),
        Page("MOD", [
            EnumControl(
                key="wave",
                label="WAVE",
                options=("SINE", "TRI", "SAW", "SQR"),
                icons=(wave_icons.wave_sine, wave_icons.wave_triangle, wave_icons.wave_saw, wave_icons.wave_square),
            ),
            EnumControl(
                key="filter",
                label="FILTER",
                options=("LP6", "HP6", "BP6", "NOTCH", "LADDER", "PULTEC"),
                icons=(
                    wave_icons.filter_lp6,
                    wave_icons.filter_hp6,
                    wave_icons.filter_bp6,
                    wave_icons.filter_notch6,
                    wave_icons.filter_ladder,
                    wave_icons.filter_pultec,
                ),
            ),
            DialControl(key="tone", label="TONE", vmin=0, vmax=100, step=1),
        ]),
        Page("LEVEL", [
            DialControl(key="pre", label="PRE", vmin=0, vmax=100, step=1),
            DialControl(key="post", label="POST", vmin=0, vmax=100, step=1),
            DialControl(key="dry", label="DRY", vmin=0, vmax=100, step=1),
        ]),
        Page("TUNE", [
            DialControl(key="detune", label="DETUNE", vmin=-12, vmax=12, step=1),
            DialControl(key="bpm", label="BPM", vmin=30, vmax=300, step=1),
            TextControl(
                key="div",
                label="DIV",
                options=("1/1", "1/2", "1/4", "1/8", "1/16"),
            ),
        ]),
    ]

    return Effect(name="CHORUS", pages=pages, params=params)


def _tile_bit(i: int) -> int:
    return (DIRTY_TILE0, DIRTY_TILE1, DIRTY_TILE2)[i]


def apply_event(effect: Effect, event) -> tuple[bool, int]:
    """
    Returns (running_ok, dirty_mask).
    """
    t = event.type

    if t == QUIT:
        return False, DIRTY_NONE

    if t == TOGGLE_BYPASS:
        effect.enabled = not effect.enabled
        return True, DIRTY_HEADER

    if t == NAV_LEFT:
        old = effect.control_index
        effect.control_index = (effect.control_index - 1) % 3
        new = effect.control_index
        return True, (_tile_bit(old) | _tile_bit(new))

    if t == NAV_RIGHT:
        old = effect.control_index
        effect.control_index = (effect.control_index + 1) % 3
        new = effect.control_index
        return True, (_tile_bit(old) | _tile_bit(new))

    if t == PAGE_PREV:
        effect.page_index = (effect.page_index - 1) % len(effect.pages)
        return True, (DIRTY_PAGE | DIRTY_TILES)

    if t == PAGE_NEXT:
        effect.page_index = (effect.page_index + 1) % len(effect.pages)
        return True, (DIRTY_PAGE | DIRTY_TILES)

    if t == VALUE_DELTA:
        ctrl = effect.current_control()
        before = effect.params.get(ctrl.key, None)
        ctrl.adjust(event.delta, effect)
        after = effect.params.get(ctrl.key, None)

        if before != after:
            return True, _tile_bit(effect.control_index)
        return True, DIRTY_NONE

    return True, DIRTY_NONE


def main():
    pygame.init()

    theme = Theme()
    win = pygame.display.set_mode((theme.W * theme.SCALE, theme.H * theme.SCALE))
    pygame.display.set_caption("MS-style UI (modular)")

    fonts = {
        "S": pygame.font.SysFont("dejavusansmono", 14, bold=True),
        "M": pygame.font.SysFont("dejavusansmono", 18, bold=True),
        "L": pygame.font.SysFont("dejavusansmono", 22, bold=True),
    }

    canvas = PygameCanvas(theme.W, theme.H, fonts)
    input_src = PygameInput(theme)
    clock = pygame.time.Clock()

    effect = build_demo_effect()

    prof = Profiler(print_interval_s=1.0)

    dirty = DIRTY_ALL
    running = True

    while running:
        dt_ms = clock.tick(theme.FPS)
        input_src.pump()

        events = input_src.get_events(dt_ms)
        prof.add_events(len(events))

        for ev in events:
            ok, d = apply_event(effect, ev)
            if not ok:
                running = False
                break
            dirty |= d

        if dirty != DIRTY_NONE:
            t0 = time.perf_counter()
            render_effect_editor(canvas, effect, theme, dirty_mask=dirty)
            t1 = time.perf_counter()

            scaled = pygame.transform.scale(canvas.surface, (theme.W * theme.SCALE, theme.H * theme.SCALE))
            win.blit(scaled, (0, 0))
            pygame.display.flip()
            t2 = time.perf_counter()

            prof.add_render(t1 - t0, t2 - t1)
            dirty = DIRTY_NONE

        prof.tick_loop()
        line = prof.maybe_report()
        if line:
            print(line)

    pygame.quit()


if __name__ == "__main__":
    main()
