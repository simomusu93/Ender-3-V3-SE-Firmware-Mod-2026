"""Banco di prova Simomusu93-FW – livello 4: confronta l'anteprima disegnata dal firmware simulato con quella dello script.

Uso: python verifica_anteprima.py <file.gcode con blocco E3V3SE_THUMB_RAW16> <disegnato.raw> <anteprima.png>
"""
import struct, sys
from PIL import Image

gcode, raw, png = sys.argv[1:4]
exp = []
with open(gcode, encoding="utf-8", errors="replace") as f:
    inside = False
    for line in f:
        if line.startswith("; E3V3SE_THUMB_RAW16_BEGIN"): inside = True; continue
        if line.startswith("; E3V3SE_THUMB_RAW16_END"): break
        if inside: h = line[2:].strip(); exp += [int(h[i:i + 4], 16) for i in range(0, 384, 4)]
got = list(struct.unpack("<%dH" % (96 * 96), open(raw, "rb").read()))
diff = sum(1 for a, b in zip(exp, got) if a != b)
fg = sum(1 for a in exp if a)
img = Image.new("RGB", (96, 96))
img.putdata([((p >> 11) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in got])
img.resize((288, 288), Image.NEAREST).save(png)
ok = len(exp) == 96 * 96 and diff == 0
print(("  OK    " if ok else "  ERRORE ") + "anteprima disegnata = immagine dello script: %d pixel diversi su %d (modello: %d pixel)" % (diff, len(exp), fg))
print("ANTEPRIMA|" + png)
sys.exit(0 if ok else 1)
