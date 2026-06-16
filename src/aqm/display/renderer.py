"""Render the latest readings to a Pillow image for the ST7789 TFT.

Kept separate from the hardware so the layout can be previewed to a PNG on a
laptop (``aqm-display --save preview.png``). Requires Pillow (".[display]").
"""
from __future__ import annotations

import os
from typing import Dict, Tuple

from ..models import DISPLAY_ORDER, METRICS, Status

_COLORS = {
    Status.GOOD: (46, 204, 113),
    Status.MODERATE: (241, 196, 15),
    Status.POOR: (231, 76, 60),
    Status.UNKNOWN: (140, 140, 150),
}
_BG = (18, 18, 22)
_FG = (235, 235, 235)

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
)


def _font(size: int):
    from PIL import ImageFont

    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                pass
    return ImageFont.load_default()


def render(latest: Dict[str, Tuple[float, int]], size: Tuple[int, int] = (240, 240)):
    """Return a PIL.Image: CO₂ headline on top, a 2-column grid below."""
    from PIL import Image, ImageDraw

    width, height = size
    img = Image.new("RGB", size, _BG)
    draw = ImageDraw.Draw(img)

    # Headline: CO₂
    if "co2" in latest:
        value, _ = latest["co2"]
        spec = METRICS["co2"]
        color = _COLORS[spec.status(value)]
        draw.text((12, 8), "CO2", font=_font(20), fill=_FG)
        draw.text((12, 32), spec.format(value), font=_font(60), fill=color)
        draw.text((12, 100), "ppm", font=_font(18), fill=_FG)

    # Grid of the remaining metrics, two per row.
    others = [k for k in DISPLAY_ORDER if k != "co2" and k in latest]
    x, y, col = 12, 138, 0
    for key in others:
        value, _ = latest[key]
        spec = METRICS[key]
        color = _COLORS[spec.status(value)]
        draw.text((x, y), spec.label, font=_font(13), fill=_FG)
        draw.text((x, y + 16), f"{spec.format(value)} {spec.unit}", font=_font(17), fill=color)
        col += 1
        if col % 2 == 0:
            x, y = 12, y + 46
        else:
            x = width // 2 + 6

    return img
