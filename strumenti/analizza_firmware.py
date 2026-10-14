"""Analisi di un firmware .bin per microcontrollori ARM Cortex-M (Ender-3 V3 SE).
Uso: python analizza_firmware.py <file.bin> [<file2.bin> ...]
Legge la tabella dei vettori, deduce l'indirizzo di caricamento (spazio del bootloader),
misura l'entropia (cifrato o no) ed estrae stringhe utili (versioni, funzioni, comandi G-code)."""
import sys, struct, math, re, os
from collections import Counter

KEYWORDS = {
    "versione": rb"(V\d+\.\d+\.\d+[\w.]*|Marlin[ \w.\-]*\d|SWV[\w.]+|HW[\w]+C1[34]\w*|bugfix[\w.\-]*)",
    "data build": rb"((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) [ \d]\d \d{4})",
    "comandi G-code": rb"\b([MG]\d{1,4})\b",
}
FEATURES = ["Linear Advance", "LIN_ADVANCE", "Input Shaping", "M593", "M900", "M852", "Skew", "Mesh", "Bilinear",
            "Thermal Runaway", "THERMAL RUNAWAY", "MINTEMP", "MAXTEMP", "Heating failed", "Probe", "CRTouch", "BLTouch",
            "Z Offset", "M117", "Layer", "layer", "Octoprint", "OctoPrint", "Statistics", "Buzzer", "Runout", "M600",
            "thumbnail", "Thumbnail", "QR", "Orca", "Cura", "PRUSA", "M73", "Print Time"]


def entropy(b):
    c = Counter(b); n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())


def strings(b, minlen=5):
    return [m.group().decode("ascii", "replace") for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, b)]


def analyze(path):
    b = open(path, "rb").read()
    print("=" * 90)
    print(f"{os.path.basename(path)}  –  {len(b):,} byte")
    print(f"entropia: {entropy(b):.2f} bit/byte (codice ARM normale ~5.5-6.5; >7.8 = compresso/cifrato)")
    sp, reset = struct.unpack_from("<II", b, 0)
    vec = struct.unpack_from("<16I", b, 0)
    ok_sp = 0x20000000 <= sp <= 0x20020000
    ok_reset = (reset & 1) and 0x08000000 <= reset < 0x08100000
    print(f"stack iniziale: 0x{sp:08X} {'(RAM ok)' if ok_sp else '(non valido)'}")
    print(f"reset handler:  0x{reset:08X} {'(flash ok, Thumb)' if ok_reset else '(non valido -> forse cifrato o con header)'}")
    if ok_reset:
        handlers = [v for v in vec[1:] if v and (v & 1) and 0x08000000 <= v < 0x08100000]
        base = min(handlers) & ~0xFFF if handlers else 0
        # i gestori puntano dentro l'immagine: la base è l'indirizzo di flash meno l'offset nel file
        cand = [0x08000000, 0x08005000, 0x08007000, 0x08008000, 0x08010000, 0x0800C000]
        fits = [c for c in cand if all(c <= h < c + len(b) for h in handlers)]
        print(f"indirizzo di caricamento probabile: {', '.join(f'0x{c:08X}' for c in fits) or 'sconosciuto'}"
              f"  -> bootloader di {', '.join(f'{(c - 0x08000000) // 1024} KB' for c in fits)}")
        print(f"RAM usata dallo stack: fino a {(sp - 0x20000000) // 1024} KB")
    s = strings(b)
    print(f"stringhe di testo: {len(s)}")
    blob = b
    for name, rx in KEYWORDS.items():
        found = Counter(m.group(1).decode("ascii", "replace") for m in re.finditer(rx, blob))
        top = [k for k, _ in found.most_common(60)]
        if name == "comandi G-code":
            top = sorted(set(top), key=lambda x: (x[0], int(x[1:])))
        print(f"{name}: {', '.join(top[:60])}")
    print("funzioni trovate nel testo:", ", ".join(f for f in FEATURES if f.encode() in b))
    interesting = [x for x in s if re.search(r"(?i)(version|firmware|creality|ender|marlin|advance|shap|runaway|layer|level|probe|offset)", x)]
    print("stringhe interessanti (prime 40):")
    for x in interesting[:40]:
        print("   ", x[:110])
    return b


if __name__ == "__main__":
    for p in sys.argv[1:]:
        analyze(p)
