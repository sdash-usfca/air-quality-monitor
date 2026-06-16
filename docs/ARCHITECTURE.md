# Architecture

The app is split into small layers so each can be read, tested and replaced on
its own. Data flows one direction: **sensors → collector → storage → readers**.

```
src/aqm/
├── models.py        # METRICS table: label, unit, thresholds, formatting (single source of truth)
├── config.py        # load_config() -> typed Config from config.yaml (+ defaults)
├── sensors/
│   ├── base.py      # Sensor ABC: read() -> {metric_key: value}
│   ├── mock.py      # fake but realistic readings (laptop dev, tests)
│   ├── scd41.py     # CO2 + temp + humidity (I²C)
│   ├── bme680.py    # pressure + VOC/gas (I²C)
│   └── pms5003.py   # PM1.0 / PM2.5 / PM10 (UART)
├── storage/db.py    # SQLite time series: insert / latest / history / prune
├── collector/       # timed read loop -> storage  (its own process/service)
├── web/             # Flask: dashboard + JSON API  (its own process/service)
└── display/         # render latest -> ST7789 TFT  (its own process/service)
```

## Key design decisions

**One metric table drives everything.** `models.METRICS` defines each metric's
label, unit, decimal precision, and good/moderate/poor thresholds. The web UI
and the TFT both call `spec.status(value)` and `spec.format(value)`, so colors
and formatting can never drift between screen and dashboard.

**Sensors return plain dicts.** Every driver implements `read() -> {key: value}`
where keys are entries in `METRICS`. That keeps drivers dumb and the collector
sensor-agnostic. Adding a sensor = one new module + one line in the factory.

**First-sensor-wins merge.** The collector reads sensors in the order listed in
`config.yaml` and merges their dicts, keeping the first value for any duplicated
metric. That's why the BME680 driver omits temperature/humidity by default — the
SCD41 owns those. Flip `include_temp_humidity=True` if the BME680 is your only
source.

**The database is the integration point.** Collector, web and display are
separate processes that only share the SQLite file (WAL mode for concurrent
read/write). This means you can restart the dashboard without disturbing data
collection, and each runs as its own `systemd` service.

**Mock-first.** `MockSensor` lets the entire pipeline run on a laptop, so ~80% of
the work (storage, API, dashboard, display layout) is built and tested before any
hardware arrives. Every new sensor should keep this property.

## Why Flask (not FastAPI) on the Pi Zero W

The Pi Zero W is **ARMv6**. FastAPI's stack (pydantic v2 → `pydantic-core` in
Rust, plus uvloop/httptools in C) has no prebuilt ARMv6 wheels and would try to
compile from source on a 512 MB single-core board. Flask + the standard library
is pure Python, installs in seconds, and is plenty for a home dashboard.
