# Guide: flashing Simomusu93-FW and going back to the original firmware

Printer: Creality Ender-3 V3 SE · mainboard **CR4NS200320C13** (GD32F303 chip). [Versione italiana](GUIDA-AGGIORNAMENTO.md).

| File | Where |
|---|---|
| New firmware | `firmware/build/Simomusu93-FW_0.9.bin` |
| Original firmware (backup) | `Ender3 V3 SE GD303SWV1.1.0_HWCR4NS200320C13_20250422.bin` from the official Creality download page (not included in this repository) |

The printer's menus are shown here in English; on an Italian-language printer they are *Controllo → Info*, *Livellamento*, *Salva impostazioni*.

---

## 0. Before you start (once)

1. **Wait for any running print to finish.**
2. **Check the board**: menu **Control → Info**. At the bottom, the hardware version must read **CR4NS200320C13**.
   If it says **C14** (or F401): **stop**, this firmware is not for your board.
3. **Write down** (or take a photo of) the Info screen and your current **Z-offset**.
4. Prepare a **dedicated microSD** for the update (the printer's one works too, but an empty one is better):
   - formatted **FAT32** (right-click the drive in File Explorer → Format → FAT32);
   - keep the original firmware on the PC too, so you can go back at any time.

## 1. Flashing Simomusu93-FW

1. Copy `Simomusu93-FW_0.9.bin` to the **root** of the microSD (not inside a folder).
2. **Rename it to a name never used before**: at most 8 letters/digits, **no spaces and no extra dots**, e.g. `fw09.bin`.
   Names like `sm93_0.8.bin` (two dots) don't work: Windows stores them with a short name like `SM93_0~1.BIN`, the same for 0.6, 0.7, 0.8…,
   and the bootloader takes it for the firmware already installed (happened on 2026-10-14).
   The bootloader ignores a file whose name was already installed: use a new name every time (`fw09b.bin`, …).
3. Safely eject the microSD from the PC.
4. **Switch the printer off** with the power switch.
5. Insert the microSD into the printer.
6. **Switch on** and **don't touch anything for at least 30 seconds**: the bootloader copies the firmware (usually 10–15 s).
   The screen may stay black or frozen meanwhile: that's normal.
   **Do not switch off during this phase.**
7. When the menu appears, go to **Control → Info**: it must read **`Simomusu93 0.9`**.
   If it still shows the old version, the file was not read → rename it to another new name and repeat from step 4.
8. Remove the microSD and delete the `.bin` (or leave it: with the same name it won't be installed again).

## 2. After the first boot (required)

The new firmware **resets the saved settings** (Z-offset, leveling, PID) when coming from the Creality firmware or from 0.1/0.2.
The language is kept. From 0.3 onwards the settings are kept: just check the Z-offset.

1. **Leveling → Auto Z-offset** (the pressure sensor measures the nozzle).
2. **Leveling → Auto bed leveling** (4×4 grid).
3. **Control → Save settings**.
4. Compare the Z-offset with the one you wrote down: if it's very different (more than ~0.2 mm), repeat step 1.

## 3. Tests (stay near the printer)

Use the files in `modelli/miei/test-firmware/` (instructions in that folder's README):

1. **20 mm cube** (≈20 min): stable heating, regular print, normal end of print.
2. **M73 tower** (≈1 h): remaining time close to Creality Print's estimate, **"Strato X/Y"** (layer) line increasing.
3. **Control menu**, at the bottom: **Statistiche** (open and go back), **Suono** (sound, Sì↔No), **Sensore filo** (filament sensor, Sì↔No),
   **Reset**: a single click → "Clic ancora: RESET" appears → **turn the knob** to cancel (don't click a second time).
   Scroll down to the last entry and back up to "Back": every entry must appear exactly once.
4. **Control → Info**: note "RAM libera min" (yellow line in place of "Contact us") right after power-on and after the tower.

If anything goes wrong (strange heating, freezes, overlapping text): **switch off** and go to step 4.
A photo of the screen helps understand the problem.

## 3b. G-code preview (from 0.9)

The printer shows the model picture on the file confirm screen only if the G-code contains the preview block. Two ways to add it:
- **automatically**: in Creality Print, process settings → *Others* (advanced/expert view) → **Post-processing scripts**, enter
  `"C:\Users\<user>\.venvs\pio\Scripts\python.exe" "<project>\strumenti\anteprima_gcode.py";`
  (with your own paths); every exported G-code then gets the preview;
- **by hand**: drag one or more G-code files onto `strumenti/anteprima_gcode.bat`.
Without the block the screen shows Creality's robot as before. Drawing takes 1–4 seconds ("Anteprima..." in the title).

## 4. Going back to the original firmware (backup)

The official package from the Creality website (`…HWCR4NS200320C13C14_SWV1.1.0_GD303STM32F401.rar`) contains two files:
the one in the root, `…GD303…HWCR4NS200320C13….bin`, is for the **C13** board; the one in `STM32F4_UPDATE/` is for the C14 board — **don't copy it**.

Same procedure as step 1, with the original file:

1. Copy `Ender3 V3 SE GD303SWV1.1.0_HWCR4NS200320C13_20250422.bin` to the root of the microSD.
2. Rename it to a **new name**, e.g. `orig110.bin`.
3. Printer **off** → insert the microSD → **switch on** → wait 30 seconds without touching.
4. **Control → Info**: the Creality version must appear (e.g. V1.1.0).
5. Settings are reset here too: redo **auto Z-offset**, **leveling** and **Save**.

The bootloader (the part that reads the microSD at power-on) is **never overwritten** by these files:
that's why you can always put the original firmware back.

## Common problems

| What happens | What to do |
|---|---|
| The version in Info doesn't change | `.bin` name already used, or file not in the root → new name, repeat |
| Black screen for more than 2 minutes | Switch off, check that the SD is FAT32 and the file is the right one, retry with a new name; otherwise flash the original firmware |
| Leveling / Z-offset error | Redo auto Z-offset before leveling; clean nozzle |
| Any doubt | Go back to the original (step 4): it is always possible |
