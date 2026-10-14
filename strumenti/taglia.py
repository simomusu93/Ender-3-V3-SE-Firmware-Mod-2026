# Taglia un STL troppo grande in pezzi stampabili sulla Ender-3 V3 SE, con fori per perni di allineamento.
#
# Uso:
#   blender -b --factory-startup --python taglia.py -- tubo  <input.stl> <cartella_out> [pin_d] [prof]
#   blender -b --factory-startup --python taglia.py -- piano <input.stl> <cartella_out> [pin_d] [prof] [asse_su]
#
# tubo : modello allungato (coda, serpente, drago): segue l'asse del tubo e taglia perpendicolarmente.
# piano: modello compatto (basi, piedistalli): un taglio verticale, cerca l'angolo con cui le due metà entrano nel piano.
# pin_d: diametro perno in mm (foro = pin_d + 0.4). prof: profondità foro per lato in mm.
# asse_su: asse verticale del modello (x, y, z; default z) - per il modo piano.

import bpy, bmesh, sys, math, os
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

BED = np.array([215.0, 215.0, 245.0])   # 220x220x250 con margine
SLAB = 0.3                              # spessore della lama di taglio (mm)
CLEAR_HOLE = 0.4                         # gioco diametrale perno/foro
MIN_WALL = 4.0                          # parete minima attorno al foro

args = sys.argv[sys.argv.index("--") + 1:]
mode, src, out = args[0], args[1], args[2]
PIN_D = float(args[3]) if len(args) > 3 else 6.0
DEPTH = float(args[4]) if len(args) > 4 else 10.0
UP = args[5] if len(args) > 5 else "z"
MAX_TRI = int(args[6]) if len(args) > 6 else 600000   # oltre questa soglia il modello viene semplificato (la booleana esatta consuma molta RAM)
HOLE_R = (PIN_D + CLEAR_HOLE) / 2
os.makedirs(out, exist_ok=True)
log = []
def say(s):
    print("TAGLIA| " + s); log.append(s)


# ---------- utilità ----------
def load(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=path)
    ob = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    bm.to_mesh(ob.data); bm.free()
    ntri = len(ob.data.polygons)
    if ntri > MAX_TRI:
        bpy.context.view_layer.objects.active = ob
        m = ob.modifiers.new("dec", "DECIMATE"); m.ratio = MAX_TRI / ntri
        bpy.ops.object.modifier_apply(modifier=m.name)
        say(f"modello semplificato da {ntri} a {len(ob.data.polygons)} triangoli")
    return ob

def verts(ob):
    a = np.empty(len(ob.data.vertices) * 3); ob.data.vertices.foreach_get("co", a)
    a = a.reshape(-1, 3); M = np.array(ob.matrix_world)
    return a @ M[:3, :3].T + M[:3, 3]

def rot_down(d):
    q = Vector(d).normalized().rotation_difference(Vector((0, 0, -1)))
    return np.array(q.to_matrix())

