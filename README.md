# 3D printing – Creality Ender-3 V3 SE

Personal project by **Simomusu93** for 3D printing with a **Creality Ender-3 V3 SE** (mainboard **CR4NS200320C13**, GD32F303 chip)
and the **Creality Print 7.3** slicer: print profiles, cutting models that are too big for the bed, and an improved firmware, **Simomusu93-FW**.

## Acknowledgements

Special thanks to **navaismo** and their project [navaismo/Ender-3V3-SE](https://github.com/navaismo/Ender-3V3-SE):
their 1.1.0 firmware for the V3 SE was the starting point to understand how this printer's firmware is built,
what can be improved and where the limits are (memory, DWIN display). Their screens (statistics, sound, menus)
inspired the entries added to Simomusu93-FW; the code was rewritten from scratch on top of the official Creality source,
fixing the problems found during the analysis (see [`firmware/ANALYSIS.md`](firmware/ANALYSIS.md)).
Thanks also to [Marlin](https://github.com/MarlinFirmware/Marlin) and to
[CrealityOfficial/Ender-3V3-SE](https://github.com/CrealityOfficial/Ender-3V3-SE) for publishing the source code.

## Folders

| Folder | Contents |
|---|---|
| [`profili/`](profili/) | Creality Print profiles: process (small / large prints) and filament (SUNLU PLA Basic and PLA+) |
| [`strumenti/`](strumenti/) | Blender scripts (cutting oversized STLs with alignment pins, renders, analysis) and Python tools |
| [`firmware/simomusu93-fw/`](firmware/simomusu93-fw/) | **Simomusu93-FW** source code; changelog: [`Simomusu93-FW.md`](firmware/simomusu93-fw/Simomusu93-FW.md) |
| [`firmware/build/`](firmware/build/) | Compiled firmware `Simomusu93-FW_x.y.bin` |
| [`firmware/UPDATE-GUIDE.md`](firmware/UPDATE-GUIDE.md) | How to flash the firmware and how to go back to the original ([Italiano](firmware/GUIDA-AGGIORNAMENTO.md)) |
| [`firmware/ANALYSIS.md`](firmware/ANALYSIS.md) | Analysis of the Creality and navaismo firmware |
| [`strumenti/banco_prova/`](strumenti/banco_prova/) | Firmware test bench that runs on the PC, without the printer |
| [`modelli/miei/test-firmware/`](modelli/miei/test-firmware/) | Test STLs for the firmware |
| `calibrazione/`, `manutenzione/` | Calibration notes and maintenance log |

Folder names, slicer profile names and the printer's menu labels are in Italian (the author's language); all documentation is in English.

---

## The procedure we followed

### 1. Print profiles for Creality Print

1. **Research** of recommended settings for the V3 SE and for SUNLU filaments (datasheets, forums, community tests).
2. **Process profiles**, inheriting from the official Creality presets (only the needed values are changed):
   - **Simomusu93 Piccole 0.12mm** ("small") – miniatures and fine details: 3 walls, 15% gyroid, outer walls 40 mm/s, low accelerations;
   - **Simomusu93 Grandi 0.16mm** ("large") – statues and big parts: 12% gyroid, outer walls 70 mm/s, organic supports, 6 mm brim.
3. **Filament profiles** for **SUNLU PLA Basic** and **SUNLU PLA+** (small/large variants): temperatures within SUNLU's range,
   PLA+ ~5 °C hotter, 0.8 mm retraction, 12 mm³/s max volumetric flow.
4. **Installed** in Creality Print and backed up to `profili/` with `backup-profili.ps1`.
   Details and reasoning: [`profili/README.md`](profili/README.md).

### 2. Cutting oversized models (Blender)

The bed is 220 × 220 × 250 mm. For bigger parts (e.g. a dragon body and a statue base) the Blender scripts in `strumenti/`:
1. `analizza.py` – measures the model, checks for holes and open edges;
2. `taglia.py` – cuts it into pieces that fit the bed (`tubo` for elongated shapes, `piano` for bases), with **holes for alignment pins**
   and STLs of the pins;
3. `parti.py` and `render_viste.py` – check that no stray fragments are left and render views for a visual check.

Lessons learned: an EXACT boolean on 1.4 million triangles used 28 GB of RAM → above 600k triangles the model is decimated first;
each pin is a separate cutter object (a single object holding all the cylinders gave wrong results).

### 3. The problem that started the firmware work

A print estimated at **14 hours** by Creality Print showed **60 hours** remaining on the printer, and "1%" after one hour.
Cause: the Creality firmware estimates time and percentage from the **bytes read from the SD card**, ignoring the `M73` commands
the slicer writes into the G-code. The test bench later measured the stock estimate at up to **3.8×** the real remaining time.

### 4. Firmware analysis

1. **Official 1.1.0 firmware** downloaded from the Creality website (kept as a backup, not published here): the package contains one file
   for the **C13** board (GD32F303, goes in the SD root) and one for the **C14** board (STM32F401, `STM32F4_UPDATE` folder).
2. **`.bin` structure**: not encrypted; a 28 KB Creality bootloader that is never overwritten; firmware loaded at 0x08007000;
   64 KB of RAM (the real limit); 484 KB of flash available.
3. **navaismo's 1.1.0 firmware** studied in depth: features, screens and the bugs reported by users.
4. **Pure Creality source** (V1.0.6, the only one ever published): built unmodified, it differs from the official 1.1.0 by only **8 bytes**,
   with identical strings → for the C13 board, 1.1.0 is essentially the same code. It is the base of Simomusu93-FW.

### 5. Simomusu93-FW

Every change in the code is marked `Simomusu93-FW`. Rules: few changes per version, one test per version,
**no changes to thermal protections**, strict linking (a missing function stops the build instead of producing
a firmware that crashes).

| Version | What it adds |
|---|---|
| 0.1 | Remaining time and % from the slicer (`M73`), without enabling `HAS_DISPLAY` (on the DWIN display that would turn a thermal error into a crash) |
| 0.2 | Remaining time **self-calibrated** on the real speed (e.g. printing at 160%), **current layer** "Strato 152/1078", minimum free RAM in the Info menu, linear advance (`M900`), skew correction (`M852`) |
| 0.3 | **Statistics** (prints, hours, filament), **Sound on/off**, **Filament sensor on/off**, **Settings reset with confirmation** (previously one click wiped Z-offset and leveling) – first version flashed on the printer (2026-10-14) |
| 0.4 | Info menu: "RAM libera min" (min free RAM) replaces "Contact us"; fixed the Control menu redraw when scrolling back up (empty or duplicated entries) |
| 0.5 | Fixed the "Motion" label left overlapping another entry when scrolling the Control menu back up |
| 0.6 | Fixed the layer counter showing "Z 0.44 mm" instead of "Strato X/Y": the start G-code's M190/M109 were wiping the total layer count |
| 0.7 | A new print no longer shows the % and remaining time of the previous one |

Full changelog with sizes, SHA256 and test procedures: [`Simomusu93-FW.md`](firmware/simomusu93-fw/Simomusu93-FW.md).

### 6. Test bench on the PC

Before every flash, `strumenti/banco_prova/banco_prova.ps1` checks the firmware without the printer:
1. **Level 1 – the `.bin`** (`verifica_firmware.py`, 24 checks): vector table identical to the official one, version, features present,
   flash/RAM usage, per-function stack usage;
2. **Level 2 – the G-code** (`simula_gcode.cpp`): the firmware's own layer/time parsing code, compiled for the PC, reads a real G-code
   and checks that layer count and remaining time are right, also at different speeds;
3. **Level 3 – screen previews** (`anteprima_schermo.py`): images of what the print screen will look like.

### 7. Flashing the printer

Full procedure, including going back to the original firmware: [`firmware/UPDATE-GUIDE.md`](firmware/UPDATE-GUIDE.md). In short:
1. check in **Control → Info** that the board is **CR4NS200320C13**;
2. copy the `.bin` to the root of a FAT32 microSD, **with a file name never used before**;
3. printer off → insert the microSD → power on → wait 30 seconds without touching anything;
4. check the version in Info, then run **auto Z-offset**, **auto leveling**, **Save**;
5. test prints (20 mm cube, M73 tower) from `modelli/miei/test-firmware/`;
6. to go back: same procedure with the official Creality 1.1.0 file for the C13 board.

### Next steps

- Tune **linear advance** (Creality Print "Pressure advance" test) for the SUNLU profiles.
- Measure and correct **skew** (`M852`).
- **7×7** leveling mesh for large parts.

---

## ⚠️ Disclaimer

Simomusu93-FW is a personal project, tested on a single printer. Use it only with a **CR4NS200320C13** board and
only if you know how to go back to the original Creality firmware. Provided "as is", without any warranty (GPL-3.0, sections 15–16):
you flash it at your own risk.

## Trademarks

This is an independent community project. It is **not affiliated with, endorsed by or supported by Creality**.
"Creality", "Ender" and "Creality Print" are trademarks of their respective owners and are used here only to describe
which printer and software this project works with. No Creality logos, images or official firmware files are included.

## Licenses

- `firmware/simomusu93-fw/` is derived from [Marlin](https://github.com/MarlinFirmware/Marlin) and from
  [CrealityOfficial/Ender-3V3-SE](https://github.com/CrealityOfficial/Ender-3V3-SE): **GPL-3.0** (see `firmware/simomusu93-fw/LICENSE`).
  UI ideas come from [navaismo/Ender-3V3-SE](https://github.com/navaismo/Ender-3V3-SE) (GPL-3.0); the code was rewritten.
- No third-party models, G-code, official firmware or images are included.
