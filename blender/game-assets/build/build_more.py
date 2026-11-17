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


def dancing_girl():
    root, P = rig_person("CH_DancingGirl", PINK, None, DSKIN, BLACK, skirt=PURPLE)
    sc.frame_start, sc.frame_end = 1, 48
    for f, (sway, bob, al, ar) in {1: (-0.25, 0, 2.6, 0.5), 13: (0, 0.06, 2.0, 1.2), 25: (0.25, 0, 0.5, 2.6), 37: (0, 0.06, 1.2, 2.0), 49: (-0.25, 0, 2.6, 0.5)}.items():
        key(root, f, rotation_euler=(0, 0, sway), location=(0, 0, bob))
        key(P["armL"], f, rotation_euler=(0, al - 3.1, 0)); key(P["armR"], f, rotation_euler=(0, -(ar - 3.1) * -1 + 0, 0))
    sc.frame_end = 49
    export([root] + list(P.values()), "CH_DancingGirl", anim=True)
    return root


def stubborn():
    root, P = rig_person("CH_Stubborn", mat("stub_shirt", (0.55, 0.1, 0.1)), mat("stub_pants", (0.2, 0.2, 0.22)), SKIN, BLACK)
    for f, (lean, a, bob) in {1: (0.0, 0.0, 0.0), 7: (0.25, -1.5, 0.08), 13: (0.0, -0.4, 0.0), 19: (0.25, -1.5, 0.08), 25: (0.0, 0.0, 0.0)}.items():
        key(root, f, rotation_euler=(-lean, 0, 0), location=(0, 0, bob))
        key(P["armL"], f, rotation_euler=(a, 0, 0)); key(P["armR"], f, rotation_euler=(a, 0, 0))
        key(P["legL"], f, rotation_euler=(lean, 0, 0)); key(P["legR"], f, rotation_euler=(-lean, 0, 0))
    sc.frame_end = 25
    export([root] + list(P.values()), "CH_Stubborn", anim=True)


def hawker():
    root, P = rig_person("CH_Hawker", mat("h_top", (0.1, 0.55, 0.4)), None, DSKIN, mat("wrap", (0.9, 0.5, 0.1)), skirt=mat("wrapper", (0.15, 0.3, 0.7)))
    tray = prim("box", "tray", (0.7, 0.5, 0.06), (0, 0, 1.78), GREY)
    P["sachets"] = prim("box", "sachets", (0.6, 0.4, 0.28), (0, 0, 1.96), mat("sachet", (0.5, 0.8, 1.0), 0.3))
    P["tray"] = tray
    for k in ("tray", "sachets"): P[k].parent = root
    export([root] + list(P.values()), "CH_Hawker", anim=False)


def lecturer():
    root, P = rig_person("CH_Lecturer", mat("lec_shirt", (0.85, 0.85, 0.8)), mat("lec_pants", (0.15, 0.15, 0.2)), SKIN, mat("grey_hair", (0.6, 0.6, 0.6)))
    P["tie"] = prim("box", "tie", (0.07, 0.02, 0.35), (0, -0.13, 1.05), RED)
    P["glasses"] = prim("box", "glasses", (0.3, 0.03, 0.05), (0, -0.16, 1.56), BLACK)
    P["handout"] = prim("box", "handout", (0.4, 0.28, 0.18), (0.33, -0.18, 0.95), mat("paper", (0.92, 0.9, 0.8)))
    for k in ("tie", "glasses", "handout"): P[k].parent = root
    export([root] + list(P.values()), "CH_Lecturer")