def best_fit(P, downs):
    if len(P) > 80000:
        P = P[:: len(P) // 80000 + 1]
    best = None
    for d in downs:
        R = rot_down(d); Q = P @ R.T
        h = Q[:, 2].max() - Q[:, 2].min()
        for a in np.radians(np.arange(0, 90, 1.5)):
            c, s = math.cos(a), math.sin(a)
            x = Q[:, 0] * c - Q[:, 1] * s; y = Q[:, 0] * s + Q[:, 1] * c
            ext = np.array([x.max() - x.min(), y.max() - y.min(), h])
            over = (ext - BED).max()
            if best is None or over < best[0]:
                best = (over, tuple(d), a, ext, R)
    return best

def basis(n):
    n = Vector(n).normalized()
    u = n.orthogonal().normalized(); v = n.cross(u)
    return n, u, v

def find_pins(bvh, c, n, Rs, npins, step):
    n, u, v = basis(n); c = Vector(c)
    cand = []
    ts = np.linspace(-DEPTH - 0.5, DEPTH + 0.5, 6)
    for i in np.arange(-Rs, Rs, step):
        for j in np.arange(-Rs, Rs, step):
            p = c + u * i + v * j
            ok, clear = True, 1e9
            for t in ts:
                q = p + n * t
                loc, nor, idx, dist = bvh.find_nearest(q)
                if loc is None or (q - loc).dot(nor) > 0 or dist < HOLE_R + MIN_WALL:
                    ok = False; break
                clear = min(clear, dist)
            if ok:
                cand.append((np.array(p), clear))
    if not cand:
        return []
    pts = np.array([p for p, _ in cand])
    # campionamento del punto più lontano: perni il più distanti possibile tra loro
    first = np.argmax(np.linalg.norm(pts - pts.mean(0), axis=1))
    chosen = [first]
    while len(chosen) < npins:
        d = np.min([np.linalg.norm(pts - pts[k], axis=1) for k in chosen], axis=0)
        k = int(np.argmax(d))
        if d[k] < PIN_D * 3: break
        chosen.append(k)
    return [Vector(pts[k]) for k in chosen]

def add_box(bm, c, n, half, thick):
    n, u, v = basis(n)
    M = Matrix((u, v, n)).transposed().to_4x4(); M.translation = Vector(c)
    r = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(2 * half, 2 * half, thick), verts=r["verts"])
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])

def add_cyl(bm, c, n, r, length, seg=32):
    n, u, v = basis(n)
    M = Matrix((u, v, n)).transposed().to_4x4(); M.translation = Vector(c)
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=length)
    bmesh.ops.transform(bm, matrix=M, verts=res["verts"])

def boolean_diff(ob, cutters, solvers=("MANIFOLD", "EXACT")):
    # ogni utensile (lama o foro) è un oggetto separato: le sovrapposizioni le gestisce il solver
    coll = bpy.data.collections.new("cutters")
    bpy.context.scene.collection.children.link(coll)
    for i, cb in enumerate(cutters):
        me = bpy.data.meshes.new(f"cut{i}"); cb.to_mesh(me)
        coll.objects.link(bpy.data.objects.new(f"cut{i}", me))
    for solver in solvers:
        work = ob.copy(); work.data = ob.data.copy(); bpy.context.scene.collection.objects.link(work)
        m = work.modifiers.new("b", "BOOLEAN"); m.operation = "DIFFERENCE"
        m.operand_type = "COLLECTION"; m.collection = coll
        try:
            m.solver = solver
        except TypeError:
            continue
        bpy.context.view_layer.objects.active = work
        try:
            bpy.ops.object.modifier_apply(modifier=m.name)
        except RuntimeError as e:
            say(f"solver {solver} fallito: {e}"); continue
        if len(work.data.vertices) > 0.5 * len(ob.data.vertices) and len(work.data.vertices) != len(ob.data.vertices):
            say(f"booleana ok con solver {solver} ({len(ob.data.vertices)} -> {len(work.data.vertices)} vertici)")
            for o in list(coll.objects): bpy.data.objects.remove(o)
            bpy.data.collections.remove(coll)
            return work
        say(f"solver {solver}: risultato non valido ({len(work.data.vertices)} vertici), riprovo")
        bpy.data.objects.remove(work)
    raise RuntimeError("booleana fallita")

def split_loose(ob):
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
    return list(bpy.context.selected_objects)

def join(objs):
    for o in bpy.context.selected_objects: o.select_set(False)
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1: bpy.ops.object.join()
    return objs[0]

def export(ob, path):
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=path, export_selected_objects=True)

def place_for_print(ob, R, ang):
    c, s = math.cos(ang), math.sin(ang)
    Rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    M = Matrix((Rz @ R).tolist()).to_4x4()
    ob.data.transform(M); ob.matrix_world = Matrix.Identity(4)
    P = verts(ob); mn, mx = P.min(0), P.max(0)
    ob.data.transform(Matrix.Translation(Vector((-(mn[0] + mx[0]) / 2, -(mn[1] + mx[1]) / 2, -mn[2]))))
    return mx - mn


