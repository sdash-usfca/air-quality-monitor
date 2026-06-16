"""Load typed configuration from config.yaml (with sensible defaults)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


@dataclass
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass
class DisplayConfig:
    enabled: bool = False
    width: int = 240
    height: int = 240
    rotation: int = 0
    refresh_seconds: int = 5


@dataclass
class Config:
    sensors: List[str] = field(default_factory=lambda: ["mock"])
    interval_seconds: int = 10
    db_path: str = "aqm.db"
    retention_days: int = 30
    web: WebConfig = field(default_factory=WebConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)


def load_config(path: Optional[str] = None) -> Config:
    """Read config from `path`, then $AQM_CONFIG, then ./config.yaml.

    A missing file is fine — you get defaults (which use the mock sensor), so the
    app runs on a fresh laptop with no setup.
    """
    path = path or os.environ.get("AQM_CONFIG", "config.yaml")
    data = {}
    if path and os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    return Config(
        sensors=data.get("sensors") or ["mock"],
        interval_seconds=int(data.get("interval_seconds", 10)),
        db_path=data.get("db_path", "aqm.db"),
        retention_days=int(data.get("retention_days", 30)),
        web=WebConfig(**(data.get("web") or {})),
        display=DisplayConfig(**(data.get("display") or {})),
    )
