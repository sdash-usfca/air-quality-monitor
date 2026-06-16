"""Metric definitions — the single source of truth for what we measure.

Both the web dashboard and the TFT display read from ``METRICS`` so that units,
formatting, plain-English descriptions, and good/moderate/poor colour grading can
never drift between them.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class Status(str, Enum):
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    UNKNOWN = "unknown"  # for metrics without health thresholds (temp, pressure, ...)


@dataclass(frozen=True)
class MetricSpec:
    key: str
    label: str
    unit: str
    good_max: Optional[float] = None
    moderate_max: Optional[float] = None
    precision: int = 0
    description: str = ""

    def status(self, value: Optional[float]) -> Status:
        """Grade a value. Assumes 'higher is worse' for thresholded metrics."""
        if value is None or self.good_max is None or self.moderate_max is None:
            return Status.UNKNOWN
        if value <= self.good_max:
            return Status.GOOD
        if value <= self.moderate_max:
            return Status.MODERATE
        return Status.POOR

    def format(self, value: Optional[float]) -> str:
        if value is None:
            return "--"
        return f"{value:.{self.precision}f}"


# Thresholds: CO2 from common indoor-air guidance; PM2.5/PM10 from US EPA AQI
# breakpoints (good / moderate boundaries). Temp/humidity/pressure/gas have no
# universal health threshold, so they render in a neutral colour.
METRICS: Dict[str, MetricSpec] = {
    "co2": MetricSpec(
        "co2", "CO₂", "ppm", good_max=800, moderate_max=1200, precision=0,
        description="Carbon dioxide — builds up in stuffy, poorly-ventilated rooms; a good proxy for how fresh the air is."),
    "pm2_5": MetricSpec(
        "pm2_5", "PM2.5", "µg/m³", good_max=12, moderate_max=35, precision=0,
        description="Fine particles ≤2.5 microns (smoke, cooking fumes) — small enough to reach deep into the lungs."),
    "pm10": MetricSpec(
        "pm10", "PM10", "µg/m³", good_max=54, moderate_max=154, precision=0,
        description="Coarse particles ≤10 microns, such as dust and pollen."),
    "pm1_0": MetricSpec(
        "pm1_0", "PM1.0", "µg/m³", precision=0,
        description="Ultrafine particles ≤1 micron — the smallest size the sensor reports."),
    "temperature": MetricSpec(
        "temperature", "Temp", "°C", precision=1,
        description="Air temperature."),
    "humidity": MetricSpec(
        "humidity", "Humidity", "%", precision=0,
        description="Relative humidity — how much moisture the air holds vs. its max (comfort is ~40–60%)."),
    "pressure": MetricSpec(
        "pressure", "Pressure", "hPa", precision=0,
        description="Barometric (atmospheric) pressure; a falling trend often precedes stormy weather."),
    "gas_resistance": MetricSpec(
        "gas_resistance", "VOC (gas)", "kΩ", precision=0,
        description="Gas-sensor resistance — LOWER means more VOCs in the air (odors, cleaning products, off-gassing)."),
}

# Order metrics are shown in (most important first).
DISPLAY_ORDER: List[str] = [
    "co2", "pm2_5", "pm10", "pm1_0",
    "temperature", "humidity", "pressure", "gas_resistance",
]
