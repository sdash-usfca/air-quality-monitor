"""Display service: render the latest readings to the ST7789 TFT.

  aqm-display                 # run forever, drawing to the TFT (on the Pi)
  aqm-display --save out.png  # render one frame to a PNG (preview on a laptop)
  aqm-display --once          # render one frame to the TFT and exit
"""
from __future__ import annotations

import argparse
import time

from ..config import load_config
from ..storage.db import Database
from .renderer import render


def main() -> None:
    parser = argparse.ArgumentParser(description="AQM display service")
    parser.add_argument("--save", metavar="PATH",
                        help="save one rendered frame to a PNG instead of the TFT")
    parser.add_argument("--once", action="store_true",
                        help="render a single frame and exit")
    args = parser.parse_args()

    config = load_config()
    db = Database(config.db_path)
    size = (config.display.width, config.display.height)

    def frame():
        return render(db.latest(), size=size)

    if args.save:
        frame().save(args.save)
        print(f"saved {args.save}")
        return

    disp = _open_tft(config)
    while True:
        disp.display(frame())
        if args.once:
            return
        time.sleep(config.display.refresh_seconds)


def _open_tft(config):
    """Open the ST7789. Pins must match your wiring (see docs/WIRING.md)."""
    import st7789  # noqa: import lazily — only needed on the Pi

    disp = st7789.ST7789(
        height=config.display.height,
        width=config.display.width,
        rotation=config.display.rotation,
        port=0, cs=0, dc=9, backlight=18,
        spi_speed_hz=80 * 1000 * 1000,
    )
    disp.begin()
    return disp


if __name__ == "__main__":
    main()
