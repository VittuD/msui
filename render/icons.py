import math
import math
from dataclasses import dataclass

### UTILS ###

from dataclasses import dataclass
import math
import warnings

@dataclass
class _MirrorCanvas:
    base: object
    rect: tuple  # (x, y, w, h)
    flip_h: bool         # top<->bottom requested
    flip_v: bool         # left<->right
    h_mode: str = "literal"   # "literal" | "below_zero"
    below_shift: float = 0.75   # fraction of half-height

    def _zero_y(self):
        x0, y0, w, h = self.rect
        return y0 + h // 2

    def _map_point(self, p):
        x0, y0, w, h = self.rect
        x, y = p
        lx = x - x0
        ly = y - y0

        # Vertical mirror (left<->right)
        if self.flip_v:
            lx = (w - 1) - lx
            
            if self.h_mode == "below_zero":
                warnings.warn("h_mode 'below_zero' is not applicable for vertical flip", ResourceWarning)

        # Horizontal mirror (top<->bottom) can be literal OR "below_zero"
        if self.flip_h:
            # 1) Always do a literal flip first
            ly = (h - 1) - ly

            if self.h_mode == "below_zero":
                half = h // 2
                shift = int(half * self.below_shift)
                ly = ly + shift

                # clamp to bottom half
                if ly < half:
                    ly = half
                if ly > (h - 1):
                    ly = h - 1

            else:
                raise ValueError(f"Unknown h_mode: {self.h_mode}")

        return (x0 + lx, y0 + ly)

    def _map_rect(self, r):
        x, y, w, h = r
        p1 = self._map_point((x, y))
        p2 = self._map_point((x + w, y + h))
        nx = min(p1[0], p2[0])
        ny = min(p1[1], p2[1])
        nw = abs(p2[0] - p1[0])
        nh = abs(p2[1] - p1[1])
        return (nx, ny, nw, nh)

    # --- transformed drawing methods used by icons ---
    def line(self, p1, p2, color, width=1):
        return self.base.line(self._map_point(p1), self._map_point(p2), color, width=width)

    def circle(self, center, r, color, width=1):
        return self.base.circle(self._map_point(center), r, color, width=width)

    def round_rect(self, rect, radius, color, fill=True, width=1):
        return self.base.round_rect(self._map_rect(rect), radius, color, fill=fill, width=width)

    def arc(self, rect, start_rad, end_rad, color, width=1):
        """
        Mirroring arcs flips angle orientation.
        NOTE: 'below_zero' folding is non-linear; arc mirroring there is approximate.
        For icons, try to prefer polylines/curves over arcs if using below_zero.
        """
        r2 = self._map_rect(rect)

        def map_ang(a):
            # literal transforms (best-effort)
            if self.flip_h and self.h_mode == "literal":
                a = -a
            if self.flip_v:
                a = math.pi - a
            return a

        s2 = map_ang(start_rad)
        e2 = map_ang(end_rad)
        return self.base.arc(r2, s2, e2, color, width=width)

    # Forward everything else unchanged (fill, text, etc.)
    def __getattr__(self, name):
        return getattr(self.base, name)


def mirror(icon_fn, flip="horizontal", h_mode="literal"):
    """
    Returns a new icon function that mirrors `icon_fn` inside its rect.

    flip:
      - "horizontal": top<->bottom
      - "vertical":   left<->right
      - "both":       both flips
      - ("horizontal","vertical"): also supported

    h_mode:
      - "literal": normal horizontal mirror across the whole rect
      - "below_zero": fold result so it stays below the 0 dB line (rect midline)
    """
    if isinstance(flip, (tuple, list)):
        flip_h = "horizontal" in flip
        flip_v = "vertical" in flip
    else:
        flip_h = flip in ("horizontal", "both")
        flip_v = flip in ("vertical", "both")

    def wrapped(canvas, rect, color, theme):
        mc = _MirrorCanvas(canvas, rect, flip_h=flip_h, flip_v=flip_v, h_mode=h_mode)
        return icon_fn(mc, rect, color, theme)

    return wrapped


def _pad_rect(rect, pad):
    x, y, w, h = rect
    return (x + pad, y + pad, max(1, w - 2 * pad), max(1, h - 2 * pad))

def _polyline(canvas, pts, color, width=2):
    for i in range(len(pts) - 1):
        canvas.line(pts[i], pts[i + 1], color, width=width)

def _bezier2(p0, p1, p2, t):
    # quadratic bezier
    x = (1-t)*(1-t)*p0[0] + 2*(1-t)*t*p1[0] + t*t*p2[0]
    y = (1-t)*(1-t)*p0[1] + 2*(1-t)*t*p1[1] + t*t*p2[1]
    return (int(x), int(y))

def _bezier3(p0, p1, p2, p3, t):
    # cubic bezier
    u = 1 - t
    x = (u*u*u)*p0[0] + 3*(u*u)*t*p1[0] + 3*u*(t*t)*p2[0] + (t*t*t)*p3[0]
    y = (u*u*u)*p0[1] + 3*(u*u)*t*p1[1] + 3*u*(t*t)*p2[1] + (t*t*t)*p3[1]
    return (int(x), int(y))

def _draw_cubic(canvas, p0, p1, p2, p3, color, width=3, steps=24):
    pts = [_bezier3(p0, p1, p2, p3, i/(steps-1)) for i in range(steps)]
    _polyline(canvas, pts, color, width=width)


### WAVEFORM ICONS ###

def wave_sine(canvas, rect, color, theme):
    x, y, w, h = _pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)
    n = max(16, w)

    pts = []
    for i in range(n):
        t = i / (n - 1)
        xx = x + int(t * (w - 1))
        yy = mid - int(math.sin(2 * math.pi * t) * amp)
        pts.append((xx, yy))
    _polyline(canvas, pts, color, width=3)

