"""Sensirion SCD41 — true NDIR CO₂ + temperature + humidity over I²C (0x62).

Requires the Pi extras:  pip install -e ".[pi]"
Needs on-device testing (no hardware in CI).
"""
from __future__ import annotations

import time
from typing import Dict

from .base import Sensor


class SCD41Sensor(Sensor):
    key = "scd41"

    def __init__(self) -> None:
        import board  # noqa: import lazily so the module loads on a laptop
        import busio
        import adafruit_scd4x

        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._scd = adafruit_scd4x.SCD4X(self._i2c)
        self._scd.start_periodic_measurement()
        self._last: Dict[str, float] = {}

    def read(self) -> Dict[str, float]:
        # The SCD41 emits a fresh sample about every 5 s; poll briefly for one.
        deadline = time.time() + 6
        while time.time() < deadline:
            if self._scd.data_ready:
                self._last = {
                    "co2": float(self._scd.CO2),
                    "temperature": round(float(self._scd.temperature), 1),
                    "humidity": round(float(self._scd.relative_humidity)),
                }
                return self._last
            time.sleep(0.5)
        return self._last  # no fresh sample this cycle — reuse the previous one
