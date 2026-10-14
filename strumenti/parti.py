# Elenca le parti staccate (shell) dentro ogni STL: volume, dimensioni, posizione.
# Uso: blender -b --factory-startup --python parti.py -- file1.stl [file2.stl ...]
import bpy, bmesh, sys, os
import numpy as np

for f in sys.argv[sys.argv.index("--") + 1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=f)
    ob = bpy.context.selected_objects[0]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    seen, shells = set(), []
    for v in bm.verts:
        if v.index in seen: continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            x = stack.pop(); comp.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o.index not in seen:
                    seen.add(o.index); stack.append(o)
        P = np.array([tuple(x.co) for x in comp])
        shells.append((len(comp), P.min(0), P.max(0)))
    shells.sort(key=lambda s: -s[0])
    print(f"PARTI| {os.path.basename(f)}: {len(shells)} shell")
    for n, mn, mx in shells:
        print(f"PARTI|   {n:7d} vertici  dim {np.round(mx - mn, 1)}  min z {mn[2]:.1f}  centro {np.round((mn + mx) / 2, 1)}")
