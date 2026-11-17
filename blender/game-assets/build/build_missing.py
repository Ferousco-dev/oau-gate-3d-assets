"""Builds the assets the free packs do not cover: characters, vehicles, props, pickups, chasers.
Run: blender -b -P build_missing.py      Units m, Z up, assets face -Y, origin at ground contact, flat-colour low-poly."""
import bpy, math, os
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP, REV = os.path.join(ROOT, "exports"), os.path.join(ROOT, "review")
GHOST = os.path.join(ROOT, "downloads/graveyard/Models/GLB format/character-ghost.glb")
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
MATS = {}


def mat(name, rgb, rough=0.8, emit=0.0):
    if name not in MATS:
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
        if emit:
            b.inputs["Emission Color"].default_value = (*rgb, 1); b.inputs["Emission Strength"].default_value = emit
        MATS[name] = m
    return MATS[name]


SKIN, DSKIN = mat("skin", (0.36, 0.22, 0.14)), mat("skin_dark", (0.24, 0.14, 0.09))
WHITE, BLACK, RED = mat("white", (0.9, 0.9, 0.88)), mat("black", (0.04, 0.04, 0.045)), mat("red", (0.75, 0.08, 0.06))
YEL, BLUE, GREY = mat("yellow", (0.95, 0.72, 0.05)), mat("blue", (0.1, 0.25, 0.7)), mat("grey", (0.45, 0.46, 0.5))
GREEN, ORANGE, PAPER = mat("green", (0.1, 0.5, 0.15)), mat("orange", (0.9, 0.4, 0.05)), mat("paper", (0.92, 0.9, 0.8))


