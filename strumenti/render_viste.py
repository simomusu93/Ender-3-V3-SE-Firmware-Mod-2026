# Render ortografico (fronte, lato, alto, prospettiva) di uno o più STL insieme.
# Uso: blender -b --factory-startup --python render_viste.py -- <cartella_output> <prefisso> <file1.stl> [file2.stl ...]
import bpy, sys, math
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
out_dir, prefix, files = args[0], args[1], args[2:]

bpy.ops.wm.read_factory_settings(use_empty=True)
colors = [(0.9, 0.55, 0.2, 1), (0.3, 0.6, 0.9, 1), (0.5, 0.8, 0.4, 1), (0.85, 0.4, 0.6, 1),
          (0.8, 0.8, 0.3, 1), (0.6, 0.5, 0.9, 1), (0.4, 0.8, 0.8, 1), (0.9, 0.3, 0.3, 1)]
objs = []
for i, f in enumerate(files):
    bpy.ops.wm.stl_import(filepath=f)
    ob = bpy.context.selected_objects[0]
    ob.color = colors[i % len(colors)]
    objs.append(ob)

pts = [ob.matrix_world @ v.co for ob in objs for v in ob.data.vertices]
mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
c = (mn + mx) / 2
size = max(mx - mn)

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.color_type = "OBJECT"
scene.display.shading.light = "STUDIO"
scene.display.shading.show_cavity = True
scene.render.resolution_x = scene.render.resolution_y = 900
scene.world = bpy.data.worlds.new("w")
scene.world.color = (1, 1, 1)

cam_data = bpy.data.cameras.new("cam")
cam = bpy.data.objects.new("cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam

views = {
    "fronte": (Vector((0, -1, 0)), "ORTHO"),
    "lato": (Vector((1, 0, 0)), "ORTHO"),
    "alto": (Vector((0, 0, 1)), "ORTHO"),
    "prospettiva": (Vector((1, -1, 0.7)).normalized(), "ORTHO"),
    "sotto": (Vector((0, 0, -1)), "ORTHO"),
}
for name, (d, kind) in views.items():
    cam_data.type = kind
    cam_data.ortho_scale = size * 1.15
    cam.location = c + d * size * 3
    up = Vector((0, 1, 0)) if name == "alto" else Vector((0, 0, 1))
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    if name == "alto":
        cam.rotation_euler = (0, 0, 0)
    if name == "sotto":
        cam.rotation_euler = (math.pi, 0, 0)
    cam_data.clip_end = size * 10
    scene.render.filepath = f"{out_dir}\\{prefix}_{name}.png"
    bpy.ops.render.render(write_still=True)
print(f"BBOX min={tuple(round(x,1) for x in mn)} max={tuple(round(x,1) for x in mx)}")
