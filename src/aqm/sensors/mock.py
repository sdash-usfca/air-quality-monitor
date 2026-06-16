"""A fake sensor that produces realistic, slowly-drifting readings.

Lets you build and test the entire pipeline — storage, API, dashboard, display —
on a laptop with no hardware. CO₂ follows a slow sine so you can watch the
dashboard change colour over a few minutes.
"""
from __future__ import annotations

import math
import random
import time
from typing import Dict

from .base import Sensor


class MockSensor(Sensor):
    key = "mock"

    def __init__(self) -> None:
        self._t0 = time.time()
        self._state = {
            "pm2_5": 8.0, "pm10": 14.0, "pm1_0": 5.0,
            "temperature": 21.5, "humidity": 45.0,
            "pressure": 1013.0, "gas_resistance": 120.0,
        }

    def _walk(self, key: str, lo: float, hi: float, step: float) -> float:
        v = self._state[key] + random.uniform(-step, step)
        v = max(lo, min(hi, v))
        self._state[key] = v
        return v

    def read(self) -> Dict[str, float]:
        # CO2: slow ~4-minute sine (420–1570 ppm) so colours visibly cycle.
        t = time.time() - self._t0
        co2 = 700 + 450 * (0.5 + 0.5 * math.sin(t / 120.0)) + random.uniform(-40, 40)
        return {
            "co2": round(max(420.0, co2)),
            "pm2_5": round(self._walk("pm2_5", 2, 45, 3), 1),
            "pm10": round(self._walk("pm10", 4, 90, 4), 1),
            "pm1_0": round(self._walk("pm1_0", 1, 30, 2), 1),
            "temperature": round(self._walk("temperature", 17, 27, 0.2), 1),
            "humidity": round(self._walk("humidity", 30, 65, 1)),
            "pressure": round(self._walk("pressure", 995, 1030, 0.5)),
            "gas_resistance": round(self._walk("gas_resistance", 30, 250, 10)),
        }
