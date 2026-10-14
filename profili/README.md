# Final profiles – Ender-3 V3 SE + Creality Print 7.3

Installed in Creality Print on 2026-10-13. Each profile inherits from an official Creality preset and changes only the values listed.
To use them, import the `.json` files in `stampante/`, `filamenti/`, `processo/` with Creality Print's preset import.
("Piccole" = small prints, "Grandi" = large prints.)

## Which one to use

| What you print | Process | Filament |
|---|---|---|
| Miniatures, figures < 10 cm, objects with fine details | Simomusu93 Piccole 0.12mm | SUNLU PLA Basic Piccole / SUNLU PLA+ Piccole |
| Statues, busts, large or tall parts | Simomusu93 Grandi 0.16mm | SUNLU PLA Basic Grandi / SUNLU PLA+ Grandi |
| Technical/quick parts with no aesthetic needs | Simomusu93 (old) or 0.20mm Standard | Simomusu93 |

## SUNLU temperatures

| Profile | Nozzle (first layer) | Bed (first layer) | Official SUNLU range |
|---|---|---|---|
| PLA Basic Piccole | 205 °C (210) | 60 °C (60) | nozzle 190–220 °C, bed 50–65 °C |
| PLA Basic Grandi | 210 °C (215) | 60 °C (65) | |
| PLA+ Piccole | 210 °C (215) | 60 °C (60) | nozzle 205–215 °C (PLA+ 2.0, 50–100 mm/s), up to 235 °C for the older PLA+ |
| PLA+ Grandi | 215 °C (220) | 60 °C (65) | |

The "Grandi" profiles are 5 °C hotter because they print faster (more material per second to melt).
PLA+ is about 5 °C hotter than Basic. If you see stringing, lower by 5 °C; if layers split, raise by 5 °C.

## Why these values

**Speeds and accelerations.** The V3 SE is rated for 250 mm/s and 2500 mm/s², but above ~120 mm/s on outer walls the surface gets worse
and the moving bed (bed slinger) makes tall parts wobble. Hence: outer walls 40 (small) / 70 (large) mm/s, accelerations 800–2000.

**Max flow 12 mm³/s.** The V3 SE hotend typically handles 8–15 mm³/s with normal PLA; 12 is a safe limit that avoids under-extrusion.
With "Hyper"/high-speed PLA you can raise it after the volumetric flow test.

**Retraction 0.8 mm @ 40 mm/s, deretraction 35 mm/s, z-hop 0.2 mm.** Recommended values for the V3 SE direct drive;
the slower deretraction avoids under-extrusion at the start of lines.

**Pressure advance: off** (`enable_pressure_advance = 0` in the four SUNLU profiles, since 2026-10-14). The Soleyin Ultra PLA parent
turns it on with K 0.05, which made Creality Print write `M900 K0.05`: the stock firmware and Simomusu93-FW 0.8+ ignore it, but
Simomusu93-FW 0.2–0.7 (and firmware with linear advance, e.g. Marlin 2.1 builds) under-extruded the first layer with it.

**Printer profile "Ender-3 V3 SE Simomusu93".** G-code thumbnails `96x96/BTT_TFT, 300x300/CR_PNG`: the 96×96 one is written as
RGB565 pixels that Simomusu93-FW 0.9+ draws on the file confirm screen (instead of Creality's robot); the 300×300 PNG stays for
Creality Print. Use this printer profile (not the stock one) to get the preview. The old `M117 Strato …` layer-change G-code was
removed: the V3 SE screen never showed M117, and Simomusu93-FW shows the layer by itself.

**Piccole (small).** 0.12 mm layers, 3 walls (small details are almost all walls), 10 s minimum layer time
(each layer must cool before the next, or the tips melt), organic supports with 0.5 mm tip
and 0.15 mm distance so they come off without ruining the surface, scarf seam to hide the seam on curves.

**Grandi (large).** 0.16 mm layers (good quality/time trade-off for statues), 12% gyroid (light but stable),
6 mm brim + bed at 65 °C on the first layer + fan off for the first 3 layers against warping,
3 mm support branches so tall supports don't wobble, seam at the back of the model.

## After the first print

Every spool is different: for truly final results run the tests in `../calibrazione/` (temperature and flow first)
and update `nozzle_temperature` and `filament_flow_ratio` in the filament profiles.

## Sources

- Orca Slicer settings for Ender 3 V3 SE – harktech.co.uk
- Community Orca profile for E3V3SE – github.com/galadriann/e3v3se-orca-profile
- Creality forum: V3 SE pressure advance, V3 KE warping, max flow
- OrcaSlicer wiki: supports and seam/scarf joint
- Corb3d: supports for PLA miniatures
- SUNLU store (PLA+ / PLA+ 2.0 range), SUNLU filament guide 2025, 3dprintbeast.com (SUNLU PLA vs PLA+), fixmyprint3d.com (SUNLU PLA)
