# msui/backends/types.py
from __future__ import annotations

from typing import TypeAlias

Color: TypeAlias = tuple[int, int, int]          # RGB
Point: TypeAlias = tuple[int, int]               # (x, y)
Rect: TypeAlias = tuple[int, int, int, int]      # (x, y, w, h)

FontKey: TypeAlias = str
