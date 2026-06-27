"""Bosch BME680 — VOC/gas resistance + pressure over I²C (0x76 or 0x77).

Reports pressure, gas, temperature and humidity. When an SCD41 is also configured
and listed *first*, the collector's "first sensor wins" merge lets the SCD41's
(self-heating-free) temp/humidity take over automatically, so it's safe to leave
include_temp_humidity on — the BME680's values are simply ignored when a better
source is present. Set include_temp_humidity=False to suppress them outright.

Note: the BME680's own temperature reads slightly high (~1-2°C) because the gas
heater warms the package; prefer the SCD41 for temperature when you have one.

Requires the Pi extras:  pip install -e ".[pi]"
Needs on-device testing (no hardware in CI).
"""
from __future__ import annotations

from typing import Dict

from .base import Sensor


class BME680Sensor(Sensor):
    key = "bme680"

    def __init__(self, address: int = 0x77, include_temp_humidity: bool = True) -> None:  # SDO→3.3V
        import board  # noqa: import lazily
        import busio
        import adafruit_bme680

        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._bme = adafruit_bme680.Adafruit_BME680_I2C(self._i2c, address=address)
        self._include_th = include_temp_humidity

    def read(self) -> Dict[str, float]:
        out: Dict[str, float] = {
            "pressure": round(float(self._bme.pressure)),
            "gas_resistance": round(float(self._bme.gas) / 1000.0),  # Ω -> kΩ
        }
        if self._include_th:
            out["temperature"] = round(float(self._bme.temperature), 1)
            out["humidity"] = round(float(self._bme.relative_humidity))
        return out