def prim(kind, name, size, loc, m, rot=(0, 0, 0), seg=12):
    if kind == "box":
        bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
        o = bpy.context.active_object; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    elif kind == "cyl":
        bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=size[0], depth=size[1], location=loc, rotation=rot); o = bpy.context.active_object
    else:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(4, seg // 2), radius=size[0], location=loc, rotation=rot); o = bpy.context.active_object
    o.name = name; o.data.materials.append(m)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def text(name, s, size, loc, m, rot=(math.pi / 2, 0, 0), extrude=0.02):
    bpy.ops.object.text_add(location=loc, rotation=rot)
    o = bpy.context.active_object; o.name = name; o.data.body = s; o.data.size = size
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = extrude
    o.data.materials.append(m)
    bpy.context.view_layer.objects.active = o; o.select_set(True)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


def finish(asset, parts, collider=None):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = asset
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    sc.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")     # origin at ground contact, centred
    bpy.ops.object.shade_flat()
    return o


def person(prefix, shirt, pants, skin, x=0, y=0, hat=None, scale=1.0):
    parts = []
    parts.append(prim("box", "legL", (0.16, 0.18, 0.78), (x - 0.11, y, 0.39), pants))
    parts.append(prim("box", "legR", (0.16, 0.18, 0.78), (x + 0.11, y, 0.39), pants))
    parts.append(prim("box", "torso", (0.46, 0.24, 0.62), (x, y, 1.09), shirt))
    parts.append(prim("box", "armL", (0.12, 0.14, 0.6), (x - 0.3, y, 1.1), skin))
    parts.append(prim("box", "armR", (0.12, 0.14, 0.6), (x + 0.3, y, 1.1), skin))
    parts.append(prim("sph", "head", (0.17,), (x, y, 1.6), skin, seg=10))
    if hat:
        parts.append(prim("cyl", "hat", (0.19, 0.08), (x, y, 1.72), hat, seg=10))
    return parts


built = []


def asset_ict_man():
    p = person("ICT", mat("ict_shirt", (0.9, 0.9, 0.92)), mat("ict_pants", (0.12, 0.12, 0.3)), DSKIN, hat=None)
    # arms raised, waving; lanyard + big ICT tag board held up
    p += [prim("box", "board", (1.1, 0.06, 0.6), (0, -0.25, 1.9), YEL)]
    p += [prim("box", "pole", (0.05, 0.05, 0.75), (0, -0.25, 1.45), GREY)]
    p += [text("ICTtxt", "ICT", 0.38, (0, -0.29, 1.9), BLACK)]
    p += [prim("box", "lanyard", (0.06, 0.02, 0.42), (0, -0.14, 1.12), RED)]
    return finish("PR_ICTMan", p)


def asset_student_queue():
    cols = [(0.8, 0.2, 0.2), (0.2, 0.5, 0.8), (0.9, 0.7, 0.1), (0.3, 0.7, 0.3), (0.6, 0.3, 0.7)]
    p = []
    for i, c in enumerate(cols):
        p += person("S", mat(f"q{i}", c), mat("jeans", (0.12, 0.18, 0.4)), SKIN if i % 2 else DSKIN, x=(i - 2) * 0.6, y=0)
    p += [prim("box", "rope", (3.0, 0.04, 0.05), (0, -0.4, 0.9), RED)]
    return finish("PR_RegistrationQueue", p)


def asset_gboro_bus():
    p = [prim("box", "body", (2.0, 5.2, 1.9), (0, 0, 1.25), YEL),
         prim("box", "stripe", (2.02, 5.22, 0.35), (0, 0, 1.0), BLACK),
         prim("box", "glass", (2.02, 3.9, 0.7), (0, -0.4, 1.75), mat("glass", (0.25, 0.4, 0.55), 0.2)),
         prim("box", "roof", (1.9, 5.0, 0.12), (0, 0, 2.25), mat("roof", (0.8, 0.6, 0.05)))]
    for sx in (-1, 1):
        for y in (-1.7, 1.7):
            p.append(prim("cyl", "wheel", (0.42, 0.28), (sx * 1.0, y, 0.42), BLACK, rot=(0, math.pi / 2, 0)))
    p.append(text("bustxt", "GBORO", 0.35, (0, -2.62, 1.3), BLACK))
    return finish("VH_GboroBus", p)


def asset_okada():
    p = [prim("cyl", "wheelF", (0.33, 0.12), (0, -0.8, 0.33), BLACK, rot=(0, math.pi / 2, 0)),
         prim("cyl", "wheelR", (0.33, 0.12), (0, 0.8, 0.33), BLACK, rot=(0, math.pi / 2, 0)),
         prim("box", "frame", (0.2, 1.5, 0.3), (0, 0, 0.62), RED),
         prim("box", "tank", (0.3, 0.5, 0.25), (0, -0.2, 0.88), ORANGE),
         prim("box", "seat", (0.26, 0.6, 0.1), (0, 0.35, 0.82), BLACK),
         prim("box", "bars", (0.7, 0.06, 0.06), (0, -0.7, 1.05), GREY)]
    p += person("R", mat("rider", (0.1, 0.45, 0.2)), mat("rpants", (0.2, 0.2, 0.2)), DSKIN, y=0.35)
    for q in p[-6:]:
        q.location.z += 0.12
    p.append(prim("sph", "helmet", (0.2,), (0, 0.35, 1.9), WHITE, seg=10))
    return finish("VH_OkadaRider", p)


def asset_handouts():
    p = []
    for i in range(7):
        p.append(prim("box", f"h{i}", (0.9, 0.62, 0.12), (0.04 * (i % 3 - 1), 0.02 * (i % 2), 0.06 + i * 0.12), PAPER if i % 2 else mat("paper2", (0.85, 0.8, 0.65))))
    p.append(prim("box", "band", (0.92, 0.1, 0.9), (0, 0, 0.45), RED))
    p.append(text("hotxt", "BUY ME", 0.14, (0, -0.33, 0.9), BLACK))
    return finish("PR_HandoutStack", p)


def asset_portal_sign():
    p = [prim("box", "postL", (0.08, 0.08, 2.0), (-0.9, 0, 1.0), GREY), prim("box", "postR", (0.08, 0.08, 2.0), (0.9, 0, 1.0), GREY),
         prim("box", "panel", (2.1, 0.08, 1.1), (0, 0, 2.0), BLUE),
         text("t1", "PORTAL ERROR", 0.22, (0, -0.06, 2.2), WHITE), text("t2", "SERVER BUSY", 0.2, (0, -0.06, 1.8), YEL)]
    return finish("PR_PortalSign", p)


def asset_buckets():
    p = []
    for i in range(5):
        x = (i - 2) * 0.55
        p.append(prim("cyl", f"b{i}", (0.22, 0.34), (x, 0, 0.17), mat("bucket", (0.1, 0.35, 0.85 if i % 2 else 0.6))))
        p.append(prim("cyl", f"w{i}", (0.19, 0.02), (x, 0, 0.33), mat("water", (0.3, 0.6, 0.9), 0.2)))
    return finish("PR_WaterBuckets", p)


def asset_heart():
    p = [prim("sph", "l", (0.28,), (-0.17, 0, 0.9), RED, seg=10), prim("sph", "r", (0.28,), (0.17, 0, 0.9), RED, seg=10),
         prim("box", "pt", (0.4, 0.3, 0.4), (0, 0, 0.7), RED, rot=(0, math.pi / 4, 0)),
         prim("cyl", "base", (0.3, 0.05), (0, 0, 0.1), mat("pad", (1, 1, 1), 0.5, 0.6))]
    return finish("PK_HealthHeart", p)


def asset_star():
    bpy.ops.mesh.primitive_cylinder_add(vertices=5, radius=0.4, depth=0.14, location=(0, 0, 0.9), rotation=(math.pi / 2, 0, 0))
    s = bpy.context.active_object; s.data.materials.append(mat("gold", (1.0, 0.8, 0.1), 0.4, 0.4))
    p = [s, text("aplus", "A+", 0.28, (0, -0.1, 0.9), BLACK), prim("cyl", "base", (0.3, 0.05), (0, 0, 0.1), mat("pad", (1, 1, 1), 0.5, 0.6))]
    return finish("PK_CGPABoost", p)


def asset_fuel():
    p = [prim("box", "can", (0.4, 0.2, 0.5), (0, 0, 0.5), RED), prim("box", "neck", (0.12, 0.12, 0.14), (0.1, 0, 0.82), BLACK),
         prim("box", "handle", (0.18, 0.06, 0.06), (-0.08, 0, 0.8), BLACK),
         prim("cyl", "base", (0.3, 0.05), (0, 0, 0.1), mat("pad", (1, 1, 1), 0.5, 0.6))]
    p.append(text("rtxt", "F", 0.22, (0, -0.11, 0.5), WHITE))
    return finish("PK_RocketFuel", p)


def asset_sachet():
    p = [prim("box", "pack", (0.3, 0.06, 0.4), (0, 0, 0.55), mat("sachet", (0.5, 0.8, 1.0), 0.3)),
         prim("box", "seal", (0.3, 0.07, 0.04), (0, 0, 0.75), WHITE),
         prim("cyl", "base", (0.3, 0.05), (0, 0, 0.1), mat("pad", (1, 1, 1), 0.5, 0.6))]
    return finish("PK_WaterSachet", p)


def asset_chasers():
    out = []
    for nm, col, label in (("Yellow", (1.0, 0.82, 0.05), "YELLOW HOUSE"), ("White", (0.96, 0.96, 0.98), "WHITE HOUSE")):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=GHOST)
        new = [o for o in bpy.data.objects if o not in before]
        for o in new:
            o.animation_data_clear()
            if o.type == "ARMATURE": o.data.pose_position = "REST"
        bpy.context.view_layer.update()
        meshes = [o for o in new if o.type == "MESH"]
        for o in meshes:
            mw = o.matrix_world.copy(); o.parent = None; o.matrix_world = mw
            print("GHOSTIMPORT", o.name, [round(v, 2) for v in o.rotation_euler] if o.rotation_mode != "QUATERNION" else [round(v, 2) for v in o.rotation_quaternion], [round(v, 2) for v in o.scale], [m.type for m in o.modifiers])
        for o in new:
            if o.type != "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        g = meshes[0]
        if len(meshes) > 1:
            bpy.ops.object.select_all(action="DESELECT")
            for o in meshes: o.select_set(True)
            bpy.context.view_layer.objects.active = g; bpy.ops.object.join()
        g.data.materials.clear()
        m = bpy.data.materials.new(f"ghost_{nm}"); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = 0.6
        b.inputs["Emission Color"].default_value = (*col, 1); b.inputs["Emission Strength"].default_value = 0.25
        g.data.materials.append(m)
        g.scale = (7, 7, 7)
        bpy.context.view_layer.objects.active = g; g.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bb = [g.matrix_world @ Vector(c) for c in g.bound_box]
        zmin = min(v.z for v in bb); g.location.z -= zmin - 0.5
        sign = prim("box", "sign", (3.6, 0.2, 0.9), (0, -3.0, 1.2), BLACK)
        t = text("sgn", label, 0.5, (0, -3.12, 1.2), bpy.data.materials.get(f"ghost_{nm}"), extrude=0.04)
        o = finish(f"EN_Chaser{nm}House", [g, sign, t])
        out.append(o)
    return out


