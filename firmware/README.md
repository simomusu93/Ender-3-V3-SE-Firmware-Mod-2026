# Ender-3 V3 SE firmware

| Path | Contents | In this repository |
|---|---|---|
| `simomusu93-fw/` | **Simomusu93-FW** source (based on Creality V1.0.6); changelog in [`Simomusu93-FW.md`](simomusu93-fw/Simomusu93-FW.md) | yes |
| `build/` | compiled `Simomusu93-FW_x.y.bin` | yes |
| [`UPDATE-GUIDE.md`](UPDATE-GUIDE.md) | flashing and rollback guide ([Italiano](GUIDA-AGGIORNAMENTO.md)) | yes |
| [`ANALYSIS.md`](ANALYSIS.md) | analysis of the Creality and navaismo firmware | yes |
| `originale-creality-1.1.0/` | official Creality firmware (the safety net) | no – download it from Creality |
| `navaismo-1.1.0/` | navaismo's firmware and source | no – see [navaismo/Ender-3V3-SE](https://github.com/navaismo/Ender-3V3-SE) |
| `creality-sorgente-1.0.6/` | pristine Creality source | no – see [CrealityOfficial/Ender-3V3-SE](https://github.com/CrealityOfficial/Ender-3V3-SE) |

## Official firmware 1.1.0 (local backup)

| File | Board |
|---|---|
| `Ender3 V3 SE GD303SWV1.1.0_HWCR4NS200320C13_20250422.bin` (227,444 bytes) | **C13** – GigaDevice GD32F303 chip (SD root) |
| `STM32F4_UPDATE/Ender-3V3 SE_HW_CR4NS200141C14_SW_V1.1.0_F401_202504222.bin` (202,752 bytes) | **C14** – STM32F401 chip (copied *inside* the `STM32F4_UPDATE` folder on the SD) |

## Creality source 1.0.6

`Ender-3V3-SE-main_e7b2bad.zip` from github.com/CrealityOfficial/Ender-3V3-SE (commit `e7b2bad`, 2024-07-10),
SHA256 `959CF33B9D2AB94CBAADB57AF307A627D7304260D4EC75FC11EEC099B2DCCAE6`.
Version V1.0.6, C13 board (GD32F303), Marlin 2.0.8.x. The only Creality source ever published.

## Building

```
set PLATFORMIO_BUILD_DIR=C:\Users\<user>\.pio-build\simomusu93
pio run -d simomusu93-fw -e STM32F103RET6_creality
```

How to flash: see [`UPDATE-GUIDE.md`](UPDATE-GUIDE.md). First of all, check the board (CR4NS200320**C13** or **C14** in the Info menu).
