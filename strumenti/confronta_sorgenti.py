"""Confronta due alberi di sorgenti (es. Creality originale vs navaismo).
Uso: python confronta_sorgenti.py <cartella_A> <cartella_B> <file_diff_out> [sottocartelle...]
Stampa i file aggiunti/rimossi/modificati con il numero di righe cambiate e salva il diff completo."""
import sys, os, difflib

EXT = {".h", ".cpp", ".c", ".ini", ".py", ".ld", ".txt", ".json", ".md"}


def files(root, subs):
    out = {}
    for s in subs:
        base = os.path.join(root, s)
        if os.path.isfile(base):
            out[s.replace("\\", "/")] = base; continue
        for d, _, fs in os.walk(base):
            for f in fs:
                if os.path.splitext(f)[1].lower() in EXT:
                    p = os.path.join(d, f)
                    out[os.path.relpath(p, root).replace("\\", "/")] = p
    return out


def lines(p):
    with open(p, "rb") as fh:
        return fh.read().decode("utf-8", "replace").replace("\r\n", "\n").splitlines()


a_root, b_root, out_path = sys.argv[1:4]
subs = sys.argv[4:] or ["Marlin", "platformio.ini", "ini", "buildroot/share/PlatformIO"]
A, B = files(a_root, subs), files(b_root, subs)
added = sorted(set(B) - set(A)); removed = sorted(set(A) - set(B))
changed = []
with open(out_path, "w", encoding="utf-8") as out:
    for k in sorted(set(A) & set(B)):
        la, lb = lines(A[k]), lines(B[k])
        if la == lb: continue
        d = list(difflib.unified_diff(la, lb, f"creality/{k}", f"navaismo/{k}", lineterm="", n=3))
        plus = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
        minus = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
        changed.append((plus + minus, plus, minus, k))
        out.write("\n".join(d) + "\n")
    for k in added:
        out.write(f"\n### NUOVO FILE: {k}\n" + "\n".join("+" + x for x in lines(B[k])) + "\n")

print(f"CONFRONTO| file modificati: {len(changed)}, aggiunti: {len(added)}, rimossi: {len(removed)}")
print(f"CONFRONTO| righe cambiate totali: +{sum(c[1] for c in changed)} -{sum(c[2] for c in changed)} (piu' {sum(len(lines(B[k])) for k in added)} righe in file nuovi)")
print("CONFRONTO| --- file modificati (piu' cambiati prima)")
for tot, p, m, k in sorted(changed, reverse=True)[:40]:
    print(f"CONFRONTO| {tot:6d}  (+{p} -{m})  {k}")
print("CONFRONTO| --- file aggiunti da B")
for k in added[:40]: print(f"CONFRONTO|   + {k}")
print("CONFRONTO| --- file rimossi in B")
for k in removed[:40]: print(f"CONFRONTO|   - {k}")
