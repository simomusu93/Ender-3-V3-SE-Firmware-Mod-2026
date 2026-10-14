# Calibration

Creality Print has built-in calibration tests (**Calibration** menu). Recommended order with a new spool:

| # | Test | What you find | Result |
|---|---|---|---|
| 1 | Temperature tower | Ideal nozzle temperature | |
| 2 | Flow rate | Extrusion multiplier | |
| 3 | Pressure advance | Skip: linear advance is off in both the stock firmware and Simomusu93-FW (it under-extruded) | — |
| 4 | Retraction | Less stringing between parts | |
| 5 | Max volumetric speed | How fast you can print | |

For each test save a subfolder here, `YYYY-MM-DD_material_test/`, with photos and the chosen value,
then update the filament profile in `../profili/filamenti/`.
