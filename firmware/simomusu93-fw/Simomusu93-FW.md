# Simomusu93-FW – firmware for the Ender-3 V3 SE (C13 board, GD32F303)

Base: official Creality V1.0.6 source ([CrealityOfficial/Ender-3V3-SE](https://github.com/CrealityOfficial/Ender-3V3-SE), commit `e7b2bad`),
which builds to 227,436 bytes: only 8 bytes away from the official 1.1.0 firmware → practically the same code that runs on the printers today.
Every change in the code is marked with the comment `Simomusu93-FW`.
UI ideas from [navaismo/Ender-3V3-SE](https://github.com/navaismo/Ender-3V3-SE) – thanks! – with the code rewritten and the bugs found fixed.

Rules: one version = few changes = one test. **No changes to thermal protections.** Strict linking always on.

## Building
```
set PLATFORMIO_BUILD_DIR=C:\Users\<user>\.pio-build\simomusu93
pio run -d <this folder> -e STM32F103RET6_creality
```
The `.bin` ends up in `%PLATFORMIO_BUILD_DIR%\STM32F103RET6_creality\firmware.bin`; versions to test are copied to `../build/`.
Before flashing, run the test bench (`strumenti/banco_prova/banco_prova.ps1`). How to flash: [`../UPDATE-GUIDE.md`](../UPDATE-GUIDE.md).

The printer's menus are in Italian; the new labels are translated in brackets below.

## Versions

### 0.9 – `build/Simomusu93-FW_0.9.bin` (232,900 bytes, SHA256 D1A87396…F2B650E6) – TO TEST
- **G-code preview on the file confirm screen**, instead of Creality's fixed "robot" image. The V3 SE screen cannot decode the
  PNG/JPG thumbnails that Creality Print embeds (Creality's own code says so and always shows the robot), so:
  - `strumenti/anteprima_gcode.py` (slicer post-processing script, or drag a G-code onto `anteprima_gcode.bat`) converts the 96×96 PNG
    into a `; E3V3SE_THUMB_RAW16_BEGIN 96x96` block (RGB565 hex, 32 colours, transparent background = not drawn) right after the header;
  - `feature/simomusu93/simomusu93_thumb.cpp` draws it at the robot's position (72, 25) with filled rectangles: per-row runs merged
    vertically, grouped by colour, a 16 ms pause every 10 commands (the panel locks up if flooded), watchdog fed while drawing.
  Format and algorithm from navaismo's 2.1 port (`ThumbRender.cpp`, GPL-3.0), rewritten for Marlin 2.0.8; 1024 runs = 6 KB RAM
  (navaismo: 1536 = 9 KB); bigger images just flush early. New `DWIN_Fill_Rect_Raw()`.
  It also reads the **BTT_TFT** thumbnail that Creality Print/OrcaSlicer write by themselves (printer setting
  `96x96/BTT_TFT`: a `;00600060` size line + one `;<RGB565 hex>` line per row): **no script needed**. The first 300 lines are searched.
  No preview block → the robot as before. Title shows "Anteprima..." while drawing (~1.5 s for the test cube, ~3.4 s for Kratos).
- RAM: 29.1 KB static (+6.5 KB) → 34.9 KB left for stack and heap. Settings unchanged.
- Test bench level 4: the firmware's preview code compiled for the PC draws on a fake 240×320 screen: cube and Kratos pixel-exact in both formats
  (script and BTT_TFT generated like OrcaSlicer's `Thumbnails.cpp`; 0 different pixels; Kratos also exercises the early flush), no overdraw, nothing outside the 96×96 area. 25/25 checks.

### 0.8 – (231,660 bytes, SHA256 7A29B706…B5F944F4, not kept in the repository) – FLASHED on 2026-10-14
- **Linear advance turned off again**, as in the stock Creality firmware. Test on 2026-10-14, same 20 mm cube, same firmware (0.6):
  with `M900 K0.05` (written by Creality Print from the filament profile) the first layer was badly under-extruded on the 80 mm/s infill;
  with `M900 K0` the cube printed perfectly. In this Creality Marlin 2.0.8 fork linear advance does not work well together with
  Creality's input shaping / S-curve. Without `LIN_ADVANCE`, `M900` is an unknown command and is ignored, so the profiles can stay as they are.
- The EEPROM layout doesn't change (Marlin keeps the K slot even with LIN_ADVANCE off): settings are kept.
- Test bench: the M900 presence check became "M900 absent". 24/24 checks.

### 0.7 (233,540 bytes, SHA256 F01614AB…C47362E16, not kept in the repository)
0.6 on the printer (2026-10-14): "Strato 0/166" OK, but a new print started showing 12% and 00:30 left from the previous (aborted) print.
- Cause 1: Creality only redrew the % when it was > 0, so a reset to 0 never reached the screen.
- Cause 2: the print screen is drawn right after `openAndPrintFile()`, which only *queues* M23/M24: the file is opened later,
  so the screen still had the old values (and stayed like that during the pre-print calibration).
- Fix: `simomusu93_new_print_reset()` (%, M73 remaining time, layer info, screen variables) before the print screen is drawn,
  and the % is redrawn on every change, 0 included.
- Same session, open issue: the 20 mm cube came out under-extruded on the 80 mm/s first-layer infill while the slow purge line was fine.
  Suspect: linear advance (stock Creality has it off; the G-code sets `M900 K0.05`). Confirmed by the `M900 K0` test → linear advance off in 0.8.
Test bench: 24/24 checks.

### 0.6 (233,500 bytes, SHA256 51AFFD77…B781F0D04, not kept in the repository)
First real print (20 mm cube, 2026-10-14): the print screen showed "Z 0.44 mm" instead of "Strato X/Y".
- Cause: the reset of layer/total/time calibration was in `startOrResumeJob()`. With `PRINTJOB_TIMER_AUTOSTART`, the `M190`/`M109`
  of the start G-code also go through it, **after** the header with the total layer count has been read → total wiped.
  The PC simulator didn't catch it because it only runs the G-code parser, not the heating commands.
- Fix: the reset is now in `M23` (file open, before anything is read), and `startOrResumeJob()` is back to the Creality code
  (a mid-print `M109` no longer drops the % to 0 either).
- Same session: the nozzle showed target "0" while printing (165/0 → no extrusion below `EXTRUDE_MINTEMP` 180 °C).
  Not caused by these changes (temperatures are untouched); under investigation with the G-code file.
- Build: `simomusu93_no_local_paths.py` replaces the build PC's user name in the framework's `__FILE__` strings with "x"
  (same length, nothing moves; this GCC has no `-fmacro-prefix-map`).
Test bench: 24/24 checks.

### 0.5 (not kept in the repository) (233,508 bytes, SHA256 C7249A23…D43EE6BD)
0.4 flashed on 2026-10-14: no more duplicated entries, but scrolling back up the Control menu left "Motion" text overlapping
"Salva configurazione" on the Motion row (photo 2026-10-14).
- Cause: Creality's `case MROWS + 2` (Motion row at the top) was dead code with the stock 7-entry menu; with the longer menu it now runs,
  and it wrote the "Motion" font label over a row that was not cleared. Now it erases the row and draws the language image
  (`LANGUAGE_Motion`) like `Draw_Control_Menu()`. The Temperature row is also erased before redrawing.
- Settings unchanged (EEPROM "S03").
Test bench: 24/24 checks.

### 0.4 (not kept in the repository) (233,484 bytes, SHA256 1DF20803…505A8D5C) – FLASHED on 2026-10-14
0.3 tested on the printer on 2026-10-14: boot and Info menu OK, but the "RAM 35.x K" text to the right of "H/W VER" was cut off.
- **Info menu**: removed the "Contact us / www.creality.com" entry; in its place "RAM libera min" (min free RAM) with the value in KB (yellow, 8×16 font).
- **Control menu, scrolling back up**: Save / Load / Leveling data were not redrawn at the top (bug introduced in 0.3
  by the 3 entries added at the bottom: Creality only handled Back/Temperature/Motion). Added the 3 cases in `HMI_Control()`.
- EEPROM settings unchanged (version "S03"): they are **not** reset when going from 0.3 to 0.4.
Test bench: 24/24 checks.

### 0.3 (not kept in the repository) (233,436 bytes, SHA256 3E5E2AE6…BB10C0C7) – FLASHED on 2026-10-14
Printer checked on 2026-10-14 (Info photo): board **CR4NS200320C13**, previous firmware **Creality V1.0.7**.
Everything in 0.2, plus (UI taken from navaismo's screens, code rewritten and fixed):
- **Controllo > Statistiche** (statistics): total / finished / aborted prints, total time, longest print, filament (PRINTCOUNTER data
  Creality was already saving). No Arduino `String` (navaismo allocated on the heap every time the screen opened) and fixed coordinates.
- **Controllo > Suono: Si/No** (sound on/off): mutes beeps and knob clicks (`Encoder_tick`), saved in EEPROM. Note: it also mutes
  warning beeps (e.g. filament runout).
- **Controllo > Sensore filo: Si/No** (filament sensor on/off): disables the runout check during prints, saved in EEPROM.
- **Settings reset with confirmation**: first click → "Clic ancora: RESET" (click again), second click within 5 s; turning the knob cancels.
  (Previously a single click immediately wiped Z-offset, leveling and PID and rebooted.)
- EEPROM version "S03" (settings reset at first boot, as for 0.2).
- Not needed: file info before printing (time, filament, layer height) was already shown by the Creality firmware.
- Postponed: 6×6/7×7 mesh (Creality's probing with the pressure sensor, mesh screen, virtual mesh RAM 1→~3 KB).
Test bench: 24/24 checks.

0.3 test: as for 0.2, plus Control > scroll to the bottom: Statistiche (open and go back), Suono (Si↔No and check that the knob is silent),
Sensore filo (Si↔No), Reset (one click → yellow text, turn the knob → back to "Reset"; do NOT click a second time).

### 0.2 (231,876 bytes, not kept)
- **Self-calibrated remaining time**: M73 R × (real print time ÷ time predicted by the slicer so far), after 10 min,
  clamped between ×0.4 and ×3. Adapts to the speed knob (Simomusu93 prints at 160%), real accelerations, etc.
  The initial heat-up is excluded (first `dwin_heat_time` of the print). Function `Simomusu93GcodeInfo::remaining_s()`.
- **Current layer** on the print screen: "Strato 152/1078" (layer) line below the remaining time (x 117, y 174, 6×12 font).
  If the total is unknown (resume after power loss, G-code without header) it shows "Z 12.40 mm".
  Module `feature/simomusu93/simomusu93_gcode_info.*` (no Marlin dependencies, tested on the PC by the test bench),
  hooked into `gcode/queue.cpp` (SD reading), reset in `startOrResumeJob()`.
  Position checked on a photo of the real screen (2026-10-13): ~20 px free band between "remaining time" (up to y≈170) and the buttons (from y≈190).
- **Correct % also when entering the print screen** (previously it restarted from the bytes read).
- **Minimum free RAM** in the Info menu: stack painting at boot + check (`feature/simomusu93/simomusu93_ram.*`).
- **Linear advance** enabled with K=0 in the firmware (**turned off again in 0.8**, see above). **Note**: the filament profiles inheriting from "Soleyin Ultra PLA"
  (Simomusu93, SUNLU PLA Basic/PLA+ Piccole/Grandi) make Creality Print write `M900 K0.05` at the start of the G-code
  → with this firmware linear advance **is active at 0.05** in those prints (the Creality firmware ignored the command).
  Simomusu93's choice (2026-10-13): keep it. Fine tuning: Creality Print "Pressure advance" test, then the value in the profiles.
  Same configuration as navaismo (LIN_ADVANCE with K=0, value from the slicer).
- **Skew correction** enabled with factor 0 (`M852 S…` + `M500` after measuring).
- Build-time check that the settings fit in the 2 KB EEPROM.
- Built with `-fstack-usage` (per-function stack, read by the test bench).
- **EEPROM version "S02"**: at first boot settings go back to factory values → **redo Z-offset and leveling**.
  (Language and Creality data at fixed addresses 0x01-0x06 and 90 are not touched.)
Test bench: 19/19 firmware checks; Kratos G-code (1078 layers) and Kratos FINAL (1074): exact layer count.

### 0.1 (227,708 bytes, SHA256 8E87AF2D…484500, not kept)
- **Remaining time and % from the slicer (M73)**: the screen uses the `M73 P.. R..` commands written by Creality Print.
  Before, the firmware estimated from the bytes read from the SD (Kratos: 60 h shown instead of 14 h).
  If the G-code has no M73, the old Creality estimate is kept.
  Files: `Configuration_adv.h`, `inc/SanityCheck.h`, `lcd/marlinui.h`, `lcd/dwin/e3v2/dwin.cpp`, `MarlinCore.cpp`
  (% reset at every new print).
  Done **without** enabling `HAS_DISPLAY` (navaismo's mistake: with HAS_DISPLAY a thermal error calls
  `MarlinUI::kill_screen()`, which doesn't exist for DWIN → crash instead of the error message).
- **Strict linking**: `buildroot/share/PlatformIO/scripts/simomusu93_strict_link.py` removes the framework's `--warn-unresolved-symbols`:
  a missing function now stops the build instead of producing a firmware that jumps to address 0.
  (It already caught one mistake while developing this version.)
- Version shown in the Info menu: `Simomusu93 0.1`.
PC checks: build without warnings, vector table identical to the official one (stack 0x2000FFD8, reset 0x080073A1, load address 0x08007000).

## Roadmap – proposed 2026-10-13

| Ver. | Feature | Why | Flash | Risk |
|---|---|---|---|---|
| 0.1 | Time and % from M73 | correct estimate (**done**) | +0.3 KB | low |
| 0.2 | Stack meter in the Info menu | **done** | <1 KB | low |
| 0.2 | Current layer while printing | **done** | <1 KB | low |
| 0.2 | Linear advance (M900, saved in EEPROM) | enabled in 0.2, **turned off in 0.8**: under-extrusion with Creality's input shaping; would need the Marlin 2.1 port | 2-4 KB | high |
| 0.2 | Skew correction (M852) | **enabled with factor 0**, measurement still to do | ~1 KB | low |
| 0.3 | Statistics (prints, hours, meters) | **done** | 1-2 KB | low |
| 0.3 | Sound on/off | **done** | <0.5 KB | low |
| next | Tuned input shaping (M593 already present, X 42 Hz / Y 40 Hz) + saving | fewer "ripples" on surfaces | ~0 | low |
| next | 7×7 leveling mesh | uniform first layer on large parts | <1 KB | medium (2 KB EEPROM) |
| next | Filament used / estimated weight on screen (from the G-code header) | know if the spool is enough | ~1 KB | low |
| next | Reworked M600 filament change (parking, slow purge) | two-colour prints without clogs | ~1 KB | medium |
| — | Filament runout sensor | **already supported by the Creality firmware** (pin PC15, `HAS_CHECKFILAMENT` in `pins_CREALITY_V3_GD303.h`; low pin = filament present; 7 consecutive high readings every 500 ms ≈ 3.5 s → pause and dialog on screen; SD printing only). On/off switch added in 0.3. | 0 | — |
| later | G-code thumbnail preview on screen | convenience | 5-10 KB + RAM | high |
| later | Port to Marlin 2.1 (FT_Motion, MPC) | modern motion system | a project of its own | high |
