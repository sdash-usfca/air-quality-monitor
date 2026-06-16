"""Sensor factory. Hardware libraries are imported lazily inside each driver, so
importing this module (and using the mock) works fine on a laptop."""
from __future__ import annotations

from .base import Sensor

KNOWN = ("mock", "scd41", "bme680", "pms5003")


def create_sensor(key: str) -> Sensor:
    key = key.lower()
    if key == "mock":
        from .mock import MockSensor
        return MockSensor()
    if key == "scd41":
        from .scd41 import SCD41Sensor
        return SCD41Sensor()
    if key == "bme680":
        from .bme680 import BME680Sensor
        return BME680Sensor()
    if key == "pms5003":
        from .pms5003 import PMS5003Sensor
        return PMS5003Sensor()
    raise ValueError(f"Unknown sensor '{key}'. Known: {', '.join(KNOWN)}")
