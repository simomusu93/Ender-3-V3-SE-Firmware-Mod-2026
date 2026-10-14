# Simomusu93-FW test bench

Tests the firmware **on the PC, without the printer**. Single command (PowerShell):

```
.\banco_prova.ps1 -Gcode "C:\path\to\file.gcode"
```

| Level | Program | What it checks |
|---|---|---|
| 1 | `verifica_firmware.py` | the `.bin`: boot structure, version, that every feature is really inside, that the thermal protections are there, no missing functions, memory and stack function by function |
| 2 | `simula_gcode.exe` (from `simula_gcode.cpp`) | compiles **the same source file as the firmware** (`simomusu93_gcode_info.cpp`) and runs it on a real G-code, character by character like the printer: layers counted vs declared, M73 commands, comparison with the Creality estimate |
| 3 | `anteprima_schermo.py` | draws the print screen (original Creality on the left, Simomusu93-FW on the right) at a few moments of the print |

Results in `risultati/<G-code name>/` (CSV with the full history + images).

## What it can NOT check
- The real behaviour of motors, heaters, probe, SD card and screen: that still has to be tested on the printer.
- The exact look of the screen: the icons live in the display's memory; the preview shows positions and numbers, not the graphics.
- The RAM really used during a print: the firmware measures it itself (Info menu, "RAM libera min").

## Requirements
- Python + PlatformIO in a virtual environment (with `ziglang` to build the simulator and `pillow` for the images)
- Firmware built with `-fstack-usage` in `%USERPROFILE%\.pio-build\simomusu93\STM32F103RET6_creality`
