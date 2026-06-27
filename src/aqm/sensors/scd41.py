"""Sensirion SCD41 — true NDIR CO₂ + temperature + humidity over I²C (0x62).

Requires the Pi extras:  pip install -e ".[pi]"
Needs on-device testing (no hardware in CI).

This driver is deliberately tolerant of flaky wiring: hand-soldered headers and
dupont jumpers don't always make a perfect contact, so an I²C transaction can
fail intermittently. Rather than crash, both init and read retry for a while.
"""
from __future__ import annotations

import logging
import time
from typing import Dict

from .base import Sensor

log = logging.getLogger(__name__)

_SCD41_ADDR = 0x62
_STOP_MEASUREMENT = bytes([0x3F, 0x86])  # exits periodic-measurement mode


class SCD41Sensor(Sensor):
    key = "scd41"

    def __init__(self) -> None:
        import board  # noqa: import lazily so the module loads on a laptop
        import busio
        import adafruit_scd4x
        from adafruit_bus_device import i2c_device

        # The SCD4x doesn't reliably ACK the zero-length "are you there?" probe
        # that adafruit_bus_device runs when it opens the device, so I2CDevice
        # raises "No I2C device at address: 0x62" even though the sensor is
        # present (i2cdetect and i2c.scan() both find it fine). Disable that one
        # probe; the real command transactions the driver uses still work.
        i2c_device.I2CDevice._I2CDevice__probe_for_device = lambda self: None

        self._i2c = busio.I2C(board.SCL, board.SDA)
        self._scd = self._init_scd(adafruit_scd4x)
        self._last: Dict[str, float] = {}

    def _stop_measurement(self) -> None:
        """Nudge the sensor back to idle (harmless if it already is)."""
        try:
            while not self._i2c.try_lock():
                pass
            try:
                self._i2c.writeto(_SCD41_ADDR, _STOP_MEASUREMENT)
            finally:
                self._i2c.unlock()
        except Exception:
            pass  # a dropped stop is fine; we retry the whole init anyway

    def _init_scd(self, adafruit_scd4x, attempts: int = 20):
        """Construct + start the sensor, retrying through intermittent I²C errors.

        A previous run can leave the sensor in periodic-measurement mode, and a
        marginal wire drops the occasional transaction, so a single attempt may
        fail with "...unavailable while in working mode". Keep trying.
        """
        last_err: Exception | None = None
        for n in range(attempts):
            self._stop_measurement()
            time.sleep(0.5)  # let stop_periodic_measurement settle
            try:
                scd = adafruit_scd4x.SCD4X(self._i2c)
                scd.start_periodic_measurement()
                if n:
                    log.info("scd41: initialised after %d retries", n)
                return scd
            except Exception as e:  # noqa: BLE001 — flaky bus, keep retrying
                last_err = e
                time.sleep(0.5)
        raise RuntimeError(
            f"SCD41 init failed after {attempts} attempts: {last_err!r}"
        )

    def read(self) -> Dict[str, float]:
        # The SCD41 emits a fresh sample about every 5 s; poll for one, shrugging
        # off transient I²C glitches from a marginal connection along the way.
        deadline = time.time() + 8
        while time.time() < deadline:
            try:
                if self._scd.data_ready:
                    self._last = {
                        "co2": float(self._scd.CO2),
                        "temperature": round(float(self._scd.temperature), 1),
                        "humidity": round(float(self._scd.relative_humidity)),
                    }
                    return self._last
            except Exception as e:  # noqa: BLE001 — transient bus error, retry
                log.debug("scd41: transient read error, retrying: %r", e)
            time.sleep(0.4)
        return self._last  # no fresh sample this cycle — reuse the previous one
