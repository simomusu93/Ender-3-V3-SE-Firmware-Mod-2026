"""Banco di prova Simomusu93-FW – livello 4: confronta l'anteprima disegnata dal firmware simulato con quella attesa.

Uso:
  python verifica_anteprima.py <file.gcode con anteprima> <disegnato.raw> <anteprima.png>
  python verifica_anteprima.py --crea-btt <file.gcode> <uscita.gcode>
      copia del G-code con l'anteprima 96x96 nel formato BTT_TFT, generata come fa Creality Print/OrcaSlicer
      (Thumbnails.cpp: alfa premoltiplicato, RGB565 con >>3/>>2, esadecimale minuscolo, righe ";...\r\n") e messa in cima
"""
import base64, io, re, struct, sys
from PIL import Image


def expected_pixels(gcode):
    """Pixel RGB565 attesi dal blocco dell'anteprima (formato dello script o BTT_TFT)."""
    rows, mode, w, h = [], None, 96, 96
    with open(gcode, encoding="utf-8", errors="replace") as f:
        for n, line in enumerate(f):
            line = line.rstrip("\r\n")
            if mode is None:
                if line.startswith("; E3V3SE_THUMB_RAW16_BEGIN"): mode = "raw"
                elif re.fullmatch(r";[0-9a-fA-F]{8}", line) and int(line[1:5], 16) and int(line[5:9], 16):
                    mode, w, h = "btt", int(line[1:5], 16), int(line[5:9], 16)
                elif n > 300: break
                continue
            if mode == "raw" and line.startswith("; E3V3SE_THUMB_RAW16_END"): break
            hexs = line.lstrip(";").strip()
            rows.append([int(hexs[i:i + 4], 16) for i in range(0, 4 * w, 4)])
            if len(rows) == h: break
    img = [0] * (96 * 96)
    ox, oy = (96 - w) // 2, (96 - h) // 2
    for y, r in enumerate(rows):
        for x, c in enumerate(r): img[(y + oy) * 96 + x + ox] = c
    return mode, img


def crea_btt(src, dst):
    lines = open(src, encoding="utf-8", errors="replace").read().splitlines()
    i = next(k for k, l in enumerate(lines) if re.match(r";\s*png begin 96\*96", l))
    j = next(k for k in range(i, len(lines)) if lines[k].startswith("; png end"))
    im = Image.open(io.BytesIO(base64.b64decode("".join(l[1:].strip() for l in lines[i + 1:j])))).convert("RGBA")
    px = im.load()
    out = [";%04x%04x" % (96, 96)]
    for y in range(96):
        row = ";"
        for x in range(96):
            r, g, b, a = px[x, y]
            rv, gv, bv = a * r // 255, a * g // 255, a * b // 255
            c = "%04x" % (((rv >> 3) << 11) | ((gv >> 2) << 5) | (bv >> 3))
            row += "0000" if c in ("0020", "0841", "0861") else c
        out.append(row)
    out.append("; bigtree thumbnail end")
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(out) + "\r\n\r\n" + "\n".join(lines) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "--crea-btt":
        crea_btt(sys.argv[2], sys.argv[3]); sys.exit(0)
    gcode, raw, png = sys.argv[1:4]
    mode, exp = expected_pixels(gcode)
    got = list(struct.unpack("<%dH" % (96 * 96), open(raw, "rb").read()))
    diff = sum(1 for a, b in zip(exp, got) if a != b)
    img = Image.new("RGB", (96, 96))
    img.putdata([((p >> 11) * 255 // 31, ((p >> 5) & 63) * 255 // 63, (p & 31) * 255 // 31) for p in got])
    img.resize((288, 288), Image.NEAREST).save(png)
    ok = mode is not None and diff == 0
    print(("  OK    " if ok else "  ERRORE ") + "anteprima %s disegnata = immagine attesa: %d pixel diversi su 9216 (modello: %d pixel)"
          % ({"raw": "dello script", "btt": "BTT_TFT"}.get(mode, "?"), diff, sum(1 for a in exp if a)))
    print("ANTEPRIMA|" + png)
    sys.exit(0 if ok else 1)
