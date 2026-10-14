# Plan: Simomusu93-FW on Marlin 2.1 (2026-10-14)

Today Simomusu93-FW is **Marlin 2.0.8 (2021) + Creality's changes + our changes**. "Moving to Marlin 2.1" means rebuilding it on
the current Marlin, which has a modern motion system (**FT_Motion**, where input shaping and linear advance work together),
better temperature control (MPC) and years of fixes.

## Starting point: navaismo's 2.1 port (no need to start from scratch)

Upstream Marlin only has the board pins (`pins_CREALITY_CR4NS.h`, [PR #27495](https://github.com/MarlinFirmware/Marlin/pull/27495),
`bugfix-2.1.x` only, no example configuration). The V3 SE screen is not supported upstream: it uses a different command set from the
Ender-3 V2 DWIN screens.

navaismo already did the hard part in [navaismo/Marlin_bugfix_2.1_E3V3SE](https://github.com/navaismo/Marlin_bugfix_2.1_E3V3SE)
(GPL-3.0, branch `c13_sd` for our board, actively maintained: last commit 2026-10-13, release "Belaya 6" for HW C13):
the V3 SE screen ported to 2.1, auto Z-offset routines, HX711 load cell, CRTouch helpers, FT_Motion input shaping (`M493`),
6×6 mesh, thumbnails, one-click print, statistics, layer number, M73 remaining time.

### Checked on our PC (2026-10-14, commit `60a9331`, version "v2.1.x Krasnaya 5")

| | Simomusu93-FW 0.8 (2.0.8) | navaismo 2.1 `c13_sd` |
|---|---|---|
| Builds with our PlatformIO | yes | **yes** (needs the build dir inside the project) |
| Flash | 231,660 bytes (47.9% of 484 KB) | 233,980 bytes (47.2%) |
| Static RAM | 23,320 bytes | **29,008 bytes** → ~6 KB less for stack/heap |
| Vector table | SP 0x2000FFD8, load 0x08007000 | same SP, reset inside the image → bootloader-compatible |
| Input shaping | Creality legacy, on (X 42 / Y 40 Hz) | FT_Motion, **off by default** (`ftMotionShaper_NONE`): must be set with `M493` |
| Linear advance | off (it under-extruded) | FT_Motion advance, K from `M900` (README: K0.10 coincided with under-extrusion → keep K=0 until tuned) |

### Open issues in navaismo's 2.1 (2026-10-14) – the real risk

| Issue | Problem | Weight for us |
|---|---|---|
| #23 | Extruder stops extruding mid-print | **high** (long statue prints) |
| #89 | Resume after pause / after power loss fails | **high** |
| #74 | "Tune" mid-print sometimes returns home and stops the print | medium |
| #72 | 6×6 mesh causes local stutter/artifacts | medium |
| #90 | Higher E-steps needed in 2.1.x | low (calibration) |
| #54, #53, #59, #44 | Z-offset after M600, one-click wrong file, multicolour UI glitches, fan noise | low |

## What we would add on top (our features not in navaismo 2.1)

| Feature | Effort |
|---|---|
| Self-calibrated remaining time (M73 R × real/slicer time) | small (module is independent of Marlin) |
| Minimum free RAM in Info (stack painting) – more important with 6 KB less RAM | small |
| Settings reset with confirmation, sound on/off, filament sensor on/off | small–medium (menus in navaismo's `dwin.cpp`) |
| Strict linking, user name stripped from the `.bin` | small |
| PC test bench adapted to 2.1 (symbols, M73/M900 checks, new screen layout) | medium |
| Fixes for the bugs above that we hit ourselves | **unknown** |

## Phases and estimate

| Phase | What | Claude's work | Your time at the printer | Calendar |
|---|---|---|---|---|
| 0 | Download, build, measure (**done today**) | — | — | — |
| 1 | Flash navaismo 2.1 **as is** and test: cube, M73 tower, one 3–5 h print, pause/resume, Tune menu | 1 h (guide, checks) | 2–3 h (mostly waiting) | 1–2 days |
| 2 | Decision: if #23/#89 show up on our printer → stop and stay on 0.8, or investigate the bug | — | — | — |
| 3 | Fork as "Simomusu93-FW 2.0" on `c13_sd`, port our features, adapt the test bench | 8–12 h (several sessions) | — | 3–5 days |
| 4 | Tuning: E-steps, input shaping frequencies with `M493`, linear advance K with a pressure-advance pattern | 1–2 h | 3–4 h (5–8 test prints) | 1 weekend |
| 5 | Real use before calling it stable: 3–5 normal prints, at least one > 10 h | fixes as needed | normal printing | 1–2 weeks |
| **Total** | | **~12–16 h** | **~8–12 h** | **~2–4 weeks** |

The rollback is the same as today: the Creality bootloader is never overwritten, the official 1.1.0 file always restores the printer.

## Recommendation

Do phase 1 first: it costs little and tells us whether the 2.1 base is reliable on *this* printer. Only if it passes,
build Simomusu93-FW 2.0 on it. Until then 0.8 stays the firmware for real prints.

Local copy (not in this repository): `%USERPROFILE%\.firmware-src\marlin21-navaismo` (369 MB, kept out of OneDrive).
Build: `pio run -d <that folder> -e STM32F103RET6_creality` → `.pio\build\STM32F103RET6_creality\firmware-<date>.bin`.
