import bpy, math, os
from mathutils import Vector
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
names = ["VH_KekeNapep", "VH_Danfo", "EN_MangoTree"]
xs = [-6, 6, 0, 0]; ys = [0, 0, -9, -9]
xs = [-6, 0, 8]; ys = [0, 0, 2]
for n, x, y in zip(names, xs, ys):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=os.path.join(R, "exports", n + ".glb"))
    for o in set(bpy.data.objects) - before:
        if o.parent is None: o.location += Vector((x, y, 0))
    print(n, [round(v, 2) for v in [o for o in set(bpy.data.objects) - before if o.type == "MESH"][0].dimensions])
bpy.ops.mesh.primitive_plane_add(size=100); pm = bpy.data.materials.new("p"); pm.use_nodes = True
pm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.25, 0.28, 0.25, 1); bpy.context.active_object.data.materials.append(pm)
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(45), 0, math.radians(20))); bpy.context.active_object.data.energy = 3
w = bpy.data.worlds.new("w"); sc.world = w; w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.75, 0.95, 1)
bpy.ops.object.camera_add(location=(1, -16, 6)); c = bpy.context.active_object; c.data.lens = 28
c.rotation_euler = (Vector((1, 0, 2.5)) - c.location).to_track_quat("-Z", "Y").to_euler(); sc.camera = c
for e in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: sc.render.engine = e; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 1600, 800; sc.render.filepath = os.path.join(R, "review/vehicles_tree.png")
bpy.ops.render.render(write_still=True)
