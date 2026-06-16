#!/usr/bin/env bash
# Run this ON the Raspberry Pi to print a one-shot health report.
# Read-only: it changes nothing. Copy it over and run:  bash pi-healthcheck.sh
set -u

line() { printf '%s\n' "------------------------------------------------------------"; }
have() { command -v "$1" >/dev/null 2>&1; }

line; echo "RASPBERRY PI HEALTH CHECK  ($(date))"; line

echo "MODEL / OS"
[ -e /sys/firmware/devicetree/base/model ] && echo "  model : $(tr -d '\0' < /sys/firmware/devicetree/base/model)"
echo "  arch  : $(uname -m)        (expect armv6l on a Zero W)"
have lsb_release && echo "  os    : $(lsb_release -ds)"
echo "  kernel: $(uname -r)"
echo "  python: $(python3 --version 2>&1)"

line; echo "MEMORY"
free -h | sed 's/^/  /'

line; echo "STORAGE (SD card)"
df -h / | sed 's/^/  /'

line; echo "POWER / THERMAL"
if have vcgencmd; then
  echo "  temp     : $(vcgencmd measure_temp | cut -d= -f2)"
  t=$(vcgencmd get_throttled | cut -d= -f2)
  echo "  throttled: $t   (0x0 = healthy)"
  if [ "$t" != "0x0" ]; then
    v=$((t))
    (( v & 0x1 ))    && echo "    !! under-voltage RIGHT NOW (weak PSU/cable)"
    (( v & 0x4 ))    && echo "    !! currently throttled"
    (( v & 0x10000 ))&& echo "    .. under-voltage has occurred since boot"
    (( v & 0x40000 ))&& echo "    .. throttling has occurred since boot"
  fi
else
  echo "  vcgencmd not found (not a Pi, or PATH issue)"
fi

line; echo "UPTIME / LOAD"
uptime | sed 's/^/  /'

line; echo "NETWORK (WiFi)"
have iwgetid && echo "  ssid : $(iwgetid -r 2>/dev/null)"
ip -4 addr show 2>/dev/null | awk '/inet /{print "  ip   : "$2}' | grep -v 127.0.0.1
if ping -c2 -W2 raspberrypi.org >/dev/null 2>&1; then echo "  internet: OK"; else echo "  internet: NO"; fi

line; echo "INTERFACES (for our sensors/display)"
for i in i2c spi serial; do
  if raspi-config nonint get_${i/serial/serial_hw} >/dev/null 2>&1; then
    case $i in
      i2c)    s=$(raspi-config nonint get_i2c 2>/dev/null);;
      spi)    s=$(raspi-config nonint get_spi 2>/dev/null);;
      serial) s=$(raspi-config nonint get_serial_hw 2>/dev/null);;
    esac
    [ "$s" = "0" ] && echo "  $i : enabled" || echo "  $i : disabled  (enable later for sensors)"
  fi
done
have i2cdetect && { echo "  i2cdetect bus 1:"; i2cdetect -y 1 2>/dev/null | sed 's/^/    /'; } \
              || echo "  i2cdetect: not installed (sudo apt install -y i2c-tools)"

line; echo "DONE"; line
