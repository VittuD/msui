# msui/render/icons.py
"""
Compatibility facade.

Historical imports used:
  from msui.render import icons as wave_icons

Now the canonical implementation lives in msui.render.icon (package).
This module re-exports the same names for backwards compatibility.
"""

from __future__ import annotations

from msui.render.icon import (  # helper
    mirror,
    # badges
    badge_active,
    badge_bypass,
    # waves
    wave_sine,
    wave_triangle,
    wave_saw,
    wave_square,
    # filters
    filter_lp6,
    filter_hp6,
    filter_bp6,
    filter_notch6,
    filter_ladder,
    filter_pultec,
)

__all__ = [
    # helper
    "mirror",
    # badges
    "badge_active",
    "badge_bypass",
    # waves
    "wave_sine",
    "wave_triangle",
    "wave_saw",
    "wave_square",
    # filters
    "filter_lp6",
    "filter_hp6",
    "filter_bp6",
    "filter_notch6",
    "filter_ladder",
    "filter_pultec",
]
