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


def wheel(x, y, r=0.3, w=0.18):
    return [prim("cyl", "tyre", (r, w), (x, y, r), BLACK, rot=(0, math.pi / 2, 0), seg=14), prim("cyl", "hub", (r * 0.5, w + 0.02), (x, y, r), GREY, rot=(0, math.pi / 2, 0), seg=8)]


# --- keke napep (three-wheel auto rickshaw): 2.7 x 1.35 x 1.75 m, front = -Y
GRN, KY, KB = mat("keke_green", (0.05, 0.42, 0.2)), mat("keke_yellow", (0.95, 0.75, 0.05)), mat("keke_black", (0.06, 0.06, 0.06))
p = [prim("box", "floor", (1.25, 1.9, 0.12), (0, 0.35, 0.42), GRN),
     prim("box", "cabin_back", (1.25, 0.08, 0.95), (0, 1.3, 0.95), GRN),
     prim("box", "nose", (0.8, 0.9, 0.62), (0, -0.85, 0.72), GRN), prim("box", "hood", (0.7, 0.8, 0.12), (0, -0.82, 1.1), KY, rot=(0.22, 0, 0)),
     prim("box", "roof", (1.4, 1.9, 0.1), (0, 0.45, 1.68), KY), prim("box", "stripe", (1.27, 1.9, 0.1), (0, 0.35, 0.62), KY),
     prim("box", "seat", (1.0, 0.5, 0.2), (0, 0.9, 0.62), KB), prim("box", "seat2", (0.9, 0.3, 0.35), (0, 1.17, 0.75), KB),
     prim("box", "windscreen", (1.0, 0.05, 0.62), (0, -0.4, 1.3), mat("glass", (0.3, 0.45, 0.55), 0.2), rot=(-0.25, 0, 0)),
     prim("box", "pillarL", (0.06, 0.06, 0.8), (-0.64, -0.38, 1.3), KB), prim("box", "pillarR", (0.06, 0.06, 0.8), (0.64, -0.38, 1.3), KB),
     prim("box", "pillarBL", (0.06, 0.06, 0.8), (-0.64, 1.3, 1.3), KB), prim("box", "pillarBR", (0.06, 0.06, 0.8), (0.64, 1.3, 1.3), KB),
     prim("sph", "headlight", (0.1,), (0, -1.3, 0.8), mat("lamp", (1, 0.95, 0.7), 0.3), seg=8),
     prim("box", "fender", (0.35, 0.7, 0.05), (0, -1.0, 0.55), KY),
     text("kk", "KEKE", 0.2, (0, 1.36, 0.95), KY, rot=(math.pi / 2, 0, math.pi))]
p += wheel(0, -1.05) + wheel(-0.7, 1.0) + wheel(0.7, 1.0)
asset("VH_KekeNapep", p)

# --- danfo (VW-style minibus): 5.0 x 2.0 x 2.4 m, front = -Y
DY, DB, DW = mat("danfo_yellow", (0.96, 0.78, 0.04)), mat("danfo_black", (0.05, 0.05, 0.05)), mat("danfo_glass", (0.25, 0.4, 0.5), 0.2)
p = [prim("box", "body", (2.0, 4.2, 1.45), (0, 0.25, 1.1), DY), prim("box", "hood", (1.9, 0.9, 0.9), (0, -2.15, 0.85), DY),
     prim("box", "roofhi", (1.95, 3.6, 0.7), (0, 0.45, 2.05), DY), prim("box", "stripe", (2.02, 4.2, 0.32), (0, 0.25, 0.85), DB),
     prim("box", "windscreen", (1.7, 0.06, 0.9), (0, -1.78, 1.9), DW, rot=(0.3, 0, 0)),
     prim("box", "rack", (1.7, 3.0, 0.08), (0, 0.4, 2.55), DB)]
for i in range(4): p.append(prim("box", f"win{i}", (2.03, 0.62, 0.65), (0, -0.7 + i * 0.85, 1.75), DW))
for sx in (-1, 1): p += wheel(sx * 0.95, -1.5, 0.38, 0.24) + wheel(sx * 0.95, 1.7, 0.38, 0.24)
p += [prim("box", "bumperF", (2.0, 0.18, 0.2), (0, -2.65, 0.5), mat("chrome", (0.7, 0.7, 0.72), 0.3)), prim("box", "bumperB", (2.0, 0.18, 0.2), (0, 2.45, 0.5), mat("chrome", (0.7, 0.7, 0.72), 0.3)),
      prim("sph", "hlL", (0.14,), (-0.65, -2.6, 0.9), mat("lamp", (1, 0.95, 0.7), 0.3), seg=8), prim("sph", "hlR", (0.14,), (0.65, -2.6, 0.9), mat("lamp", (1, 0.95, 0.7), 0.3), seg=8),
      text("df", "DANFO", 0.4, (1.03, 0.25, 0.85), DY, rot=(math.pi / 2, 0, math.pi / 2)), text("df2", "GOD'S TIME NO LATE", 0.22, (0, 2.38, 1.3), DB, rot=(math.pi / 2, 0, math.pi))]
asset("VH_Danfo", p)

# --- mango tree: broad dark canopy, trunk, a few fruits. ~9 m tall, 8 m canopy
TR, LV, LV2 = mat("bark", (0.28, 0.18, 0.1), 0.95), mat("mango_leaf", (0.07, 0.3, 0.08), 0.8), mat("mango_leaf2", (0.1, 0.38, 0.1), 0.8)
p = [prim("cyl", "trunk", (0.38, 4.0), (0, 0, 2.0), TR, seg=8), prim("cyl", "br1", (0.18, 2.6), (1.0, 0, 4.4), TR, rot=(0, 0.7, 0), seg=6), prim("cyl", "br2", (0.18, 2.6), (-1.0, 0.3, 4.4), TR, rot=(0, -0.7, 0), seg=6)]
import random as _r
_r.seed(3)
for i in range(11):
    a = i * 2.4; rr = 1.6 + (i % 3) * 0.9
    p.append(prim("sph", f"c{i}", (1.9 + (i % 4) * 0.35,), (rr * math.cos(a), rr * math.sin(a) * 0.9, 6.0 + (i % 3) * 0.9), LV if i % 2 else LV2, seg=7))
p.append(prim("sph", "top", (2.6,), (0, 0, 7.9), LV2, seg=7))
for i in range(6): p.append(prim("sph", f"m{i}", (0.1,), (math.cos(i * 1.1) * 2.4, math.sin(i * 1.1) * 2.1 - 1.0, 5.2 + (i % 2) * 0.5), mat("mango", (0.95, 0.6, 0.1), 0.6), seg=6))
asset("EN_MangoTree", p)
print("DONE")
