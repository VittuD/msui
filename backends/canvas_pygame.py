# backends/canvas_pygame.py
from __future__ import annotations

import pygame
from typing import Dict, Tuple
from collections import OrderedDict

from msui.backends.canvas import Canvas, Color, Point, Rect
from msui.log import LogMixin


class _LRUCache(LogMixin):
    """
    Tiny LRU cache with a hard cap to avoid unbounded growth.
    """
    def __init__(self, capacity: int):
        self.capacity = max(0, int(capacity))
        self._od: "OrderedDict[object, object]" = OrderedDict()
        self.log.debug("lru_init", capacity=self.capacity)

    def get(self, key):
        if self.capacity <= 0:
            return None
        try:
            val = self._od.pop(key)
        except KeyError:
            return None
        # re-insert as most-recent
        self._od[key] = val
        return val

    def put(self, key, val) -> None:
        if self.capacity <= 0:
            return

        if key in self._od:
            # refresh position
            try:
                self._od.pop(key)
            except KeyError:
                pass

        self._od[key] = val

        # evict least-recent
        evicted = 0
        while len(self._od) > self.capacity:
            self._od.popitem(last=False)
            evicted += 1

        if evicted:
            # DEBUG only; avoids spam
            self.log.debug("lru_evicted", count=evicted, size=len(self._od), capacity=self.capacity)

    def clear(self) -> None:
        n = len(self._od)
        self._od.clear()
        self.log.debug("lru_cleared", prev_size=n)


class PygameCanvas(LogMixin, Canvas):
    """
    Pygame implementation of the stable Canvas interface.
    Keeps pygame isolated here.
    """

    def __init__(
        self,
        w: int,
        h: int,
        fonts: Dict[str, pygame.font.Font],
        *,
        text_cache_max: int = 512,
        size_cache_max: int = 1024,
    ):
        self.w = int(w)
        self.h = int(h)
        self.surface = pygame.Surface((self.w, self.h))
        self.fonts = fonts

        # Bounded caches (memory safe)
        self._text_cache = _LRUCache(text_cache_max)
        self._size_cache = _LRUCache(size_cache_max)

        # Helpful init log (INFO is fine; it happens once)
        self.log.info(
            "canvas_init",
            backend="pygame",
            w=self.w,
            h=self.h,
            fonts=list(fonts.keys()),
            text_cache_max=int(text_cache_max),
            size_cache_max=int(size_cache_max),
        )

    def clear_caches(self) -> None:
        """
        Call this if fonts/theme are swapped at runtime.
        """
        self.log.info("canvas_clear_caches")
        self._text_cache.clear()
        self._size_cache.clear()

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
        # Cache rendered surface (bounded LRU)
        key = (font_key, s, color)
        img = self._text_cache.get(key)
        if img is None:
            font = self.fonts.get(font_key)
            if font is None:
                # This is a real bug, so warn loudly and fallback.
                self.log.warn("missing_font_key", font_key=font_key, available=list(self.fonts.keys()))
                # Pick any font deterministically to avoid crashing
                font = next(iter(self.fonts.values()))
            img = font.render(s, True, color)
            self._text_cache.put(key, img)
        self.surface.blit(img, (int(x), int(y)))

    def text_size(self, font_key: str, s: str) -> Tuple[int, int]:
        # Cache font.size results (bounded LRU)
        key = (font_key, s)
        v = self._size_cache.get(key)
        if v is None:
            font = self.fonts.get(font_key)
            if font is None:
                self.log.warn("missing_font_key_size", font_key=font_key, available=list(self.fonts.keys()))
                font = next(iter(self.fonts.values()))
            v = font.size(s)
            self._size_cache.put(key, v)
        return v