# ---------- carica ----------
ob = load(src)
V = verts(ob)
say(f"modello {os.path.basename(src)}: {len(V)} vertici, dimensioni {np.round(V.max(0) - V.min(0), 1)} mm")
bm0 = bmesh.new(); bm0.from_mesh(ob.data); bvh = BVHTree.FromBMesh(bm0)
cuts = []   # (centro, normale, raggio_lama)

if mode == "tubo":
    kd = KDTree(len(V))
    for i, p in enumerate(V): kd.insert(p, i)
    kd.balance()
    start = V[np.argmin(V[:, {"x": 0, "y": 1, "z": 2}[UP]])]   # parte dall'estremità più bassa
    # direzione iniziale verso il baricentro dei vertici vicini
    near = [V[i] for (_, i, _) in kd.find_range(start, 50)]
    p = np.array(start); t = np.mean(near, 0) - p; t /= np.linalg.norm(t)
    line = [p.copy()]; step, R = 6.0, 60.0
    for _ in range(400):
        q = p + t * step
        idx = [i for (_, i, _) in kd.find_range(q, R)]
        if not idx: break
        pts = V[idx]; sd = (pts - q) @ t
        sl = pts[np.abs(sd) < step / 2]
        if len(sl) < 30: break
        newp = sl.mean(0); newp = newp - ((newp - q) @ t) * t   # resta nel piano della fetta
        nt = newp - p; nt /= np.linalg.norm(nt)
        t = 0.6 * t + 0.4 * nt; t /= np.linalg.norm(t); p = newp; line.append(p.copy())
    line = np.array(line)
    seglen = np.linalg.norm(np.diff(line, axis=0), axis=1); S = np.concatenate([[0], np.cumsum(seglen)])
    L = S[-1]
    say(f"asse del tubo: {len(line)} punti, lunghezza {L:.0f} mm")
    kdl = KDTree(len(line))
    for i, p in enumerate(line): kdl.insert(p, i)
    kdl.balance()
    vidx = np.array([kdl.find(p)[1] for p in V]); sv = S[vidx]

    def tangent(s):
        i = int(np.clip(np.searchsorted(S, s), 2, len(S) - 3))
        d = line[i + 2] - line[i - 2]; return d / np.linalg.norm(d), line[i], i

    chosen = None
    for N in range(2, 12):
        cs = [L * k / N for k in range(1, N)]
        bounds = [0] + cs + [L + 1]
        worst = -1e9
        for k in range(N):
            P = V[(sv >= bounds[k]) & (sv < bounds[k + 1])]
            downs = []
            if k > 0: downs.append(-tangent(bounds[k])[0])
            if k < N - 1: downs.append(tangent(bounds[k + 1])[0])
            worst = max(worst, best_fit(P, downs)[0])
        say(f"prova {N} pezzi: sforamento peggiore {worst:.1f} mm")
        if worst <= 0:
            chosen = cs; break
    if chosen is None: raise RuntimeError("nessuna divisione trovata")
    for s in chosen:
        t, c, i = tangent(s)
        ring = V[np.abs(sv - s) < 8]
        lat = ring - c; lat = lat - np.outer(lat @ t, t)
        Rc = float(np.linalg.norm(lat, axis=1).max()) * 1.1 + 5
        cuts.append((c, t, Rc))
        say(f"taglio a {s:.0f} mm: centro {np.round(c, 1)}, direzione {np.round(t, 2)}, raggio lama {Rc:.0f} mm")
    np.savetxt(os.path.join(out, "_asse.txt"), line, fmt="%.1f")
    assign = lambda P: int(np.searchsorted(chosen, S[np.array([kdl.find(p)[1] for p in P[:: max(1, len(P) // 2000)]])].mean()))
    npins = 2

elif mode == "piano":
    ax = {"x": 0, "y": 1, "z": 2}[UP]
    upv = np.zeros(3); upv[ax] = 1
    o1, o2 = [i for i in range(3) if i != ax]
    ctr = (V.min(0) + V.max(0)) / 2
    best = None
    for th in np.radians(np.arange(0, 180, 5)):
        n = np.zeros(3); n[o1] = math.cos(th); n[o2] = math.sin(th)
        sd = (V - ctr) @ n
        w = -1e9
        for side, P in ((1, V[sd > 0]), (-1, V[sd < 0])):
            w = max(w, best_fit(P, [-upv, -side * n])[0])
        if best is None or w < best[0]: best = (w, n)
    say(f"miglior taglio verticale: normale {np.round(best[1], 2)}, sforamento peggiore {best[0]:.1f} mm")
    if best[0] > 0: raise RuntimeError("una sola sezione non basta: servono più tagli")
    cuts.append((ctr, best[1], 1000.0))
    n0 = best[1]
    assign = lambda P: int(((P - ctr) @ n0).mean() > 0)
    npins = 3
else:
    raise RuntimeError("modo sconosciuto")

# ---------- perni e lame ----------
cut_bm = []
pin_count = 0
for k, (c, n, Rc) in enumerate(cuts):
    Rs = min(Rc, 150.0)
    pins = find_pins(bvh, c, n, Rs, npins, step=max(1.5, Rs / 40))
    say(f"taglio {k + 1}: {len(pins)} perni d={PIN_D} mm (foro {HOLE_R * 2:.1f} mm, profondità {DEPTH} mm per lato)")
    b = bmesh.new(); add_box(b, c, n, Rc, SLAB); cut_bm.append(b)
    for p in pins:
        b = bmesh.new(); add_cyl(b, p, n, HOLE_R, 2 * DEPTH); cut_bm.append(b)
    pin_count += len(pins)
work = boolean_diff(ob, cut_bm)

# ---------- separa e raggruppa ----------
parts = split_loose(work)
say(f"parti separate dopo il taglio: {len(parts)}")
if len(parts) < len(cuts) + 1:
    say("il taglio non ha separato i pezzi, riprovo con il solver EXACT (più lento)")
    for p in parts: bpy.data.objects.remove(p)
    parts = split_loose(boolean_diff(ob, cut_bm, ("EXACT",)))
    say(f"parti separate dopo il taglio: {len(parts)}")
groups = {}
for prt in parts:
    groups.setdefault(assign(verts(prt)), []).append(prt)
base = os.path.splitext(os.path.basename(src))[0]
assem = os.path.join(out, "_assemblaggio"); os.makedirs(assem, exist_ok=True)
for gi, k in enumerate(sorted(groups)):
    piece = join(groups[k])
    P = verts(piece)
    downs = []
    for (c, n, _) in cuts:
        d = (P - c) @ n
        if (np.abs(d) < SLAB).sum() > 20:
            downs.append(-n if d.mean() > 0 else n)
    if mode == "piano": downs.append(-upv)
    downs += [np.array(x, float) for x in ((0, 0, -1), (0, 0, 1), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0))]
    over, d, ang, ext, R = best_fit(P, downs)
    name = f"{base}_pezzo{gi + 1:02d}.stl"
    export(piece, os.path.join(assem, name))
    size = place_for_print(piece, R, ang)
    export(piece, os.path.join(out, name))
    say(f"{name}: {size[0]:.0f} x {size[1]:.0f} x {size[2]:.0f} mm  {'OK' if over <= 0 else 'NON ENTRA!'}")

# ---------- perni ----------
if pin_count:
    pb = bmesh.new()
    L = 2 * DEPTH - 1.0
    for i in range(pin_count + 2):   # 2 di scorta
        add_cyl(pb, (i % 6 * (PIN_D + 4), i // 6 * (PIN_D + 4), L / 2), (0, 0, 1), PIN_D / 2, L)
    me = bpy.data.meshes.new("perni"); pb.to_mesh(me)
    po = bpy.data.objects.new("perni", me); bpy.context.scene.collection.objects.link(po)
    export(po, os.path.join(out, f"{base}_perni_d{PIN_D:g}x{L:g}mm_x{pin_count + 2}.stl"))
    say(f"perni: {pin_count} necessari (+2 scorta), d={PIN_D} mm, lunghezza {L} mm")

with open(os.path.join(out, "report.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(log) + "\n")
