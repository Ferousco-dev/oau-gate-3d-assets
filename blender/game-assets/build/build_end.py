"""Round 2 assets: animated distraction characters, roadside scenery, buildings. Units m, Z up, face -Y, origin at ground.
Run: blender -b -P build_more.py"""
import bpy, math, os
from mathutils import Vector, Matrix

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXP = os.path.join(ROOT, "exports")
bpy.ops.wm.read_factory_settings(use_empty=True); sc = bpy.context.scene
sc.render.fps = 24
MATS = {}


def mat(name, rgb, rough=0.8):
    if name not in MATS:
        m = bpy.data.materials.new(name); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
        MATS[name] = m
    return MATS[name]


SKIN, DSKIN = mat("skin", (0.36, 0.22, 0.14)), mat("skin_dark", (0.24, 0.14, 0.09))
WHITE, BLACK, RED = mat("white", (0.9, 0.9, 0.88)), mat("black", (0.04, 0.04, 0.045)), mat("red", (0.75, 0.08, 0.06))
YEL, BLUE, GREY = mat("yellow", (0.95, 0.72, 0.05)), mat("blue", (0.1, 0.25, 0.7)), mat("grey", (0.45, 0.46, 0.5))
GREEN, DGREEN, ORANGE = mat("green", (0.12, 0.5, 0.15)), mat("dgreen", (0.06, 0.32, 0.1)), mat("orange", (0.9, 0.4, 0.05))
CREAM, PINK, PURPLE = mat("cream", (0.88, 0.82, 0.66)), mat("pink", (0.9, 0.3, 0.55)), mat("purple", (0.5, 0.2, 0.7))


def prim(kind, name, size, loc, m, rot=(0, 0, 0), seg=12):
    if kind == "box":
        bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot); o = bpy.context.active_object
        o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
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
    o.data.align_x = "CENTER"; o.data.align_y = "CENTER"; o.data.extrude = extrude; o.data.materials.append(m)
    bpy.ops.object.convert(target="MESH")
    return bpy.context.active_object


def finish(asset, parts):
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts: p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    o = bpy.context.active_object; o.name = asset
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    sc.cursor.location = (0, 0, 0); bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.ops.object.shade_flat()
    return o


def limb(o, pivot):
    """move the object's origin to pivot (world) so it rotates about that point"""
    c = Vector(o.location)
    o.data.transform(Matrix.Translation(c - Vector(pivot))); o.location = pivot
    return o


