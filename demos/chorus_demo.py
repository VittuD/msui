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


def build_demo_effect() -> Effect:
    params = {
        # MAIN
        "rate": 0,          # signed dial demo (-12..+12)
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

        # TUNE (new page)
        "detune": 0,        # -12..+12
        "bpm": 120,         # 30..300
        "div": 2,           # enum index
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


def apply_event(effect: Effect, event) -> tuple[bool, bool]:
    t = event.type

    if t == QUIT:
        return False, False

    if t == TOGGLE_BYPASS:
        effect.enabled = not effect.enabled
        return True, True

    if t == NAV_LEFT:
        effect.control_index = (effect.control_index - 1) % 3
        return True, True

    if t == NAV_RIGHT:
        effect.control_index = (effect.control_index + 1) % 3
        return True, True

    if t == PAGE_PREV:
        effect.page_index = (effect.page_index - 1) % len(effect.pages)
        return True, True

    if t == PAGE_NEXT:
        effect.page_index = (effect.page_index + 1) % len(effect.pages)
        return True, True

    if t == VALUE_DELTA:
        ctrl = effect.current_control()
        before = effect.params.get(ctrl.key, None)
        ctrl.adjust(event.delta, effect)
        after = effect.params.get(ctrl.key, None)
        return True, (before != after)

    return True, False


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

    # --- profiling counters ---
    last_print = time.perf_counter()
    loops = 0
    renders = 0
    events_total = 0
    accum_render_s = 0.0
    accum_present_s = 0.0

    needs_redraw = True
    running = True

    while running:
        dt_ms = clock.tick(theme.FPS)
        input_src.pump_pygame_events()

        events = input_src.get_events(dt_ms)
        events_total += len(events)

        changed = False
        for ev in events:
            ok, did_change = apply_event(effect, ev)
            if not ok:
                running = False
                break
            if did_change:
                changed = True

        if changed:
            needs_redraw = True

        if needs_redraw:
            t0 = time.perf_counter()
            render_effect_editor(canvas, effect, theme)
            t1 = time.perf_counter()

            scaled = pygame.transform.scale(canvas.surface, (theme.W * theme.SCALE, theme.H * theme.SCALE))
            win.blit(scaled, (0, 0))
            pygame.display.flip()
            t2 = time.perf_counter()

            renders += 1
            accum_render_s += (t1 - t0)
            accum_present_s += (t2 - t1)
            needs_redraw = False

        loops += 1

        now = time.perf_counter()
        if now - last_print >= 1.0:
            avg_render_ms = (accum_render_s / max(1, renders)) * 1000.0
            avg_present_ms = (accum_present_s / max(1, renders)) * 1000.0
            print(
                f"loops={loops:4d}/s  renders={renders:4d}/s  events={events_total:4d}/s  "
                f"avg_render_ms={avg_render_ms:6.2f}  avg_present_ms={avg_present_ms:6.2f}"
            )

            last_print = now
            loops = 0
            renders = 0
            events_total = 0
            accum_render_s = 0.0
            accum_present_s = 0.0

    pygame.quit()


if __name__ == "__main__":
    main()
