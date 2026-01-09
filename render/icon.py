from dataclasses import dataclass
from typing import Callable

IconFn = Callable[[object, tuple, tuple, object], None]
# signature: fn(canvas, rect, color, theme)

@dataclass(frozen=True)
class Icon:
    fn: IconFn

    def draw(self, canvas, rect, color, theme):
        self.fn(canvas, rect, color, theme)
