"""Banco di prova Simomusu93-FW – livello 3: anteprima APPROSSIMATA della schermata di stampa (240x320).

Usa le coordinate di ui_position.h (schermo DWIN 320) e i valori calcolati da simula_gcode (CSV).
Le icone vere stanno nella memoria dello schermo e qui sono disegnate come semplici forme:
serve a vedere QUALI numeri compaiono e DOVE, non l'aspetto esatto.

Uso: python anteprima_schermo.py <risultati.csv> <nome_file> <cartella_out> <minuti1> [minuti2 ...]
"""
import sys, os, csv
from PIL import Image, ImageDraw, ImageFont

W, H = 240, 320
BG, FG, GREY, ACC, RED = (8, 8, 8), (235, 235, 235), (120, 120, 120), (60, 170, 255), (255, 90, 80)

def font(sz):
    for f in (r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

F16, F12, F10 = font(15), font(11), font(9)

def hhmm(minutes):
    if minutes is None: return "--:--"
    m = int(round(minutes))
    return ">100H" if m >= 6000 else f"{m // 60:02d}:{m % 60:02d}"

def screen(title, name, pct, elapsed, remain, layer_txt, remain_wrong=False):
    im = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 24], fill=(30, 30, 30)); d.text((8, 5), title, font=F12, fill=FG)
    d.text(((W - d.textlength(name[:30], font=F12)) / 2, 35), name[:30], font=F12, fill=FG)            # FIEL_NAME_Y
    # cerchio della percentuale (ICON_PERCENT 12,75)
    cx, cy, r = 12 + 46, 75 + 46, 44
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(50, 50, 50), width=8)
    d.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 3.6 * pct, fill=ACC, width=8)
    t = f"{pct}%"; d.text((cx - d.textlength(t, font=F16) / 2, cy - 9), t, font=F16, fill=FG)
    # colonna tempi (ICON_PRINT_TIME 117,77 / WORD 141,61 / NUM 141,92 ; RAMAIN +61)
    for i, (lab, val, col) in enumerate((("Tempo stampa", hhmm(elapsed), FG), ("Rimanente", hhmm(remain), RED if remain_wrong else FG))):
        y = 61 + 61 * i
        d.rectangle([117, y + 16, 133, y + 32], outline=GREY)
        d.text((141, y), lab, font=F10, fill=GREY)
        d.text((141, y + 31), val, font=F16, fill=col)
    if layer_txt:                                                                                 # Simomusu93: (117, 174), font 6x12
        d.text((117, 174), layer_txt, font=F12, fill=FG)
    # pulsanti (RECT_SET 12,191 68x64, passo 74)
    for i, lab in enumerate(("Regola", "Pausa", "Stop")):
        x = 12 + 74 * i
        d.rectangle([x, 191, x + 68, 255], outline=GREY); d.text((x + 34 - d.textlength(lab, font=F10) / 2, 240), lab, font=F10, fill=GREY)
    # area stato (ugello/piatto/velocità/flusso/zoffset/ventola)
    for x, y, t in ((6, 268, "210/210"), (6, 294, " 60/60"), (99, 268, "100%"), (99, 294, "100%"), (171, 268, "100%"), (171, 294, "-1.20")):
        d.text((x + 18, y + 4), t, font=F10, fill=FG)
    return im

rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8"), delimiter=";"))
name, out = sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True)
for target in map(float, sys.argv[4:]):
    r = min(rows, key=lambda x: abs(float(x["tempo_trascorso_min"]) - target))
    el = float(r["tempo_trascorso_min"]); R = float(r["m73_R_min"]); cr = float(r["stima_creality_min"])
    lay = f"Strato {r['strato']}/{r['totale']}" if int(r["totale"]) else (f"Z {float(r['z_mm']):.2f} mm" if float(r["z_mm"]) else "")
    a = screen("Creality originale", name, int(float(r["perc_file"])), el, cr, "", remain_wrong=abs(cr - R) > max(15, 0.2 * R))
    b = screen("Simomusu93-FW 0.2", name, int(r["m73_P"]), el, R, lay)
    im = Image.new("RGB", (W * 2 + 20, H + 30), (255, 255, 255)); im.paste(a, (0, 30)); im.paste(b, (W + 20, 30))
    dd = ImageDraw.Draw(im); dd.text((6, 8), f"Dopo {hhmm(el)} di stampa (anteprima approssimata)", font=F12, fill=(0, 0, 0))
    p = os.path.join(out, f"schermo_{int(el):04d}min.png"); im.save(p); print("ANTEPRIMA|", p)
