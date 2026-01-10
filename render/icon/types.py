# msui/render/icon/types.py
from __future__ import annotations

from typing import Callable, Tuple, TypeAlias

Rect: TypeAlias = Tuple[int, int, int, int]
Point: TypeAlias = Tuple[int, int]

# signature: fn(canvas, rect, color, theme)
IconFn: TypeAlias = Callable[[object, Rect, tuple, object], None]