def wave_triangle(canvas, rect, color, theme):
    x, y, w, h = _pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    # triangle over one period
    p0 = (x,         mid)
    p1 = (x + w//4,  mid - amp)
    p2 = (x + 3*w//4,mid + amp)
    p3 = (x + w - 1, mid)
    _polyline(canvas, [p0, p1, p2, p3], color, width=3)

def wave_saw(canvas, rect, color, theme):
    x, y, w, h = _pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    # rising ramp then drop
    left = x
    right = x + w - 1
    top = mid - amp
    bot = mid + amp

    canvas.line((left, bot), (right, top), color, width=3)
    canvas.line((right, top), (right, bot), color, width=3)

def wave_square(canvas, rect, color, theme):
    x, y, w, h = _pad_rect(rect, 6)
    mid = y + h // 2
    amp = max(2, (h // 2) - 2)

    left = x
    right = x + w - 1
    top = mid - amp
    bot = mid + amp
    q1 = x + w//3
    q2 = x + 2*w//3

    # low -> high -> low
    canvas.line((left, bot), (q1, bot), color, width=3)
    canvas.line((q1, bot), (q1, top), color, width=3)
    canvas.line((q1, top), (q2, top), color, width=3)
    canvas.line((q2, top), (q2, bot), color, width=3)
    canvas.line((q2, bot), (right, bot), color, width=3)


### FILTER ICONS ###

def filter_lp6(canvas, rect, color, theme):
    # Gentle lowpass: flat then smooth roll-off
    x, y, w, h = _pad_rect(rect, 6)
    mid = y + h//2
    bot = y + h - 4

    p0 = (x, mid)
    p3 = (x + w - 1, bot)
    # keep first half flat-ish, then curve down
    p1 = (x + int(w*0.55), mid)
    p2 = (x + int(w*0.75), mid + int((bot-mid)*0.55))
    _draw_cubic(canvas, p0, p1, p2, p3, color, width=3)


def filter_hp6(canvas, rect, color, theme):
    # Same as LP but mirrored vertically using the utility
    mirror_lp = mirror(filter_lp6, flip="vertical", h_mode="below_zero")
    mirror_lp(canvas, rect, color, theme)


def filter_bp6(canvas, rect, color, theme):
    # Narrow bandpass: only a small region touches 0-line in the middle, sides attenuated
    x, y, w, h = _pad_rect(rect, 6)
    zero = y + h // 2
    bot  = y + h - 4

    # Narrow passband window
    left_pass  = x + int(w * 0.42)
    right_pass = x + int(w * 0.58)

    # left side: attenuated -> rise to zero
    _draw_cubic(
        canvas,
        (x, bot),
        (x + int(w * 0.18), bot),
        (x + int(w * 0.30), zero),
        (left_pass, zero),
        color, width=3, steps=18
    )

    # passband: short flat segment ON the zero line
    canvas.line((left_pass, zero), (right_pass, zero), color, width=3)

    # right side: fall back to attenuation
    _draw_cubic(
        canvas,
        (right_pass, zero),
        (x + int(w * 0.70), zero),
        (x + int(w * 0.82), bot),
        (x + w - 1, bot),
        color, width=3, steps=18
    )


def filter_notch6(canvas, rect, color, theme):
    # Same as BP but mirrored horizontally using the utility
    mirror_bp = mirror(filter_bp6, flip="horizontal", h_mode="below_zero")
    mirror_bp(canvas, rect, color, theme)


def filter_ladder(canvas, rect, color, theme):
    # Ladder LP: flat at 0-line, small resonant "knee", then roll-off
    x, y, w, h = _pad_rect(rect, 6)
    zero = y + h // 2
    bot  = y + h - 4
    top  = y + 3

    # flat section (passband)
    knee_x = x + int(w * 0.55)
    canvas.line((x, zero), (knee_x - 6, zero), color, width=3)

    # resonant knee: a bump ABOVE the line then immediate roll-off
    # (kept subtle so it reads as resonance, not "boost")
    bump_top = zero - max(2, int((zero - top) * 0.33))

    _draw_cubic(
        canvas,
        (knee_x - 6, zero),
        (knee_x - 2, zero),
        (knee_x + 2, bump_top),
        (knee_x + 8, zero),
        color, width=3, steps=10
    )

    # roll-off after knee (same shape as lp6)
    p0 = (knee_x + 8, zero)
    p3 = (x + w - 1, bot)
    p1 = (x + int(w*0.75), zero)
    p2 = (x + int(w*0.85), zero + int((bot - zero)*0.55))
    _draw_cubic(canvas, p0, p1, p2, p3, color, width=3)


def filter_pultec(canvas, rect, color, theme):
    # Pultec-ish EQ icon: low bump + mid dip + gentle high shelf (stylized)
    x, y, w, h = _pad_rect(rect, 6)
    zero = y + h // 2
    top  = y + 3
    bot  = y + h - 4

    # Define target features
    low_bump = zero - max(2, int((zero - top) * 0.55))    # small boost
    mid_dip  = zero + max(2, int((bot - zero) * 0.55))    # gentle dip
    high_shelf = zero - max(2, int((zero - top) * 0.40))  # gentle shelf

    # One smooth curve across
    p0 = (x, zero)
    p3 = (x + w - 1, high_shelf)

    p1 = (x + int(w * 0.50), low_bump)     # bass bump
    p2 = (x + int(w * 0.55), mid_dip)      # mid dip
    
    _draw_cubic(canvas, p0, p1, p2, p3, color, width=3, steps=28)

