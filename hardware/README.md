# Hardware / enclosure

3D-printable enclosure files will live here (STL for printing + source CAD so
forkers can remix). Not designed yet — we lock the case **after** the exact
boards are in hand so the cutouts fit.

## Design constraints (learned the hard way by everyone who skips them)

1. **Thermal isolation.** The Pi's CPU heat skews temperature/humidity. Mount
   the SCD41/BME680 away from the Pi, ideally on a short cable in a vented bay,
   with the Pi's warm air venting *away* from the sensors.
2. **Airflow for the PMS5003.** It needs an unobstructed intake and a separate
   exhaust — design a through-path, not a sealed pocket.
3. **General venting.** Louvers/slots near the gas sensors; stagnant air makes
   CO₂ and VOC readings sluggish.
4. **Display cutout** sized to the ST7789 active area, plus a light-bezel.
5. **Wall mount.** Keyhole slots on the back; route the USB-power cable with
   strain relief.

## Planned files

- `enclosure.stl`, `front-bezel.stl`, `back-plate.stl`
- `enclosure.step` / source CAD
- `assembly.md` — print settings + assembly order
