"""Banco di prova Simomusu93-FW – livello 1: controllo del firmware compilato (senza stampante).

Uso: python verifica_firmware.py <cartella_build_env> <file.bin_da_controllare>
  cartella_build_env = es. %USERPROFILE%\\.pio-build\\simomusu93\\STM32F103RET6_creality (contiene firmware.elf e i .su)
"""
import sys, os, re, struct, subprocess, glob

# Toolchain ARM installata da PlatformIO (%PLATFORMIO_CORE_DIR% o ~/.platformio)
TC = os.path.join(os.environ.get("PLATFORMIO_CORE_DIR") or os.path.join(os.path.expanduser("~"), ".platformio"),
                  "packages", "toolchain-gccarmnoneeabi", "bin")
RAM_SIZE = 64 * 1024 - 40          # creality.ld
FLASH_SIZE = 512 * 1024 - 28 * 1024
LOAD_ADDR = 0x08007000

REQUIRED = {                       # funzione nel firmware -> funzionalità
    "GcodeSuite::M73()": "tempo e % dallo slicer (M73)",
    "Simomusu93GcodeInfo::parse()": "lettura strato/totale dai commenti del G-code",
    "Draw_Print_Layer()": "riga 'Strato X/Y' nella schermata di stampa",
    "simomusu93_ram_free_min()": "misuratore RAM libera (menu Info)",
    "simomusu93_ram_paint()": "riempimento RAM all'avvio",
    "GcodeSuite::M852()": "correzione squadratura (M852)",
    "GcodeSuite::M500()": "salvataggio impostazioni (M500)",
    "Temperature::min_temp_error(heater_id_t)": "protezione temperatura minima (intatta)",
    "Temperature::max_temp_error(heater_id_t)": "protezione temperatura massima (intatta)",
    "HMI_Filament()": "gestione sensore fine filamento (Creality)",
    # 0.3
    "Draw_Simomusu93_Stats()": "schermata Statistiche (0.3)",
    "HMI_Simomusu93_Stats()": "ritorno dalla schermata Statistiche (0.3)",
    "MarlinUI::buzzer_enabled": "interruttore Suono (0.3)",
    "simomusu93_runout_enabled": "interruttore Sensore filo (0.3)",
    "PrintCounter::data": "statistiche di stampa salvate (PRINTCOUNTER)",
    # 0.9
    "simomusu93_render_thumb(": "anteprima del G-code sullo schermo (0.9)",
}

ok = fail = 0
def check(cond, msg):
    global ok, fail
    print(("  OK     " if cond else "  ERRORE ") + msg)
    if cond: ok += 1
    else: fail += 1

def run(tool, *args):
    return subprocess.run([os.path.join(TC, tool)] + list(args), capture_output=True, text=True, errors="replace").stdout

build, binf = sys.argv[1], sys.argv[2]
elf = os.path.join(build, "firmware.elf")
b = open(binf, "rb").read()
print(f"Firmware: {binf}  ({len(b):,} byte)")

print("\n1) Struttura del file")
sp, reset = struct.unpack_from("<II", b, 0)
check(0x20000000 < sp <= 0x20010000, f"stack iniziale in RAM (0x{sp:08X})")
check(LOAD_ADDR <= (reset & ~1) < LOAD_ADDR + len(b) and reset & 1, f"avvio dentro il firmware, modalità Thumb (0x{reset:08X})")
check(len(b) <= FLASH_SIZE, f"entra nella flash: {len(b)/1024:.1f} KB su {FLASH_SIZE/1024:.0f} KB ({100*len(b)/FLASH_SIZE:.0f}%)")
m = re.search(rb"FIRMWARE_NAME:Marlin (.+?) \(", b)   # la versione può contenere spazi ("Simomusu93 0.3")
check(m is not None and m.group(1).startswith(b"Simomusu93"), f"versione nel firmware: {m.group(1).decode() if m else '?'}")

print("\n2) Funzionalità presenti")
syms = run("arm-none-eabi-nm.exe", "-C", elf)
ver = m.group(1).decode() if m else ""
for name, what in REQUIRED.items():
    if "(0.3)" in what and ver in ("Simomusu93 0.1", "Simomusu93 0.2"): continue
    if "(0.9)" in what and re.match(r"Simomusu93 0\.[1-8]$", ver): continue
    check(name in syms, what)
# 0.8: linear advance spento come nel firmware Creality (con l'input shaping Creality sottoestrudeva il primo strato)
check("GcodeSuite::M900()" not in syms, "linear advance spento (M900 assente, come Creality)")
kill_screen_called = "MarlinUI::kill_screen" in syms and " U MarlinUI::kill_screen" in syms
check(not kill_screen_called, "nessuna chiamata a funzioni inesistenti (bug di navaismo su kill_screen)")
undef = [l for l in syms.splitlines() if re.match(r"^\s+U ", l)]
check(not undef, f"nessun simbolo non risolto ({len(undef)})")

print("\n3) Memoria")
size = run("arm-none-eabi-size.exe", "-A", elf)
sec = {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\.\w+)\s+(\d+)", size, re.M)}
static_ram = sec.get(".data", 0) + sec.get(".bss", 0)
free_ram = RAM_SIZE - static_ram
check(static_ram < 0.6 * RAM_SIZE, f"RAM fissa: {static_ram/1024:.1f} KB su {RAM_SIZE/1024:.0f} KB -> {free_ram/1024:.1f} KB per stack e heap")

su = []
for f in glob.glob(os.path.join(build, "**", "*.su"), recursive=True):
    for line in open(f, encoding="utf-8", errors="replace"):
        p = line.rstrip().split("\t")
        if len(p) >= 3 and p[1].isdigit():
            su.append((int(p[1]), p[2], p[0].split(":")[-1] if ":" in p[0] else p[0]))
if su:
    su.sort(reverse=True)
    biggest = su[0][0]
    check(biggest < free_ram / 8, f"funzione con più stack: {biggest} byte ({su[0][2]}) – meno di 1/8 dello spazio libero")
    dyn = [s for s in su if "dynamic" in s[1]]
    print(f"         funzioni con stack variabile (alloca/VLA): {len(dyn)}")
    print("         le 8 funzioni con più stack:")
    for n, kind, fn in su[:8]:
        print(f"           {n:5d} byte  {fn}  [{kind}]")
    simomusu93 = [s for s in su if "simomusu93" in s[2].lower() or "Simomusu93" in s[2] or "Draw_Print_Layer" in s[2]]
    if simomusu93:
        print("         funzioni Simomusu93-FW:", ", ".join(f"{s[2]} {s[0]} B" for s in simomusu93))
else:
    print("  (nessun file .su: compilare con -fstack-usage)")

print(f"\nRisultato: {ok} controlli OK, {fail} errori -> {'TUTTO OK' if not fail else 'PROBLEMI TROVATI'}")
sys.exit(1 if fail else 0)