builders = [asset_ict_man, asset_student_queue, asset_gboro_bus, asset_okada, asset_handouts, asset_portal_sign,
            asset_buckets, asset_heart, asset_star, asset_fuel, asset_sachet]
for fn in builders:
    built.append(fn())
built += asset_chasers()

# ---- export each asset as its own GLB, then lay all out for a preview
for o in built:
    bpy.ops.object.select_all(action="DESELECT"); o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.gltf(filepath=os.path.join(EXP, o.name + ".glb"), export_format="GLB", use_selection=True, export_apply=True, export_animations=False)
    print("EXPORT", o.name, len(o.data.polygons), "faces", [round(d, 2) for d in o.dimensions])

x = 0.0
small = [o for o in built if not o.name.startswith("EN_")]
for o in small:
    w = max(o.dimensions.x, o.dimensions.y, 1.0)
    o.location.x = x + w / 2; x += w + 1.0
cx = x / 2
for i, o in enumerate([o for o in built if o.name.startswith("EN_")]):
    o.location = (cx - 5 + i * 10, 9, 0); print('CHASER', o.name, tuple(o.location))
# floor, light, camera
bpy.ops.mesh.primitive_plane_add(size=300, location=(20, 0, -0.01)); bpy.context.active_object.data.materials.append(mat("floor", (0.18, 0.2, 0.18), 1.0))
bpy.ops.object.light_add(type="SUN", rotation=(math.radians(50), 0, math.radians(30))); bpy.context.active_object.data.energy = 2.2
w = bpy.data.worlds.new("w"); sc.world = w; w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.6, 0.75, 0.95, 1)
bpy.ops.object.camera_add(location=(cx, -24, 12)); cam = bpy.context.active_object
cam.data.lens = 17
d = Vector((cx, 4, 2.5)) - cam.location; cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler(); sc.camera = cam
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 1920, 800
sc.render.filepath = os.path.join(REV, "missing_assets.png"); bpy.ops.render.render(write_still=True)
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "Game_Assets_master.blend"))
print("DONE", len(built))
