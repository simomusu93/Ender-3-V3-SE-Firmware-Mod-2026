# Crea gli STL di prova per il firmware.
# Uso: blender -b --factory-startup --python crea_test_firmware.py -- <cartella_out>
import bpy, bmesh, sys, os, math

out = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out, exist_ok=True)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def apply_bool(target, cutter, op="DIFFERENCE"):
    m = target.modifiers.new("b", "BOOLEAN"); m.operation = op; m.object = cutter; m.solver = "EXACT"
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=m.name)
    bpy.data.objects.remove(cutter)


def text_obj(txt, size, depth, loc, rot=(0, 0, 0)):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    t = bpy.context.object
    t.data.body = txt; t.data.size = size; t.data.extrude = depth / 2
    t.data.align_x = "CENTER"; t.data.align_y = "CENTER"
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def export(ob, name):
    for o in bpy.context.selected_objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.wm.stl_export(filepath=os.path.join(out, name), export_selected_objects=True)
    d = ob.dimensions
    print(f"TEST| {name}: {d.x:.1f} x {d.y:.1f} x {d.z:.1f} mm")


# ---------- 1. cubo 20 mm con lettere incise X, Y, Z ----------
reset()
bpy.ops.mesh.primitive_cube_add(size=20, location=(0, 0, 10))
cube = bpy.context.object
d = 0.6  # profondità incisione
for txt, loc, rot in (("X", (0, -10, 10), (math.pi / 2, 0, 0)),
                      ("Y", (10, 0, 10), (math.pi / 2, 0, math.pi / 2)),
                      ("Z", (0, 0, 20), (0, 0, 0))):
    apply_bool(cube, text_obj(txt, 11, 2 * d, loc, rot))
export(cube, "test01_cubo_20mm.stl")

# ---------- 2. test tempo: base larga e sottile + torre con tacche ogni 10 mm ----------
reset()
base_w, base_h = 100.0, 0.6          # 3 strati da 0,2: il primo è lento, pochi byte per minuto
tower_r, tower_h, wall = 6.0, 50.0, 1.6
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, base_h / 2))
base = bpy.context.object; base.scale = (base_w, base_w, base_h)
bpy.ops.object.transform_apply(scale=True)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=tower_r, depth=tower_h, location=(0, 0, base_h + tower_h / 2))
tower = bpy.context.object
# tacche: anelli in rilievo da 0,6 mm alti 1 mm ogni 10 mm (riferimento per altezza/strato)
for z in range(10, int(tower_h) + 1, 10):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=tower_r + 0.6, depth=1.0, location=(0, 0, base_h + z - 0.5))
    apply_bool(tower, bpy.context.object, "UNION")
# torre cava (pareti 1,6 mm) così ogni strato è veloce
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=tower_r - wall, depth=tower_h + 2, location=(0, 0, base_h + tower_h / 2 + 1.2))
apply_bool(tower, bpy.context.object)
apply_bool(base, tower, "UNION")
# scritta in rilievo sulla base (0,6 mm) per riconoscerlo
txt = text_obj("M73", 10, 0.6, (0, -30, base_h + 0.3))
apply_bool(base, txt, "UNION")
export(base, "test02_tempo_m73.stl")
