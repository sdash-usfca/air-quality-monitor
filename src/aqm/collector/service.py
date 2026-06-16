"""The collector: read every sensor on a timer and store the results."""
from __future__ import annotations

import logging
import signal
import time
from typing import Dict, List

from ..config import Config, load_config
from ..sensors import create_sensor
from ..sensors.base import Sensor
from ..storage.db import Database

log = logging.getLogger("aqm.collector")


class Collector:
    def __init__(self, config: Config):
        self.config = config
        self.db = Database(config.db_path)
        self.sensors: List[Sensor] = []
        self._running = True

    def setup(self) -> None:
        self.db.init_schema()
        for key in self.config.sensors:
            try:
                self.sensors.append(create_sensor(key))
                log.info("initialised sensor: %s", key)
            except Exception as exc:  # noqa: BLE001 — keep going with other sensors
                log.error("failed to init sensor '%s': %s", key, exc)
        if not self.sensors:
            raise SystemExit("No sensors initialised — check 'sensors' in config.yaml")

    def read_once(self) -> Dict[str, float]:
        """Read all sensors and merge. First sensor in config order wins ties."""
        merged: Dict[str, float] = {}
        for sensor in self.sensors:
            try:
                for key, value in sensor.read().items():
                    merged.setdefault(key, value)
            except Exception as exc:  # noqa: BLE001 — one bad sensor shouldn't stop the rest
                log.warning("sensor '%s' read failed: %s", getattr(sensor, "key", sensor), exc)
        return merged

    def run(self) -> None:
        self.setup()
        signal.signal(signal.SIGTERM, self._stop)
        signal.signal(signal.SIGINT, self._stop)
        log.info("collector started; interval=%ss sensors=%s",
                 self.config.interval_seconds, self.config.sensors)

        while self._running:
            ts = int(time.time())
            values = self.read_once()
            if values:
                self.db.insert_readings(ts, values)
                log.info("stored %d metrics: %s", len(values), values)
            if self.config.retention_days > 0:
                self.db.prune(ts - self.config.retention_days * 86400)
            self._sleep(self.config.interval_seconds)

        for sensor in self.sensors:
            try:
                sensor.close()
            except Exception:  # noqa: BLE001
                pass
        log.info("collector stopped")

    def _sleep(self, seconds: float) -> None:
        """Sleep in small slices so SIGTERM/SIGINT is responsive."""
        slept = 0.0
        while self._running and slept < seconds:
            time.sleep(0.5)
            slept += 0.5

    def _stop(self, *_args) -> None:
        self._running = False


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    Collector(load_config()).run()
