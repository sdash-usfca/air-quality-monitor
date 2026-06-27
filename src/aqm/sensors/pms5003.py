"""Plantower PMS5003 — PM1.0 / PM2.5 / PM10 particulates over UART (/dev/serial0).

Requires the UART enabled and the serial login console disabled (docs/WIRING.md).

Requires the Pi extras:  pip install -e ".[pi]"
Needs on-device testing (no hardware in CI).
"""
from __future__ import annotations

from typing import Dict

from .base import Sensor


class PMS5003Sensor(Sensor):
    key = "pms5003"

    def __init__(
        self,
        device: str = "/dev/serial0",
        baudrate: int = 9600,
        pin_enable: str = "GPIO22",  # physical pin 15 — SET/enable
        pin_reset: str = "GPIO27",   # physical pin 13 — RESET
    ) -> None:
        from pms5003 import PMS5003  # noqa: import lazily

        self._pms = PMS5003(
            device=device, baudrate=baudrate, pin_enable=pin_enable, pin_reset=pin_reset
        )

    def read(self) -> Dict[str, float]:
        data = self._pms.read()
        return {
            "pm1_0": float(data.pm_ug_per_m3(1.0)),
            "pm2_5": float(data.pm_ug_per_m3(2.5)),
            "pm10": float(data.pm_ug_per_m3(10)),
        }
