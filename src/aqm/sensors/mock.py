"""Fake sensor that simulates a realistic indoor day — no hardware required.

On top of a gentle baseline it injects occasional *events*:
  - cooking            → a sharp PM (particulate) spike that decays over minutes
  - cleaning/off-gassing → VOCs rise (gas-sensor resistance drops)
  - people coming/going → CO2 climbs while "occupied", falls when "ventilated"

This lets us exercise the thresholds, colours, charts, and (soon) alerts against
lifelike data. ``read()`` uses the wall clock; ``_read_at(now)`` takes an explicit
timestamp so the behaviour is testable.
"""
from __future__ import annotations

import math
import random
import time
from typing import Dict, List

from .base import Sensor


class _Event:
    """A transient additive disturbance: ramp up, hold at peak, then decay (seconds)."""

    def __init__(self, deltas: Dict[str, float], ramp: float, hold: float, decay: float, start: float):
        self.deltas = deltas
        self.ramp, self.hold, self.decay = ramp, hold, decay
        self.start = start

    @property
    def duration(self) -> float:
        return self.ramp + self.hold + self.decay

    def weight(self, now: float) -> float:
        t = now - self.start
        if t <= 0:
            return 0.0
        if t < self.ramp:
            return t / self.ramp
        if t < self.ramp + self.hold:
            return 1.0
        if t < self.duration:
            return max(0.0, 1.0 - (t - self.ramp - self.hold) / self.decay)
        return 0.0

    def expired(self, now: float) -> bool:
        return now - self.start >= self.duration


class MockSensor(Sensor):
    key = "mock"

    _BASELINE = {
        "pm1_0": 3.0, "pm2_5": 5.0, "pm10": 9.0,
        "temperature": 21.5, "humidity": 45.0, "pressure": 1013.0, "gas_resistance": 190.0,
    }

    def __init__(self, seed: int = None) -> None:
        self._rng = random.Random(seed)
        self._t0 = None          # set on first read
        self._last = None
        self._co2 = 480.0
        self._occupied = False
        self._events: List[_Event] = []

    def _spawn_events(self, now: float) -> None:
        r = self._rng.random
        if r() < 0.006:   # ~2/hour at a 10s interval — cooking -> PM spike
            self._events.append(_Event(
                {"pm1_0": 35, "pm2_5": 65, "pm10": 90}, ramp=30, hold=120, decay=300, start=now))
        if r() < 0.004:   # cleaning / off-gassing -> VOCs up = gas resistance down
            self._events.append(_Event(
                {"gas_resistance": -130}, ramp=20, hold=90, decay=240, start=now))

    def _update_co2(self, now: float) -> None:
        dt = now - self._last
        if self._rng.random() < 0.004:                 # someone occasionally enters/leaves
            self._occupied = not self._occupied
        target = 1450.0 if self._occupied else 470.0
        self._co2 += (target - self._co2) * (1.0 - math.exp(-dt / 240.0))  # ~4 min time constant
        self._co2 += self._rng.uniform(-8, 8)

    def read(self) -> Dict[str, float]:
        return self._read_at(time.time())

    def _read_at(self, now: float) -> Dict[str, float]:
        if self._t0 is None:
            self._t0, self._last = now, now
        self._spawn_events(now)
        self._events = [e for e in self._events if not e.expired(now)]
        self._update_co2(now)

        elapsed = now - self._t0
        rng = self._rng.uniform
        vals = {
            "co2": max(420.0, self._co2),
            "pm1_0": self._BASELINE["pm1_0"] + rng(-1, 2),
            "pm2_5": self._BASELINE["pm2_5"] + rng(-2, 3),
            "pm10": self._BASELINE["pm10"] + rng(-3, 4),
            "temperature": self._BASELINE["temperature"] + 1.5 * math.sin(elapsed / 3600) + rng(-0.2, 0.2),
            "humidity": self._BASELINE["humidity"] + 8 * math.sin(elapsed / 5000) + rng(-1, 1),
            "pressure": self._BASELINE["pressure"] + 6 * math.sin(elapsed / 20000) + rng(-0.4, 0.4),
            "gas_resistance": self._BASELINE["gas_resistance"] + rng(-10, 10),
        }
        for event in self._events:
            w = event.weight(now)
            for key, delta in event.deltas.items():
                vals[key] += delta * w

        self._last = now
        return {
            "co2": round(vals["co2"]),
            "pm1_0": round(max(0.0, vals["pm1_0"]), 1),
            "pm2_5": round(max(0.0, vals["pm2_5"]), 1),
            "pm10": round(max(0.0, vals["pm10"]), 1),
            "temperature": round(vals["temperature"], 1),
            "humidity": round(max(0.0, min(100.0, vals["humidity"]))),
            "pressure": round(vals["pressure"]),
            "gas_resistance": round(max(0.0, vals["gas_resistance"])),
        }