def static_assets():
    out = []

    def add(name, parts): out.append(finish(name, parts))
    # bush and hedge
    add("EN_Bush", [prim("sph", "b1", (0.7,), (0, 0, 0.6), GREEN, seg=8), prim("sph", "b2", (0.55,), (0.6, 0.2, 0.45), DGREEN, seg=8), prim("sph", "b3", (0.5,), (-0.55, -0.1, 0.4), GREEN, seg=8)])
    add("EN_Hedge", [prim("box", "h", (4.0, 0.9, 0.9), (0, 0, 0.45), DGREEN)] + [prim("sph", f"t{i}", (0.55,), (-1.6 + i * 0.8, 0, 0.9), GREEN, seg=6) for i in range(5)])
    # solar street lamp
    add("EN_SolarLamp", [prim("cyl", "pole", (0.07, 6.0), (0, 0, 3.0), GREY, seg=8), prim("box", "arm", (1.2, 0.1, 0.1), (0.55, 0, 6.0), GREY),
                         prim("box", "panel", (1.0, 0.7, 0.06), (0, 0, 6.35), mat("solar", (0.05, 0.1, 0.3), 0.3), rot=(0.4, 0, 0)), prim("box", "lamp", (0.4, 0.2, 0.08), (1.1, 0, 5.92), YEL)])
    # billboard
    add("EN_WelcomeBillboard", [prim("cyl", "p1", (0.1, 4.0), (-2.0, 0, 2.0), GREY, seg=8), prim("cyl", "p2", (0.1, 4.0), (2.0, 0, 2.0), GREY, seg=8),
                                prim("box", "board", (5.0, 0.15, 2.0), (0, 0, 4.4), GREEN), text("w1", "WELCOME TO OAU", 0.5, (0, -0.1, 4.6), WHITE), text("w2", "AWOLOWO HALL THIS WAY", 0.28, (0, -0.1, 4.0), YEL)])
    # bus stop
    add("EN_BusStop", [prim("box", "roof", (3.2, 1.6, 0.12), (0, 0, 2.5), BLUE), prim("box", "p1", (0.1, 0.1, 2.5), (-1.5, 0.6, 1.25), GREY), prim("box", "p2", (0.1, 0.1, 2.5), (1.5, 0.6, 1.25), GREY),
                       prim("box", "back", (3.0, 0.06, 1.4), (0, 0.7, 1.4), mat("glass", (0.4, 0.6, 0.7), 0.2)), prim("box", "bench", (2.4, 0.5, 0.1), (0, 0.4, 0.5), mat("wood", (0.4, 0.25, 0.1))),
                       text("bs", "GBORO", 0.3, (0, -0.8, 2.5), WHITE)])
    # mammy market stall with umbrella
    add("EN_MarketStall", [prim("box", "table", (2.2, 1.0, 0.9), (0, 0, 0.45), mat("wood", (0.4, 0.25, 0.1))), prim("cyl", "pole", (0.05, 2.4), (0, 0.4, 1.2), GREY, seg=6),
                           prim("cyl", "umb", (1.7, 0.12), (0, 0.4, 2.45), RED, seg=10)] + [prim("sph", f"fr{i}", (0.16,), (-0.8 + i * 0.4, -0.1, 1.0), ORANGE if i % 2 else GREEN, seg=6) for i in range(5)])
    # party speaker stack
    add("EN_PartySpeaker", [prim("box", "s1", (1.0, 0.8, 1.6), (-0.7, 0, 0.8), BLACK), prim("box", "s2", (1.0, 0.8, 1.6), (0.7, 0, 0.8), BLACK),
                            prim("cyl", "w1", (0.32, 0.1), (-0.7, -0.42, 0.5), GREY, rot=(math.pi / 2, 0, 0)), prim("cyl", "w2", (0.32, 0.1), (0.7, -0.42, 0.5), GREY, rot=(math.pi / 2, 0, 0)),
                            prim("cyl", "w3", (0.2, 0.1), (-0.7, -0.42, 1.2), GREY, rot=(math.pi / 2, 0, 0)), prim("cyl", "w4", (0.2, 0.1), (0.7, -0.42, 1.2), GREY, rot=(math.pi / 2, 0, 0)),
                            text("dj", "DJ NIGHT", 0.3, (0, -0.42, 1.75), mat("neon", (1, 0.2, 0.7), 0.3))])
    # kiosk
    add("EN_Kiosk", [prim("box", "k", (2.2, 1.8, 2.2), (0, 0, 1.1), mat("kiosk", (0.1, 0.5, 0.7))), prim("box", "win", (1.4, 0.06, 0.8), (0, -0.92, 1.3), mat("glass", (0.4, 0.6, 0.7), 0.2)),
                     prim("box", "roof", (2.5, 2.1, 0.15), (0, 0, 2.25), RED), text("kt", "RECHARGE CARD", 0.2, (0, -0.95, 1.9), WHITE)])
    # hostel block (cream, modernist, window grid) 14 x 8 x 10
    parts = [prim("box", "body", (14, 8, 10), (0, 0, 5), CREAM), prim("box", "slab", (14.6, 8.6, 0.4), (0, 0, 10.2), mat("slab", (0.6, 0.58, 0.5)))]
    win = mat("win", (0.2, 0.3, 0.4), 0.3)
    for fl in range(3):
        for i in range(6):
            parts.append(prim("box", f"w{fl}{i}", (1.2, 0.1, 1.1), (-5.5 + i * 2.2, -4.02, 2.0 + fl * 3.0), win))
    parts.append(prim("box", "door", (1.8, 0.12, 2.2), (0, -4.02, 1.1), BLACK))
    parts.append(text("hn", "ANGOLA HALL", 0.6, (0, -4.1, 9.2), mat("sign", (0.15, 0.3, 0.15))))
    add("EN_HostelBlock", parts)
    # lecture hall (long low, brise-soleil)
    parts = [prim("box", "body", (18, 9, 6), (0, 0, 3), mat("conc", (0.7, 0.68, 0.62))), prim("box", "roof", (19, 10, 0.4), (0, 0, 6.2), GREY)]
    for i in range(12):
        parts.append(prim("box", f"fin{i}", (0.25, 0.9, 5.0), (-8.25 + i * 1.5, -4.9, 3.0), CREAM))
    parts.append(text("lh", "LECTURE THEATRE", 0.55, (0, -5.4, 5.7), mat("sign2", (0.15, 0.2, 0.4))))
    add("EN_LectureHall", parts)
    # zebra crossing decal (flat) 7.2 wide x 3 long
    add("RD_Zebra", [prim("box", f"z{i}", (0.5, 3.0, 0.03), (-3.2 + i * 0.9, 0, 0.065), WHITE) for i in range(8)])
    # "slow down" sign
    add("EN_SlowSign", [prim("cyl", "p", (0.05, 2.2), (0, 0, 1.1), GREY, seg=6), prim("cyl", "d", (0.5, 0.06), (0, -0.04, 2.3), RED, rot=(math.pi / 2, 0, 0)),
                        prim("cyl", "d2", (0.38, 0.07), (0, -0.05, 2.3), WHITE, rot=(math.pi / 2, 0, 0)), text("sp", "30", 0.3, (0, -0.1, 2.3), BLACK)])
    for o in out:
        export([o], o.name)


dancing_girl(); stubborn(); hawker(); lecturer(); static_assets()
print("DONE")
