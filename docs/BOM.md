# Bill of Materials

Rough prices in USD; Adafruit/Pimoroni breakouts cost more but ship with
rock-solid libraries and wiring guides. Generic breakouts are cheaper.

| Part | Role | Bus / pins | Rough $ | Notes |
|---|---|---|---|---|
| Raspberry Pi Zero W | brains + WiFi | — | (have it) | ARMv6, 512 MB RAM |
| Sensirion **SCD41** | true CO₂ + temp + humidity | I²C @ `0x62` | $20–25 | NDIR; the headline sensor |
| Bosch **BME680** | VOC/gas + pressure | I²C @ `0x76`/`0x77` | $10–20 | temp/hum optional (off by default) |
| Plantower **PMS5003** | PM1.0 / PM2.5 / PM10 | UART `/dev/serial0` | $15–25 | needs airflow; 5 V power |
| **ST7789** 1.9–2.4" IPS TFT | the wall display | SPI | $10–15 | 240×240 default |
| microSD card 32 GB A1 | OS + database | — | $8 | |
| Dupont jumpers + GPIO header | wiring | — | $8 | |
| *(optional)* MICS-5524 | carbon monoxide (curiosity) | analog → MCP3008 ADC | $8 + $4 | **not** a safety device |

**Total: ~$70–110** depending on brand choices.

## Buying tips

- Buy the **SCD41** and **ST7789** from Adafruit or Pimoroni — their libraries
  and tutorials save hours. The BME680 is fine as a generic breakout.
- I²C address check: SCD41 (`0x62`) and BME680 (`0x76`/`0x77`) don't collide, so
  they share the same two I²C pins happily.
- The Pi has **no analog input** — any analog gas sensor (MQ-x, MICS) needs an
  ADC such as the MCP3008. The digital I²C/UART sensors above avoid this.
