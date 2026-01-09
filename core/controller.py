# msui/core/controller.py
from __future__ import annotations

from msui.core.dirty import (
    DIRTY_NONE,
    DIRTY_HEADER,
    DIRTY_PAGE,
    DIRTY_TILES,
    DIRTY_TILE0,
    DIRTY_TILE1,
    DIRTY_TILE2,
)
from msui.core.events import (
    NAV_LEFT,
    NAV_RIGHT,
    PAGE_PREV,
    PAGE_NEXT,
    VALUE_DELTA,
    TOGGLE_BYPASS,
    QUIT,
)
from msui.core.model import Effect


def _tile_bit(i: int) -> int:
    """
    Map a tile index to its dirty bit.
    The UI has 3 slots; pages may have 1..3 controls, but focus always stays in-range.
    """
    if i == 0:
        return DIRTY_TILE0
    if i == 1:
        return DIRTY_TILE1
    if i == 2:
        return DIRTY_TILE2
    # Defensive fallback (should never happen)
    return DIRTY_TILES


def apply_event(effect: Effect, event) -> tuple[bool, int]:
    """
    Core state update: apply one UIEvent to the Effect.
    Returns (running_ok, dirty_mask).

    This is intentionally backend-agnostic: no pygame, no rendering here.
    """
    t = event.type

    if t == QUIT:
        return False, DIRTY_NONE

    if t == TOGGLE_BYPASS:
        effect.enabled = not effect.enabled
        return True, DIRTY_HEADER

    if t == NAV_LEFT:
        n = effect.n_controls()
        old = effect.control_index
        effect.control_index = (effect.control_index - 1) % n
        new = effect.control_index
        if new == old:
            return True, DIRTY_NONE
        return True, (_tile_bit(old) | _tile_bit(new))

    if t == NAV_RIGHT:
        n = effect.n_controls()
        old = effect.control_index
        effect.control_index = (effect.control_index + 1) % n
        new = effect.control_index
        if new == old:
            return True, DIRTY_NONE
        return True, (_tile_bit(old) | _tile_bit(new))

    if t == PAGE_PREV:
        effect.page_index = (effect.page_index - 1) % len(effect.pages)
        effect.control_index %= effect.n_controls()
        return True, (DIRTY_PAGE | DIRTY_TILES)

    if t == PAGE_NEXT:
        effect.page_index = (effect.page_index + 1) % len(effect.pages)
        effect.control_index %= effect.n_controls()
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
