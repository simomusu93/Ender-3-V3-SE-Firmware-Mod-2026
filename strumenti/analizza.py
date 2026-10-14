import bpy, bmesh, sys
from mathutils import Vector

files = sys.argv[sys.argv.index("--") + 1:]
for f in files:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.stl_import(filepath=f)
    ob = bpy.context.selected_objects[0]
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    nonman = sum(1 for e in bm.edges if not e.is_manifold)
    vol = bm.calc_volume()
    pts = [ob.matrix_world @ v.co for v in me.vertices]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    d = mx - mn
    print(f"RESULT|{f.split(chr(92))[-1]}|dim X={d.x:.1f} Y={d.y:.1f} Z={d.z:.1f} mm|min=({mn.x:.1f},{mn.y:.1f},{mn.z:.1f})|tri={len(bm.faces)}|non_manifold_edges={nonman}|volume_cm3={vol/1000:.1f}")
    bm.free()
