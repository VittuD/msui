# backends/canvas_pygame.py
from __future__ import annotations

import pygame
from typing import Dict, Tuple

from msui.backends.canvas import Canvas, Color, Point, Rect


class PygameCanvas(Canvas):
    """
    Pygame implementation of the stable Canvas interface.
    Keeps pygame isolated here.
    """

    def __init__(self, w: int, h: int, fonts: Dict[str, pygame.font.Font]):
        self.w = int(w)
        self.h = int(h)
        self.surface = pygame.Surface((self.w, self.h))
        self.fonts = fonts

        # Cache rendered text surfaces and text sizes
        self._text_cache: dict[tuple[str, str, Color], pygame.Surface] = {}
        self._size_cache: dict[tuple[str, str], Tuple[int, int]] = {}

    def fill(self, color: Color) -> None:
        self.surface.fill(color)

    def round_rect(
        self,
        rect: Rect,
        radius: int,
        color: Color,
        *,
        fill: bool = True,
        width: int = 1,
    ) -> None:
        x, y, w, h = rect
        pygame.draw.rect(
            self.surface,
            color,
            pygame.Rect(int(x), int(y), int(w), int(h)),
            0 if fill else int(width),
            border_radius=int(radius),
        )

    def circle(self, center: Point, r: int, color: Color, *, width: int = 1) -> None:
        pygame.draw.circle(
            self.surface,
            color,
            (int(center[0]), int(center[1])),
            int(r),
            int(width),
        )

    def arc(
        self,
        rect: Rect,
        start_rad: float,
        end_rad: float,
        color: Color,
        *,
        width: int = 1,
    ) -> None:
        x, y, w, h = rect
        pygame.draw.arc(
            self.surface,
            color,
            pygame.Rect(int(x), int(y), int(w), int(h)),
            float(start_rad),
            float(end_rad),
            int(width),
        )

    def line(self, p1: Point, p2: Point, color: Color, *, width: int = 1) -> None:
        pygame.draw.line(
            self.surface,
            color,
            (int(p1[0]), int(p1[1])),
            (int(p2[0]), int(p2[1])),
            int(width),
        )

    def text(self, font_key: str, x: int, y: int, s: str, color: Color) -> None:
        key = (font_key, s, color)
        img = self._text_cache.get(key)
        if img is None:
            font = self.fonts[font_key]
            img = font.render(s, True, color)
            self._text_cache[key] = img
        self.surface.blit(img, (int(x), int(y)))

    def text_size(self, font_key: str, s: str) -> Tuple[int, int]:
        key = (font_key, s)
        v = self._size_cache.get(key)
        if v is None:
            font = self.fonts[font_key]
            v = font.size(s)
            self._size_cache[key] = v
        return v