def export(objs, name, anim=False):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs: o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(filepath=os.path.join(EXP, name + ".glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_animations=anim)
    print("EXPORT", name, "anim" if anim else "")


def key(o, f, **kw):
    for k, v in kw.items():
        setattr(o, k, v); o.keyframe_insert(k, frame=f)


def rig_person(name, shirt, pants, skin, hair, skirt=None, arms_up=0.0, extra=None):
    """articulated person: root empty + separate parts so they can be animated; returns (root, parts dict)"""
    root = bpy.data.objects.new(name, None); sc.collection.objects.link(root)
    P = {}
    if skirt:
        P["legs"] = prim("cyl", "skirt", (0.3, 0.6), (0, 0, 0.6), skirt, seg=10)
        P["legL"] = prim("box", "legL", (0.1, 0.1, 0.35), (-0.1, 0, 0.17), skin); P["legR"] = prim("box", "legR", (0.1, 0.1, 0.35), (0.1, 0, 0.17), skin)
    else:
        P["legL"] = prim("box", "legL", (0.16, 0.18, 0.78), (-0.11, 0, 0.39), pants); P["legR"] = prim("box", "legR", (0.16, 0.18, 0.78), (0.11, 0, 0.39), pants)
    P["torso"] = prim("box", "torso", (0.44, 0.24, 0.55), (0, 0, 1.0), shirt)
    P["head"] = prim("sph", "head", (0.17,), (0, 0, 1.52), skin, seg=10)
    P["hair"] = prim("sph", "hair", (0.19,), (0, 0.04, 1.56), hair, seg=8)
    P["armL"] = limb(prim("box", "armL", (0.11, 0.13, 0.55), (-0.3, 0, 1.0), skin), (-0.28, 0, 1.25))
    P["armR"] = limb(prim("box", "armR", (0.11, 0.13, 0.55), (0.3, 0, 1.0), skin), (0.28, 0, 1.25))
    for p in P.values(): p.parent = root
    return root, P



def asset(name, parts):
    o = finish(name, parts); export([o], name); return o


# Student Union placeholder: replace with the photo-based model (skill pipeline) when the photo arrives
LIME = mat("su_wall", (0.86, 0.84, 0.76)); GLASS = mat("glass", (0.25, 0.4, 0.55), 0.2); DEEP = mat("su_deep", (0.1, 0.25, 0.15))
p = [prim("box", "ground", (30, 20, 5.5), (0, 0, 2.75), LIME), prim("box", "upper", (22, 14, 4), (0, 1, 7.5), LIME),
     prim("box", "roof", (31, 21, 0.5), (0, 0, 5.75), DEEP), prim("box", "roof2", (23, 15, 0.5), (0, 1, 9.75), DEEP),
     prim("box", "glassband", (24, 0.2, 2.2), (0, -9.2, 2.6), GLASS), prim("box", "glassband2", (18, 0.2, 2.0), (0, -5.9, 7.5), GLASS),
     prim("box", "portico", (10, 3, 0.5), (0, -11.5, 4.2), DEEP)]
for i in (-4, -1.3, 1.3, 4): p.append(prim("box", f"col{i}", (0.6, 0.6, 4.2), (i, -12.6, 2.1), LIME))
p.append(text("su", "STUDENTS' UNION BUILDING", 0.75, (0, -10.1, 5.0), mat("su_sign", (0.95, 0.9, 0.7))))
asset("EN_StudentUnion_Placeholder", p)

# graduation finish arch across the dual carriageway (span about 32 m)
p = [prim("box", "pl", (1.2, 1.2, 9), (-16, 0, 4.5), DEEP), prim("box", "pr", (1.2, 1.2, 9), (16, 0, 4.5), DEEP),
     prim("box", "beam", (34, 1.4, 2.6), (0, 0, 9.3), mat("grad", (0.55, 0.1, 0.12))),
     text("g1", "GRADUATION", 1.1, (0, -0.8, 9.3), mat("gold", (1.0, 0.8, 0.1), 0.4))]
for i in range(8): p.append(prim("box", f"fl{i}", (0.5, 0.05, 0.5), (-14 + i * 4, -0.72, 7.8), WHITE if i % 2 else BLACK))
asset("EN_GraduationArch", p)

# athletics track (Main Bowl) 176 x 92 m oval with green field, plus stand
import bmesh
def oval(name, rx, ry, h, m, n=48):
    bm = bmesh.new()
    vs = [bm.verts.new((rx * math.cos(2 * math.pi * i / n), ry * math.sin(2 * math.pi * i / n), h)) for i in range(n)]
    bm.faces.new(vs)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o); o.data.materials.append(m)
    return o
red = mat("track", (0.55, 0.12, 0.08), 0.9); grass = mat("pitch", (0.22, 0.5, 0.18), 1.0)
p = [oval("trk", 88, 46, 0.05, red), oval("fld", 70, 30, 0.08, grass)]
p.append(prim("box", "stand", (90, 7, 5), (0, 56, 2.5), mat("stand", (0.7, 0.7, 0.72))))
p.append(prim("box", "standroof", (92, 9, 0.4), (0, 54.5, 5.4), RED))
for i in range(4): p.append(prim("box", f"fl{i}", (0.3, 0.3, 14), (-60 + i * 40, -52, 7), GREY))
asset("EN_MainBowl", p)

# swimming pool and courts
asset("EN_SwimPool", [prim("box", "deck", (34, 20, 0.3), (0, 0, 0.15), mat("deck", (0.7, 0.7, 0.68))), prim("box", "water", (25, 12.5, 0.1), (0, 0, 0.32), mat("pool", (0.2, 0.7, 0.8), 0.2))])
asset("EN_TennisCourts", [prim("box", f"c{i}", (11, 24, 0.08), (i * 13, 0, 0.04), mat("court", (0.1, 0.25, 0.65) if i % 2 else (0.7, 0.2, 0.15), 0.8)) for i in range(3)] +
      [prim("box", f"n{i}", (0.05, 8, 1.0), (i * 13, 0, 0.6), WHITE) for i in range(3)])
print("DONE")
