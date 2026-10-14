# Ender-3 V3 SE firmware analysis (2026-10-13)

Tools: `strumenti/analizza_firmware.py` + reading navaismo's 1.1.0 source code.
The official and navaismo files analysed here are not included in this repository (third-party material).

## What a .bin file looks like

| | Creality 1.1.0 C13 | navaismo 1.1.0 (C13) | Creality 1.1.0 C14 |
|---|---|---|---|
| Size | 227,444 bytes | 240,268 bytes | 202,752 bytes |
| Encrypted | no | no | no |
| Chip | GigaDevice GD32F303 (built as STM32F103) | same | STM32F401 |
| Load address | 0x08007000 | 0x08007000 (confirmed by `platformio.ini`) | probably higher (reset vector at 0x08011D85) |
| Creality bootloader | 28 KB at the start of flash | same | not verified |
| RAM | 64 KB | 64 KB | 96 KB |
| Build date | 22 Apr 2025 | 24 Nov 2025 | 22 Apr 2025 |
| Base | Marlin 2.0.8.3 modified by Creality ("2.0.8.3T") | same + navaismo's changes | same |

- The file is the "bare" program: the ARM vector table (initial stack + reset address), then code and data.
- At power-on the **bootloader** (28 KB, never overwritten) looks for a `.bin` with a new name on the SD card and copies it to flash at 0x08007000.
  That's why a bad firmware can usually be recovered by flashing the original one.
- Total flash 512 KB − 28 KB bootloader = 484 KB available; navaismo uses 240 KB. The real limit is **RAM** (64 KB).

## Source tree (navaismo 1.1.0, `Marlin/src`)

| Folder | Contents |
|---|---|
| `module/` | motion, planner, temperatures, steppers |
| `gcode/` | one file per G/M command (e.g. `gcode/lcd/M117.cpp`, `M73.cpp`) |
| `feature/` | optional features: linear advance, input shaping, leveling, runout |
| `lcd/dwin/e3v2/` | **the V3 SE screen** – `dwin.cpp` (10,188 lines) draws every screen |
| `HAL/STM32F1/` | chip abstraction layer |
| `sd/` | SD card access |

Configuration: `Marlin/Configuration.h` and `Configuration_adv.h`.

## Official vs navaismo (from the strings in the binary)

- Both: input shaping (`M593`), bilinear leveling, thermal protections (thermal runaway, MINTEMP, MAXTEMP).
- navaismo only: linear advance (`Advance K=`, M900), skew correction (M852), improved M600,
  statistics, buzzer, filament sensor, Orca/Creality Print file info, screen brightness (M255/M256).

## Known bugs in navaismo 1.1.0 (GitHub issues, no published fix at the time)

| Issue | Problem | First guess at the cause |
|---|---|---|
| #208 | M600: extruder runs very fast, clogs | **Confirmed by the diff:** Creality 1.0.6 has `FILAMENT_UNLOAD_PURGE_LENGTH 8`, navaismo raised it to `50` mm (at 25 mm/s ≈ 60 mm³/s, 4–5× what the hotend can melt). |
| #199, #204 | 1.1.0: diagonal moves on the first layer, slow/noisy printing, defects above a certain height | to investigate (input shaping / linear advance / planner) |
| #86, #214 | remaining time inaccurate or stuck | M73 logic in `dwin.cpp` |
| #160 | "print finished" dialog too early, % going down after 100% | progress logic in `dwin.cpp` |
| #190, #209 | random freezes/reboots, suspected memory waste | RAM (64 KB): stack and heap need measuring |
| #163, #212 | sometimes freezes at print start | start / leveling sequence |
| #168 | SD inserted while the printer is on: files not visible | SD detection |
| #41 | a different file starts than the one selected | 8.3 file names |

## Creality 1.0.6 source ↔ navaismo 1.1.0

Official source: GitHub CrealityOfficial/Ender-3V3-SE, commit `e7b2bad` (2024-07-10), zip SHA256 `959CF33B…DCCAE6`.
It is the only Creality source ever published: no 1.1.0, no C14. Diff script: `strumenti/confronta_sorgenti.py`.

- 42 files modified, 3 added (M255, M256 brightness). Most of it is the screen: `dwin.cpp` (+8207 −5853 lines),
  `lcd_rts.cpp`, `gcode.cpp` (many lines are just reformatting).
- Key configuration changes made by navaismo:
  - `LIN_ADVANCE` enabled (Creality had it off), K from 0.2 to 0.0
  - `USE_M73_REMAINING_TIME` extended to the DWIN screen → **explains the 60 hours**: the Creality firmware ignores the M73 time in the G-code
  - `FILAMENT_UNLOAD_PURGE_LENGTH` from 8 to 50 mm → bug #208
- Input shaping (`INPUT_SHAPING_X/Y`) is already in the Creality 1.0.6 source.

## Official 1.1.0 (C13) vs Creality 1.0.6 source (2026-10-14)

The 1.0.6 source built unmodified is **8 bytes** smaller than the official 1.1.0 C13 file. All printable strings
(menus, messages, commands, source file names) are identical except the version ("V1.1.0" vs "V1.0.6"), the build date and the
build machine's user folder in 9 embedded paths (one character longer at Creality, which accounts for the size difference).
→ For the C13 board, 1.1.0 is essentially 1.0.6 rebuilt with a new version number. Creality's release notes are empty.

## Useful findings

1. **Current layer:** in this firmware `M117` does not show up on the print screen
   (the M117 popup is only active with `HOST2_ACTION_COMMANDS`, which is disabled) → a change in `dwin.cpp` is needed
   (`Draw_Print_*` functions). Done in Simomusu93-FW 0.2.
2. **Remaining time:** with `LCD_SET_PROGRESS_MANUALLY` + `USE_M73_REMAINING_TIME` the screen can use the time computed by
   Creality Print (M73 commands in the G-code) instead of the "bytes read" estimate. Done in Simomusu93-FW 0.1,
   without `HAS_DISPLAY` (see `simomusu93-fw/Simomusu93-FW.md`).
