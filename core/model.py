from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, MutableMapping, Protocol, Tuple, runtime_checkable

from msui.core.dirty import DIRTY_ALL, DIRTY_NONE
from msui.log import LogMixin


@runtime_checkable
class ControlLike(Protocol):
    key: str
    label: str

    def render(self, canvas, rect, focused: bool, effect, theme) -> None: ...
    def adjust(self, delta: int, effect) -> None: ...
    def value_text(self, effect) -> str: ...


ControlsUpTo3 = Tuple[ControlLike, ...]


@dataclass
class Page(LogMixin):
    title: str
    controls: ControlsUpTo3

    def __post_init__(self) -> None:
        # Accept list/tuple at construction; store as tuple.
        if not isinstance(self.controls, tuple):
            self.controls = tuple(self.controls)  # type: ignore[assignment]

        n = len(self.controls)
        if n < 1 or n > 3:
            # init-time error; safe to log once
            self.log.error("invalid_page_controls", title=self.title, n_controls=n)
            raise ValueError(
                f"Page.controls must have 1..3 controls; got {n} for page '{self.title}'"
            )


@dataclass
class Effect(LogMixin):
    name: str
    pages: List[Page]
    params: MutableMapping[str, Any]

    enabled: bool = True
    page_index: int = 0
    control_index: int = 0  # 0..(n_controls-1) for current page

    # UI-only state (selection inside compound controls, etc.)
    ui: Dict[str, Any] = field(default_factory=dict)

    # Dirty mask for incremental rendering
    dirty: int = DIRTY_ALL

    def __post_init__(self) -> None:
        if not self.pages:
            self.log.error("effect_no_pages", name=self.name)
            raise ValueError("Effect.pages must be non-empty")

        # Validate each page (Page.__post_init__ already checks control count)
        for p in self.pages:
            n = len(p.controls)
            if n < 1 or n > 3:
                self.log.error("invalid_page", effect=self.name, page=p.title, n_controls=n)
                raise ValueError(f"Invalid page '{p.title}': expected 1..3 controls, got {n}")

        # Normalize indices defensively
        old_pi = int(self.page_index)
        self.page_index = old_pi % len(self.pages)

        old_ci = int(self.control_index)
        self.control_index = old_ci % self.n_controls()

        # Debug-only; happens at init (not spam)
        if self.page_index != old_pi or self.control_index != old_ci:
            self.log.debug(
                "normalize_indices",
                effect=self.name,
                page_index_before=old_pi,
                page_index_after=self.page_index,
                control_index_before=old_ci,
                control_index_after=self.control_index,
            )

    def n_pages(self) -> int:
        return len(self.pages)

    def current_page(self) -> Page:
        self.page_index = int(self.page_index) % len(self.pages)
        return self.pages[self.page_index]

    def n_controls(self) -> int:
        return len(self.current_page().controls)

    def current_control(self) -> ControlLike:
        n = self.n_controls()
        self.control_index = int(self.control_index) % n
        return self.current_page().controls[self.control_index]

    def mark_dirty(self, mask: int) -> None:
        self.dirty |= int(mask)

    def clear_dirty(self) -> None:
        self.dirty = DIRTY_NONE
