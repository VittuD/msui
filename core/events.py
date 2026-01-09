from dataclasses import dataclass

NAV_LEFT = "NAV_LEFT"
NAV_RIGHT = "NAV_RIGHT"
PAGE_PREV = "PAGE_PREV"
PAGE_NEXT = "PAGE_NEXT"
VALUE_DELTA = "VALUE_DELTA"
TOGGLE_BYPASS = "TOGGLE_BYPASS"
QUIT = "QUIT"


@dataclass(frozen=True)
class UIEvent:
    type: str
    delta: int = 0
