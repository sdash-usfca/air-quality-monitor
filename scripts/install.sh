#!/usr/bin/env bash
# Set up the project on a Raspberry Pi. Run from the repo root.
set -euo pipefail

echo "==> Creating virtualenv (.venv)"
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip

echo "==> Installing aqm with the Pi sensor + display libraries"
./.venv/bin/pip install -e ".[pi]"

echo
echo "Done. Next steps (manual — they need sudo / a reboot):"
echo "  1. Enable buses:"
echo "       sudo raspi-config nonint do_i2c 0"
echo "       sudo raspi-config nonint do_spi 0"
echo "       sudo raspi-config nonint do_serial_cons 1   # free the UART (PMS5003)"
echo "       sudo raspi-config nonint do_serial_hw 0"
echo "       sudo reboot"
echo "  2. Verify sensors:   i2cdetect -y 1   # expect 0x62 (SCD41), 0x76/0x77 (BME680)"
echo "  3. Configure:        cp config.example.yaml config.yaml"
echo "                       # set sensors: [scd41, bme680, pms5003] and display.enabled: true"
echo "  4. Install services: sudo cp systemd/*.service /etc/systemd/system/"
echo "                       # edit User/paths in those files if you are not user 'pi'"
echo "                       sudo systemctl daemon-reload"
echo "                       sudo systemctl enable --now aqm-collector aqm-web aqm-display"
echo "  5. Open the dashboard at  http://<pi-ip>:8000"
