"""Estrae fotogrammi distribuiti da una GIF e li mette in un unico foglio (provino) ridotto.
Uso: python fotogrammi_gif.py <file.gif> <out.png> [numero_fotogrammi=8] [larghezza_singolo=300]"""
import sys
from PIL import Image, ImageSequence

src, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 8
w = int(sys.argv[4]) if len(sys.argv) > 4 else 300
im = Image.open(src)
total = getattr(im, "n_frames", 1)
idx = sorted({round(i * (total - 1) / max(1, n - 1)) for i in range(n)})
frames = []
for i in idx:
    im.seek(i)
    f = im.convert("RGB")
    f = f.resize((w, int(f.height * w / f.width)))
    frames.append(f)
cols = 4
rows = (len(frames) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * frames[0].height), (255, 255, 255))
for k, f in enumerate(frames):
    sheet.paste(f, ((k % cols) * w, (k // cols) * f.height))
sheet.save(out)
print(f"FOTOGRAMMI| {src}: {total} fotogrammi, salvati {len(frames)} in {out}")
