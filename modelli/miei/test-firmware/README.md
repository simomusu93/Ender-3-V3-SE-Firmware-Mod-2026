# Test prints for Simomusu93-FW

Generated with `strumenti/crea_test_firmware.py`. In Creality Print use:
- Printer: **Creality Ender-3 V3 SE 0.4 nozzle** (the stock one, not "Simomusu93", so the test only measures the firmware)
- Process: **0.20mm Standard** · Filament: **SUNLU PLA Basic Piccole** (or PLA+)
- Supports: no · Brim: no

Before flashing: note the **Z-offset** and take a photo of the **Info** menu.
Keep the original firmware ready on a second SD card. **Stay near the printer** during the tests.

## Test 1 – `test01_cubo_20mm.stl` (≈ 20 min): does the printer work?

After flashing `Simomusu93-FW_0.6.bin`:

| Check | OK if… |
|---|---|
| Info menu | shows `Simomusu93 0.6` |
| Auto leveling | finishes without errors; Z-offset as before (or redo it) |
| Heating | nozzle and bed reach their temperatures and stay stable |
| Print | regular cube, readable X/Y/Z letters, 20 mm (±0.2) |
| End of print | the printer goes back to the menu normally |

If any of these fails: **stop** and flash the original firmware again.

## Test 2 – `test02_tempo_m73.stl` (≈ 1 h): is the time right?

100 × 100 × 0.6 mm base (slow first layer, little data) + 50 mm tall hollow tower with a ring every 10 mm.
It is the same pattern that fooled the Creality estimate with the Kratos print.

1. Before printing, note the **time estimated by Creality Print**: T = ______ min
2. Photograph the screen at these moments and fill in:

| Elapsed | % on screen | Remaining time on screen | Expected (T − elapsed) |
|---|---|---|---|
| 5 min | | | |
| 15 min | | | |
| 30 min | | | |
| halfway up the tower (2nd ring, 20 mm) | | | |

OK if the remaining time stays within a few minutes of the expected one and the % rises steadily.
With the original firmware, during the first minutes the remaining time would be much higher (estimate from bytes read).

The rings on the tower (10, 20, 30, 40, 50 mm above the base) also check the "Strato X/Y" (current layer) line:
ring at 20 mm above the base = Z 20.6 mm ≈ layer 103 with 0.2 mm layers.
