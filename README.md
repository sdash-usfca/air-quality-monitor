# 🌬️ air-quality-monitor

A DIY indoor **air quality monitor** built on a Raspberry Pi. It reads CO₂,
particulate matter, VOCs, temperature, humidity and pressure, shows them on a
small color TFT for the wall, and serves a live **web dashboard** over your home
network. History is logged to SQLite so you can see trends.

Designed as a learning project: it's split into clean layers (sensor drivers →
collector → storage → web/display) so each piece is easy to understand, test,
and swap. You can build and run the **entire app on your laptop** using a mock
sensor — no hardware required to get started.

> ⚠️ **Safety:** the optional carbon-monoxide reading is for curiosity and
> logging only. It is **not** a life-safety device. Keep a certified CO alarm.

## Features

- 📈 **Real metrics:** CO₂ (the true "is this room stuffy" number), PM1/PM2.5/PM10
  particulates, VOC/gas, temperature, humidity, pressure.
- 🟢🟡🔴 **Status at a glance:** every metric is graded good / moderate / poor from
  one shared threshold table — used by both the screen and the web UI.
- 🖥️ **Web dashboard:** live cards + history charts, dependency-free vanilla JS.
- 📺 **Wall display:** color ST7789 TFT, with a PNG-preview mode for your laptop.
- 💾 **History:** lightweight SQLite time series with automatic pruning.
- 🧪 **Mock sensor:** develop the whole stack with no hardware.

## Hardware

Target board: **Raspberry Pi Zero W** (ARMv6 — that's why the stack is Flask +
pure-Python, no Rust/C wheels to compile). Works on any Pi.

See [docs/BOM.md](docs/BOM.md) for the full parts list and
[docs/WIRING.md](docs/WIRING.md) for how to connect everything.

## Quickstart — on your laptop (no hardware)

```bash
cd air-quality-monitor
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,display]"
cp config.example.yaml config.yaml          # defaults to the mock sensor

# terminal 1 — generate fake readings into the database
aqm-collect

# terminal 2 — serve the dashboard
aqm-web
# open http://localhost:8000
```

Preview the wall display layout without a screen:

```bash
aqm-display --save preview.png && open preview.png
```

## On the Raspberry Pi

```bash
git clone <your-fork-url> air-quality-monitor && cd air-quality-monitor
./scripts/install.sh                         # venv + ".[pi]" + next-step hints
cp config.example.yaml config.yaml
# edit config.yaml -> sensors: [scd41, bme680, pms5003], display.enabled: true
```

Then enable I²C/SPI/UART and install the services — see
[docs/WIRING.md](docs/WIRING.md) and [scripts/install.sh](scripts/install.sh).

## Architecture

```
Sensors (SCD41 / BME680 / PMS5003)        ← drivers, one module each (I²C / UART)
        │  Sensor.read() -> {metric: value}
        ▼
Collector service  ──────────────────────► SQLite (time series)
 (timed read loop, first-sensor-wins merge)        │
                                                    ├──► Flask web app  → dashboard + JSON API
                                                    └──► Display service → ST7789 TFT
```

Details and design rationale in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Roadmap

- [ ] Per-metric history charts + selectable time ranges
- [ ] WebSocket / SSE push instead of polling
- [ ] Threshold alerts (e.g. CO₂ > 1500 ppm) + notifications
- [ ] Home Assistant / MQTT integration
- [ ] 3D-printed enclosure (STL + source CAD) in [hardware/](hardware/)

## Contributing

PRs and forks welcome — this is meant to be copied and adapted. Please keep the
layered structure and add a mock path for any new sensor so it stays
laptop-testable.

## License

MIT — see [LICENSE](LICENSE).
