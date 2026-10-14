# Ritaglia le figure affiancate di un foglio di riferimento (turnaround) in immagini quadrate separate su fondo bianco,
# pronte per i generatori 3D multi-vista (Tripo, Meshy, Hunyuan3D).
# Uso: blender -b --factory-startup --python ritaglia_viste.py -- <immagine> <cartella_out> <y_alto> <y_basso> <x_max> <nome1,nome2,...>
#   y_alto/y_basso: fascia verticale (pixel dall'alto) che contiene le figure intere; x_max: ignora tutto a destra.
import bpy, sys, os
import numpy as np

a = sys.argv[sys.argv.index("--") + 1:]
src, out, y0, y1, xmax, names = a[0], a[1], int(a[2]), int(a[3]), int(a[4]), a[5].split(",")
os.makedirs(out, exist_ok=True)

img = bpy.data.images.load(src)
w, h = img.size
px = np.array(img.pixels[:]).reshape(h, w, 4)[::-1]          # riga 0 = in alto
band = px[y0:y1, :xmax, :3]
bg = np.median(np.concatenate([band[:5].reshape(-1, 3), band[-5:].reshape(-1, 3)]), axis=0)
mask = np.abs(band - bg).max(axis=2) > 0.12
cols = mask.sum(axis=0) > 3

segs, start = [], None
for x, c in enumerate(list(cols) + [False]):
    if c and start is None: start = x
    if not c and start is not None:
        if x - start > 40: segs.append((start, x))
        start = None
# unisce segmenti separati da piccoli spazi (es. braccio staccato dal corpo)
merged = []
for s in segs:
    if merged and s[0] - merged[-1][1] < 12: merged[-1] = (merged[-1][0], s[1])
    else: merged.append(s)
# figure che si toccano: un segmento molto più largo degli altri viene diviso nella colonna più vuota
counts = mask.sum(axis=0)
med = np.median([b - a for a, b in merged])
split = []
for a_, b_ in merged:
    if b_ - a_ > 1.6 * med:
        lo, hi = a_ + (b_ - a_) // 3, b_ - (b_ - a_) // 3
        cut = lo + int(np.argmin(counts[lo:hi]))
        split += [(a_, cut), (cut, b_)]
    else:
        split.append((a_, b_))
merged = split
print(f"VISTE| trovate {len(merged)} figure: {merged}")

for i, (xa, xb) in enumerate(merged):
    rows = np.where(mask[:, xa:xb].any(axis=1))[0]
    ya, yb = y0 + rows.min(), y0 + rows.max() + 1
    crop = px[ya:yb, xa:xb].copy()
    # sfondo grigio chiaro -> bianco puro
    near = np.abs(crop[:, :, :3] - bg).max(axis=2) < 0.06
    crop[near, :3] = 1.0
    ch, cw = crop.shape[:2]
    side = int(max(ch, cw) * 1.12)
    canvas = np.ones((side, side, 4))
    oy, ox = (side - ch) // 2, (side - cw) // 2
    canvas[oy:oy + ch, ox:ox + cw] = crop
    canvas[:, :, 3] = 1.0
    name = names[i] if i < len(names) else f"vista{i + 1}"
    im = bpy.data.images.new(name, side, side)
    im.pixels = canvas[::-1].ravel()
    im.scale(1024, 1024)
    im.filepath_raw = os.path.join(out, f"{i + 1:02d}_{name}.png"); im.file_format = "PNG"; im.save()
    print(f"VISTE| {i + 1:02d}_{name}.png  da x {xa}-{xb}, y {ya}-{yb}")
