import pygame

from msui.core.model import Effect, Page
from msui.controls.dial import DialControl
from msui.controls.button import ButtonControl
from msui.controls.enumsel import EnumControl
from msui.controls.switch import SwitchControl  # NEW
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
        "rate": 35,
        "depth": 45,
        "tone": 55,

        "sync": False,          # button
        "mode": 0,              # 3-way switch index (0..2)  NEW
        "wave": 0,              # enum index
        "filter": 0,            # enum index

        "pre": 10,
        "post": 70,
        "dry": 90,
    }

    pages = [
        Page("MAIN", [
            DialControl(key="rate", label="RATE", vmin=0, vmax=100, step=1),
            SwitchControl(key="mode", label="MODE", options=("A", "B", "C")),  # NEW
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
    ]

    return Effect(name="CHORUS", pages=pages, params=params)


def apply_event(effect: Effect, event):
    t = event.type

    if t == QUIT:
        return False

    if t == TOGGLE_BYPASS:
        effect.enabled = not effect.enabled
        return True

    if t == NAV_LEFT:
        effect.control_index = (effect.control_index - 1) % 3
        return True

    if t == NAV_RIGHT:
        effect.control_index = (effect.control_index + 1) % 3
        return True

    if t == PAGE_PREV:
        effect.page_index = (effect.page_index - 1) % len(effect.pages)
        return True

    if t == PAGE_NEXT:
        effect.page_index = (effect.page_index + 1) % len(effect.pages)
        return True

    if t == VALUE_DELTA:
        ctrl = effect.current_control()
        ctrl.adjust(event.delta, effect)
        return True

    return True


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
    input_src = PygameInput()
    clock = pygame.time.Clock()

    effect = build_demo_effect()

    running = True
    while running:
        dt_ms = clock.tick(theme.FPS)
        input_src.pump_pygame_events()

        for ev in input_src.get_events(dt_ms):
            ok = apply_event(effect, ev)
            if not ok:
                running = False
                break

        render_effect_editor(canvas, effect, theme)

        scaled = pygame.transform.scale(canvas.surface, (theme.W * theme.SCALE, theme.H * theme.SCALE))
        win.blit(scaled, (0, 0))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
