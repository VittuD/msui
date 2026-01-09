import pygame


class PygameCanvas:
    """
    A tiny drawing API used by render/ and controls/.
    Keeps pygame isolated here.
    """
    def __init__(self, w: int, h: int, fonts: dict):
        self.w = w
        self.h = h
        self.surface = pygame.Surface((w, h))
        self.fonts = fonts

    def fill(self, color):
        self.surface.fill(color)

    def round_rect(self, rect, radius, color, fill=True, width=1):
        x, y, w, h = rect
        pygame.draw.rect(
            self.surface,
            color,
            pygame.Rect(x, y, w, h),
            0 if fill else width,
            border_radius=radius,
        )

    def circle(self, center, r, color, width=1):
        pygame.draw.circle(self.surface, color, center, r, width)

    def arc(self, rect, start_rad, end_rad, color, width=1):
        x, y, w, h = rect
        pygame.draw.arc(self.surface, color, pygame.Rect(x, y, w, h), start_rad, end_rad, width)

    def line(self, p1, p2, color, width=1):
        pygame.draw.line(self.surface, color, p1, p2, width)

    def text(self, font_key, x, y, s, color):
        font = self.fonts[font_key]
        img = font.render(s, True, color)
        self.surface.blit(img, (x, y))

    def text_size(self, font_key, s):
        font = self.fonts[font_key]
        return font.size(s)
