# Wiring & Pi setup

Pin numbers below are **BCM** (the GPIO numbers), with the physical header pin in
parentheses. The Pi Zero W has the standard 40-pin header layout.

## Power

- 3.3 V (pin 1) → SCD41 VIN, BME680 VIN, ST7789 VCC
- 5 V (pin 2 or 4) → PMS5003 VCC (the fan/laser needs 5 V)
- GND (pins 6, 9, 14, …) → every sensor's GND

## I²C — SCD41 + BME680 (share the same two pins)

| Signal | BCM | Header pin |
|---|---|---|
| SDA | GPIO2 | 3 |
| SCL | GPIO3 | 5 |

Enable and verify:

```bash
sudo raspi-config nonint do_i2c 0
sudo reboot
i2cdetect -y 1        # expect 0x62 (SCD41) and 0x76 or 0x77 (BME680)
```

## SPI — ST7789 TFT

| Signal | BCM | Header pin |
|---|---|---|
| MOSI (SDA/DIN) | GPIO10 | 19 |
| SCLK (CLK)     | GPIO11 | 23 |
| CS             | GPIO8 (CE0) | 24 |
| DC             | GPIO9  | 21 |
| BL (backlight) | GPIO18 | 12 |
| RST            | (often tied to 3.3 V, or a spare GPIO) | — |

```bash
sudo raspi-config nonint do_spi 0
```

> The exact pins must match `_open_tft()` in `src/aqm/display/__main__.py`.
> Adjust whichever is easier to change.

## UART — PMS5003 (particulates)

| Signal | BCM | Header pin |
|---|---|---|
| Pi TXD → PMS RX | GPIO14 | 8 |
| Pi RXD ← PMS TX | GPIO15 | 10 |
| ENABLE (SET)    | GPIO22 | 15 |
| RESET           | GPIO27 | 13 |

Free the UART from the Linux serial console, then enable the hardware UART:

```bash
sudo raspi-config nonint do_serial_cons 1   # disable the login shell on serial
sudo raspi-config nonint do_serial_hw 0     # enable the UART hardware
sudo reboot
# device should be /dev/serial0
```

## Heat & airflow (this affects readings!)

- Keep the SCD41/BME680 **away from the Pi's warm side** — CPU heat inflates the
  temperature and deflates the humidity reading. A short ribbon cable to a cool
  vented corner is ideal.
- The **PMS5003 needs a clear intake and exhaust** — never seal it in a box.
- Vent the enclosure generously; stagnant air makes CO₂/gas readings lag.
