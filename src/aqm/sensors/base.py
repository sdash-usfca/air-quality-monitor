"""The sensor contract every driver implements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict


class Sensor(ABC):
    """A sensor reads one or more metrics.

    ``read()`` returns ``{metric_key: value}`` where every key is an entry in
    ``aqm.models.METRICS``. Drivers stay dumb; the collector is sensor-agnostic.
    """

    key: str = "base"

    @abstractmethod
    def read(self) -> Dict[str, float]:
        raise NotImplementedError

    def close(self) -> None:  # optional cleanup hook
        pass
