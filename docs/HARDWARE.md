# Hardware — as-built log

What was actually received for this build, how it's wired, and the tools used.
(See [BOM.md](BOM.md) for the generic parts list and [WIRING.md](WIRING.md) for the
generic pinout reference.)

## Board
- **Raspberry Pi Zero W v1.1** — ARMv6, 512 MB RAM, 2.4 GHz WiFi. Hostname `airmon`.
  The 40-pin GPIO header shipped **bare** (no pins) — a 2×20 male header is soldered on.

## Sensors (received)
| Sensor | Measures | Bus / addr | Driver |
|---|---|---|---|
| Sensirion **SCD41** (photoacoustic) | CO₂ + temp + humidity | I²C `0x62` | `scd41` |
| Bosch **BME680** | VOC/gas + pressure (+temp/hum) | I²C `0x76`/`0x77` | `bme680` |
| Plantower **PMS5003** | PM1.0 / PM2.5 / PM10 | UART `/dev/serial0` | `pms5003` |

All three breakouts shipped with **loose header pins** that get soldered on.

## Display
- **5″ IPS LCD, 1024×600, capacitive touch** — connects via **HDMI** (video) + **USB-C
  "TouchPower"** (power + touch). Needs its **own 5 V USB supply** (use the included
  USB-A→USB-C cable into a phone charger). The Pi's mini-HDMI → display HDMI via adapter.
- **Approach:** the Pi runs a **full-screen browser (kiosk)** showing the dashboard at
  `http://localhost:8000`. We do **not** use the `st7789` SPI display path for this build.

## Not used / not part of this project
- **K-TAG ECU programmer** — unrelated automotive tool (wrong/extra item). Set aside.
- **Two "2 TB" microSD cards** — almost certainly **counterfeit** (fake capacity). Do NOT
  use for the Pi. The real 32 GB card stays in the Pi. (Test their true size with `f3` later.)
- **Qwiic/STEMMA QT "Pi SHIM"** — optional I²C-over-Qwiic adapter; not needed since our
  sensors use pin headers + the PMS5003 needs UART.

## Tools used
- Soldering iron + rosin-core solder (0.6–0.8 mm)
- Flush cutters, helping-hands clamp (recommended)
- Breadboard (reused from an Arduino kit) — for the shared I²C bus
- Female-to-male + male-to-male jumper wires
- Single-row male header strip (reused) — spare sensor pins

## Final purchase (ordered 2026-06-23)
- Break-Away 2×20 dual male header for Pi Zero GPIO (pack of 10)
- ELEGOO 120 pc Dupont jumper kit (M-F / M-M / F-F)
- Soldering iron + solder kit
- 5 V USB wall charger (for the display)

## Wiring map

Pin numbers are **physical** header pins on the Pi. The two I²C sensors share the same
four lines (that's what the breadboard is for).

### I²C — SCD41 + BME680
| Sensor | → Pi physical pin |
|---|---|
| VIN | 5V (pin 2) |
| GND | GND (pin 6) |
| SDA | GPIO2 / SDA (pin 3) |
| SCL | GPIO3 / SCL (pin 5) |

⚠️ Set each board's **I²C-logic voltage-select jumper to 3.3 V** so the SDA/SCL lines
can't over-volt the Pi's 3.3 V GPIO.

### UART — PMS5003
| PMS5003 | → Pi physical pin |
|---|---|
| VCC | 5V (pin 4) |
| GND | GND (pin 9) |
| TX | RXD / GPIO15 (pin 10) |
| RX | TXD / GPIO14 (pin 8) |

## Soldering order
1. Solder the **2×20 male header** onto the Pi (flush, all 40 pins).
2. Solder a **pin strip** onto each sensor breakout (SCD41, BME680, PMS5003 adapter).
3. Trim excess pin length with flush cutters.
4. Mount sensors + Pi jumpers on the **breadboard**; wire per the map above.

## Bring-up (software)
1. `sudo raspi-config nonint do_i2c 0` and enable UART (`do_serial_hw 0`, `do_serial_cons 1`), reboot.
2. `pip install -e ".[pi]"` (or just the SCD4x/BME680/PMS5003 libs).
3. `i2cdetect -y 1` → expect `0x62` (SCD41) and `0x76`/`0x77` (BME680).
4. Edit `config.yaml` → `sensors: [scd41, bme680, pms5003]`.
5. `./scripts/deploy.sh airmon@10.0.0.94` (or restart the services) → real data on the dashboard.
