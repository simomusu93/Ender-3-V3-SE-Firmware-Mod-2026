"""Simomusu93-FW: aggiunge al G-code l'anteprima nel formato che il firmware sa disegnare (dalla 0.9).

Creality Print mette nel G-code l'anteprima come PNG in base64 ("; png begin 96*96 ..."), ma lo schermo della V3 SE
non sa decodificarlo (per questo il firmware Creality mostra sempre l'omino). Questo script la converte in
    ; E3V3SE_THUMB_RAW16_BEGIN 96x96
    ; <96 pixel RGB565 in esadecimale>      (96 righe, 0000 = sfondo, non disegnato)
    ; E3V3SE_THUMB_RAW16_END
e la inserisce subito dopo l'intestazione (il firmware la cerca nelle prime 60 righe).
Alternativa senza script: in Creality Print anteprima "96x96/BTT_TFT" (il firmware legge anche quel formato).
Formato compatibile con navaismo/Marlin_bugfix_2.1_E3V3SE (SlicerScripts/orca_parser.py), scritto da zero.

Uso:
  - in Creality Print: Processo > Altro > Script di post-elaborazione:
        "<python.exe>" "<percorso>\\strumenti\\anteprima_gcode.py";
    (Creality Print passa il percorso del G-code come ultimo argomento; il file viene modificato sul posto)
  - a mano su un G-code già fatto:  python anteprima_gcode.py file.gcode [altro.gcode ...]

Se il G-code non ha l'anteprima lo lascia com'è ed esce con 0 (un errore bloccherebbe l'esportazione nello slicer).
Richiede Pillow.
"""
import base64
import io
import os
import re
import sys
import tempfile

from PIL import Image

SIZE = 96
COLORS = 32                 # pochi colori = meno comandi allo schermo = disegno più veloce (navaismo: 32)
HEADER_LINES = 60           # il firmware cerca il blocco solo qui
BEGIN = "; E3V3SE_THUMB_RAW16_BEGIN"
END = "; E3V3SE_THUMB_RAW16_END"
PIC_BEGIN = re.compile(r"^;\s*(png|jpg|thumbnail|thumbnail_PNG|thumbnail_JPG)\s+begin\s+(\d+)\s*[*x]\s*(\d+)", re.I)
PIC_END = re.compile(r"^;\s*(png|jpg|thumbnail|thumbnail_PNG|thumbnail_JPG)\s+end", re.I)


def find_thumbnail(lines):
    """Base64 dell'anteprima più adatta: 96x96 se c'è, altrimenti la più piccola fra quelle >= 96, poi la più grande."""
    found = []
    i = 0
    while i < len(lines):
        m = PIC_BEGIN.match(lines[i])
        if not m:
            i += 1
            continue
        w, h = int(m.group(2)), int(m.group(3))
        data = []
        i += 1
        while i < len(lines) and not PIC_END.match(lines[i]):
            data.append(lines[i].lstrip(";").strip())
            i += 1
        found.append((w, h, "".join(data)))
        i += 1
    if not found:
        return None
    exact = [f for f in found if f[0] == SIZE and f[1] == SIZE]
    big = sorted((f for f in found if f[0] >= SIZE), key=lambda f: f[0])
    return (exact or big or sorted(found, key=lambda f: -f[0]))[0][2]


def to_rgb565(r, g, b):
    return ((r * 31 // 255) << 11) | ((g * 63 // 255) << 5) | (b * 31 // 255)


def thumbnail_rows(b64):
    img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGBA")
    img.thumbnail((SIZE, SIZE), Image.LANCZOS)
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    canvas.paste(img, ((SIZE - img.width) // 2, (SIZE - img.height) // 2))

    px = canvas.load()
    fg = [(x, y) for y in range(SIZE) for x in range(SIZE) if px[x, y][3] >= 128]
    colors = {}
    if fg:
        # Riduce a COLORS colori solo i pixel del modello: lo sfondo (trasparente) resta 0000 = non disegnato
        strip = Image.new("RGB", (len(fg), 1))
        strip.putdata([px[x, y][:3] for x, y in fg])
        q = strip.quantize(colors=COLORS, method=Image.Quantize.MEDIANCUT).convert("RGB")
        data = q.get_flattened_data() if hasattr(q, "get_flattened_data") else q.getdata()   # getdata(): Pillow < 12.1
        for (x, y), rgb in zip(fg, data):
            c = to_rgb565(*rgb)
            colors[(x, y)] = c if c else 0x0001   # un pixel del modello quasi nero non deve diventare "sfondo"
    rows = []
    for y in range(SIZE):
        rows.append("; " + "".join("%04X" % colors.get((x, y), 0) for x in range(SIZE)))
    return rows


def process(path):
    with open(path, "rb") as f:
        raw = f.read()
    nl = "\r\n" if b"\r\n" in raw[:4096] else "\n"
    text = raw.decode("utf-8", errors="surrogateescape")
    lines = text.split(nl)

    # Toglie un blocco già presente (script lanciato due volte)
    if BEGIN in text:
        out, skip = [], False
        for line in lines:
            if line.startswith(BEGIN):
                skip = True
            elif skip and line.startswith(END):
                skip = False
                continue
            if not skip:
                out.append(line)
        lines = out

    b64 = find_thumbnail(lines[:5000])
    if not b64:
        print("anteprima_gcode: nessuna anteprima nel file, lasciato com'è:", path)
        return False

    at = 1
    for k, line in enumerate(lines[:HEADER_LINES]):
        if line.strip().upper().startswith("; HEADER_BLOCK_END"):
            at = k + 1
            break
    block = [BEGIN + " %dx%d" % (SIZE, SIZE)] + thumbnail_rows(b64) + [END]
    lines[at:at] = block

    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(os.path.abspath(path)), suffix=".tmp")
    with os.fdopen(fd, "wb") as f:
        f.write(nl.join(lines).encode("utf-8", errors="surrogateescape"))
    os.replace(tmp, path)
    print("anteprima_gcode: anteprima 96x96 aggiunta alla riga %d: %s" % (at + 1, path))
    return True


def main(argv):
    files = [a for a in argv[1:] if os.path.isfile(a)]
    if not files:
        print(__doc__)
        return 0
    for path in files:
        try:
            process(path)
        except Exception as e:   # mai bloccare l'esportazione dello slicer
            print("anteprima_gcode: errore, file lasciato com'è:", path, "-", e)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
