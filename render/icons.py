import math
from dataclasses import dataclass

# --------------------
# Mirror utility
# --------------------

@dataclass
class _MirrorCanvas:
    base: object
    rect: tuple  # (x, y, w, h)
    flip_h: bool         # top<->bottom
    flip_v: bool         # left<->right
    h_mode: str = "literal"      # "literal" | "below_zero"
    below_shift: float = 0.65    # fraction of half-height (only for below_zero)

    def _map_point(self, p):
        x0, y0, w, h = self.rect
        x, y = p
        lx = x - x0
        ly = y - y0

        # left<->right
        if self.flip_v:
            lx = (w - 1) - lx

        # top<->bottom
        if self.flip_h:
            if self.h_mode == "literal":
                ly = (h - 1) - ly
            elif self.h_mode == "below_zero":
                # 1) mirror
                ly = (h - 1) - ly
                # 2) shift into bottom half, then clamp
                half = h // 2
                shift = int(half * self.below_shift)
                ly = ly + shift
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

    def line(self, p1, p2, color, width=1):
        return self.base.line(self._map_point(p1), self._map_point(p2), color, width=width)

    def circle(self, center, r, color, width=1):
        return self.base.circle(self._map_point(center), r, color, width=width)

    def round_rect(self, rect, radius, color, fill=True, width=1):
        return self.base.round_rect(self._map_rect(rect), radius, color, fill=fill, width=width)

    def arc(self, rect, start_rad, end_rad, color, width=1):
        # best-effort for literal mirror only; prefer polylines in icons
        r2 = self._map_rect(rect)

        def map_ang(a):
            if self.flip_h and self.h_mode == "literal":
                a = -a
            if self.flip_v:
                a = math.pi - a
            return a

        return self.base.arc(r2, map_ang(start_rad), map_ang(end_rad), color, width=width)

    def __getattr__(self, name):
        return getattr(self.base, name)


def mirror(icon_fn, flip="horizontal", h_mode="literal", below_shift=0.65):
    """
    flip:
      - "horizontal": top<->bottom
      - "vertical":   left<->right
      - "both":       both flips
    h_mode (only affects horizontal flip):
      - "literal"
      - "below_zero": mirror then shift into bottom half
    """
    if isinstance(flip, (tuple, list)):
        flip_h = "horizontal" in flip
        flip_v = "vertical" in flip
    else:
        flip_h = flip in ("horizontal", "both")
        flip_v = flip in ("vertical", "both")

    def wrapped(canvas, rect, color, theme):
        mc = _MirrorCanvas(
            canvas, rect,
            flip_h=flip_h, flip_v=flip_v,
            h_mode=h_mode, below_shift=below_shift
        )
        return icon_fn(mc, rect, color, theme)

    return wrapped


# --------------------
# Drawing helpers
# --------------------

def _pad_rect(rect, pad):
    x, y, w, h = rect
    return (x + pad, y + pad, max(1, w - 2 * pad), max(1, h - 2 * pad))

def _polyline(canvas, pts, color, width=2):
    for i in range(len(pts) - 1):
        canvas.line(pts[i], pts[i + 1], color, width=width)

def _bezier3(p0, p1, p2, p3, t):
    u = 1 - t
    x = (u*u*u)*p0[0] + 3*(u*u)*t*p1[0] + 3*u*(t*t)*p2[0] + (t*t*t)*p3[0]
    y = (u*u*u)*p0[1] + 3*(u*u)*t*p1[1] + 3*u*(t*t)*p2[1] + (t*t*t)*p3[1]
    return (int(x), int(y))

def _draw_cubic(canvas, p0, p1, p2, p3, color, width=3, steps=24):
    pts = [_bezier3(p0, p1, p2, p3, i/(steps-1)) for i in range(steps)]
    _polyline(canvas, pts, color, width=width)

def _arrow(canvas, x1, y1, x2, y2, color, w=2):
    canvas.line((x1, y1), (x2, y2), color, width=w)
    # small arrow head
    dx = x2 - x1
    dy = y2 - y1
    # normalize-ish for tiny head
    if abs(dx) + abs(dy) == 0:
        return
    # head size
    hs = 4
    # perpendicular
    px, py = -dy, dx
    # clamp for tiny icons
    if px > 0: px = 1
    if px < 0: px = -1
    if py > 0: py = 1
    if py < 0: py = -1
    canvas.line((x2, y2), (x2 - 2 - px*hs//2, y2 - py*hs//2), color, width=w)
    canvas.line((x2, y2), (x2 - 2 + px*hs//2, y2 + py*hs//2), color, width=w)


### BADGE ICONS ###

def badge_active(canvas, rect, color, theme):
    # Simple stompbox glyph
    x, y, w, h = _pad_rect(rect, 1)

    pw = max(14, int(w * 0.70))
    ph = max(10, int(h * 0.80))
    px = x + (w - pw) // 2
    py = y + (h - ph) // 2

    # pedal outline
    canvas.round_rect((px, py, pw, ph), radius=4, color=color, fill=False, width=2)

    # two knobs
    canvas.circle((px + int(pw * 0.30), py + int(ph * 0.25)), 2, color, width=0)
    canvas.circle((px + int(pw * 0.70), py + int(ph * 0.25)), 2, color, width=0)

    # footswitch / “active” indicator: filled
    canvas.circle((px + pw // 2, py + int(ph * 0.70)), 3, color, width=0)


def badge_bypass(canvas, rect, color, theme):
    # Stompbox + clean bypass "wire loop" under it (with terminals + rounded corners)
    x, y, w, h = _pad_rect(rect, 1)

    # pedal body
    pw = max(14, int(w * 0.70))
    ph = max(10, int(h * 0.80))
    px = x + (w - pw) // 2
    py = y + (h - ph) // 2

    canvas.round_rect((px, py, pw, ph), radius=4, color=color, fill=False, width=2)

    # knobs
    canvas.circle((px + int(pw * 0.30), py + int(ph * 0.25)), 2, color, width=0)
    canvas.circle((px + int(pw * 0.70), py + int(ph * 0.25)), 2, color, width=0)

    # footswitch hollow (inactive)
    fsx = px + pw // 2
    fsy = py + int(ph * 0.70)
    canvas.circle((fsx, fsy), 3, color, width=2)


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

# cache mirror variants once (module scope)
_filter_hp6 = mirror(filter_lp6, flip="vertical")
_filter_notch6 = mirror(filter_bp6, flip="horizontal", h_mode="below_zero", below_shift=0.65)

def filter_hp6(canvas, rect, color, theme):
    _filter_hp6(canvas, rect, color, theme)

def filter_notch6(canvas, rect, color, theme):
    _filter_notch6(canvas, rect, color, theme)


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

