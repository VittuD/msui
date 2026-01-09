# backends/__init__.py
from .canvas import Canvas, Rect, Point, Color
from .input import InputSource

from .canvas_pygame import PygameCanvas
from .input_pygame import PygameInput

__all__ = [
    "Canvas",
    "Rect",
    "Point",
    "Color",
    "InputSource",
    "PygameCanvas",
    "PygameInput",
]
