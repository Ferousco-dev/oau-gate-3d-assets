"""Level_GateRun: the OAU gate, a long two-lane road with obstacles, a jump ramp, and the rocket roadster
animated driving down the right lane, weaving past obstacles, launching off the ramp and flying over the gate.
Run:  blender -b -P Level_GateRun/build_level.py
Units metres, Z up. The gate is at the origin facing -Y; traffic travels +Y (the car drives from the front, over the gate)."""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
GATE = os.path.join(ROOT, "AR_OAUGate/exports/AR_OAUGate.glb")
CAR = os.path.join(ROOT, "VH_RocketRoadster/exports/VH_RocketRoadster.glb")
PROPS = os.path.join(ROOT, "PR_RoadObstacles/exports/PR_RoadObstacles.glb")
ASPHALT = os.path.join(ROOT, "AR_OAUGate/textures/asphalt.png")
OUT = os.path.join(HERE, "output"); os.makedirs(OUT, exist_ok=True)

# ---- layout constants
LANE_X, LANE_W, MEDIAN_W = 3.65, 3.5, 3.8        # same as the gate's side passages
ROAD_Y0, ROAD_T, CURB_W, CURB_H = -300.0, 0.05, 1.5, 0.15
RAMP_Y0, RAMP_LEN, RAMP_H = -62.0, 8.0, 2.2
Y_LIP, Y_LAND = RAMP_Y0 + RAMP_LEN, 62.0
FPS, HOP, WHEEL_R = 30, 15.0, 0.34
V1, V2 = 38.0 / FPS, 30.0 / FPS                   # m per frame: approach / after landing (flight speed is derived)
FLIGHT_FRAMES = 83

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.fps = FPS


def new_col(name, hide=False):
    c = bpy.data.collections.new(name); sc.collection.children.link(c); c.hide_render = hide
    return c


C_GATE, C_CAR, C_ROAD, C_OBS = new_col("Gate"), new_col("Car"), new_col("Road"), new_col("Obstacles")
C_SRC = new_col("PropSources", hide=True); C_SRC.hide_viewport = True
C_SCN = new_col("Scenery")
C_DIST = new_col("Distractions")


def to_col(ob, c):
    for k in list(ob.users_collection):
        k.objects.unlink(ob)
    c.objects.link(ob)


def import_glb(path, c):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        to_col(o, c)
    drop = [o for o in new if o.name.startswith(("COL_", "SOCKET_"))]     # visual level only
    keep = [o for o in new if o not in drop]
    for o in drop:
        bpy.data.objects.remove(o, do_unlink=True)
    return keep


# ---------------------------------------------------------------- materials for road
def mat(name, color, rough=0.9):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1); b.inputs["Roughness"].default_value = rough
    for k in ("Specular IOR Level", "Specular"):
        if k in b.inputs: b.inputs[k].default_value = 0.1; break
    return m


M_ASPH = bpy.data.materials.new("Level_Asphalt"); M_ASPH.use_nodes = True
_b = M_ASPH.node_tree.nodes["Principled BSDF"]; _b.inputs["Roughness"].default_value = 1.0
for k in ("Specular IOR Level", "Specular"):
    if k in _b.inputs: _b.inputs[k].default_value = 0.1; break
_t = M_ASPH.node_tree.nodes.new("ShaderNodeTexImage"); _t.image = bpy.data.images.load(ASPHALT); _t.image.pack()
M_ASPH.node_tree.links.new(_t.outputs["Color"], _b.inputs["Base Color"])
M_WHITE, M_YEL = mat("Level_PaintWhite", (0.8, 0.8, 0.78), 0.7), mat("Level_PaintYellow", (0.75, 0.55, 0.05), 0.7)
M_CURB, M_GRASS = mat("Level_Curb", (0.45, 0.43, 0.40)), mat("Level_Median", (0.10, 0.28, 0.07), 0.95)
M_GROUND = mat("Level_Ground", (0.17, 0.22, 0.09), 1.0)


def mk_box(name, c, s, m, coll, uvtile=4.0):
    cx, cy, cz = c; sx, sy, sz = s
    vs = [(cx + x * sx / 2, cy + y * sy / 2, cz + z * sz / 2) for z in (-1, 1) for (x, y) in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    fs = [(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    uv = me.uv_layers.new(name="UVMap")
    for p in me.polygons:
        ax = max(range(3), key=lambda i: abs(p.normal[i]))
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            u, w = (v.y, v.z) if ax == 0 else (v.x, v.z) if ax == 1 else (v.x, v.y)
            uv.data[li].uv = (u / uvtile, w / uvtile)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); coll.objects.link(ob)
    return ob


# ---- road centreline: straight through the gate zone (y -75..80), winding S-curves before and after
def _sm(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


# Road 1 centreline traced from the OpenStreetMap screenshot (pixel coords, y down). Gate = first point.
TRACE_PX = [(112, 1065), (135, 1015), (160, 960), (190, 895), (222, 830), (255, 765), (288, 700), (316, 640), (332, 590),
            (318, 540), (298, 500), (262, 452), (235, 400), (205, 350), (175, 305), (150, 262), (132, 220), (124, 170),
            (126, 120), (140, 70), (150, 40)]
M_PER_PX = 1.5            # ASSUMED map scale (no scale bar in the screenshot); change to stretch or shrink the whole road
DS = 2.0                  # station spacing in metres
STRAIGHT_END = 80.0       # the gate zone (stations ROAD_Y0 .. 80) is dead straight; the traced curve starts after it


def _chaikin(pts, n):
    for _ in range(n):
        out = [pts[0]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            out += [(0.75 * x0 + 0.25 * x1, 0.75 * y0 + 0.25 * y1), (0.25 * x0 + 0.75 * x1, 0.25 * y0 + 0.75 * y1)]
        pts = out + [pts[-1]]
    return pts


def _build_centreline():
    px0, py0 = TRACE_PX[0]
    w = [((px - px0) * M_PER_PX, (py0 - py) * M_PER_PX) for px, py in TRACE_PX]
    w = _chaikin(w, 4)
    # resample by arc length
    seg, acc = [0.0], 0.0
    for (x0, y0), (x1, y1) in zip(w, w[1:]):
        acc += math.hypot(x1 - x0, y1 - y0); seg.append(acc)
    n = int(acc / DS); pts = []
    j = 0
    for i in range(n + 1):
        d = i * DS
        while j < len(seg) - 2 and seg[j + 1] < d: j += 1
        t = (d - seg[j]) / max(1e-9, seg[j + 1] - seg[j])
        pts.append((w[j][0] + t * (w[j + 1][0] - w[j][0]), w[j][1] + t * (w[j + 1][1] - w[j][1])))
    th = [math.atan2(pts[min(i + 1, n)][0] - pts[max(i - 1, 0)][0], pts[min(i + 1, n)][1] - pts[max(i - 1, 0)][1]) for i in range(n + 1)]
    th0 = th[0]; th = [t - th0 for t in th]
    k = 15                                                   # moving-average smoothing of the heading (+-30 m)
    th = [sum(th[max(0, i - k):i + k + 1]) / len(th[max(0, i - k):i + k + 1]) for i in range(n + 1)]
    th = [t * _sm(i * DS / 80.0) for i, t in enumerate(th)]  # ease the bend in over the first 80 m
    # full station table: straight lead-in, then the curve, integrated from heading
    ST, XS, YS, TH = [], [], [], []
    y = ROAD_Y0
    while y < STRAIGHT_END:
        ST.append(y); XS.append(0.0); YS.append(y); TH.append(0.0); y += DS
    x, yy = 0.0, STRAIGHT_END
    for i, t in enumerate(th):
        ST.append(STRAIGHT_END + i * DS); XS.append(x); YS.append(yy); TH.append(t)
        x += DS * math.sin(t); yy += DS * math.cos(t)
    return ST, XS, YS, TH


_ST, _XS, _YS, _TH = _build_centreline()
ROAD_Y1 = _ST[-1]
print("ROAD LENGTH", round(ROAD_Y1 - ROAD_Y0), "m; curve length", round(ROAD_Y1 - STRAIGHT_END), "m")


def _lk(y):
    f = (y - ROAD_Y0) / DS
    i = max(0, min(len(_ST) - 2, int(math.floor(f)))); t = f - i
    if y < ROAD_Y0 or y > _ST[-1]:                           # extrapolate straight along the end tangents
        t = max(-50.0, min(50.0, t)) if y < ROAD_Y0 else t
    th = _TH[i] + (_TH[i + 1] - _TH[i]) * max(0.0, min(1.0, t))
    cx = _XS[i] + (_XS[i + 1] - _XS[i]) * t; cy = _YS[i] + (_YS[i + 1] - _YS[i]) * t
    return cx, cy, th


def theta(y):
    return _lk(y)[2]


MED_D = 7.0                                                 # extra half-width of the median far from the gate (metres)


def _delta(y):
    return MED_D * _sm((y - 90.0) / 140.0)


def pos(lat, y):
    cx, cy, th = _lk(y)
    if lat:
        lat += math.copysign(_delta(y), lat)                 # everything outboard of the centreline slides out with the median
    return cx + lat * math.cos(th), cy - lat * math.sin(th)


def C(y):                                                   # kept for old call sites: world x of the centreline
    return _lk(y)[0]


def dC(y):
    return math.tan(theta(y))


def ribbon(name, a, b, h, m, y0, y1, step=2.0, uvtile=4.0):
    """strip between lateral offsets a..b from the centreline, top at height h, side walls down to 0"""
    ys = [y0 + i * step for i in range(int((y1 - y0) / step))] + [y1]
    vs, fs, ids = [], [], []
    for i, y in enumerate(ys):
        (xa, ya), (xb, yb) = pos(a, y), pos(b, y)
        vs += [(xa, ya, h), (xb, yb, h), (xa, ya, 0.0), (xb, yb, 0.0)]; ids += [(a, y), (b, y), (a, y), (b, y)]
        if i:
            k = 4 * (i - 1); n = 4 * i
            fs += [(k, k + 1, n + 1, n), (k + 2, k, n, n + 2), (k + 1, k + 3, n + 3, n + 1)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    uv = me.uv_layers.new(name="UVMap")
    for p_ in me.polygons:
        for li in p_.loop_indices:
            lat, st = ids[me.loops[li].vertex_index]
            uv.data[li].uv = (lat / uvtile, st / uvtile)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); C_ROAD.objects.link(ob)
    return ob


def build_road():
    gx0, gx1, gy0, gy1 = min(_XS) - 400, max(_XS) + 400, min(_YS) - 400, max(_YS) + 400
    mk_box("Level_Ground", ((gx0 + gx1) / 2, (gy0 + gy1) / 2, -0.06), (gx1 - gx0, gy1 - gy0, 0.1), M_GROUND, C_ROAD, 8.0)
    for s in (-1, 1):
        t = "L" if s < 0 else "R"
        lo, hi = sorted((s * (LANE_X - LANE_W / 2), s * (LANE_X + LANE_W / 2)))
        ribbon(f"Road_{t}", lo, hi, ROAD_T, M_ASPH, ROAD_Y0, ROAD_Y1)
        for xo in (LANE_X - LANE_W / 2 + 0.15, LANE_X + LANE_W / 2 - 0.15):
            ribbon(f"Edge_{t}_{int(xo*100)}", s * xo - 0.06, s * xo + 0.06, ROAD_T + 0.01, M_WHITE, ROAD_Y0, ROAD_Y1)
        k0, k1 = sorted((s * (LANE_X + LANE_W / 2), s * (LANE_X + LANE_W / 2 + CURB_W)))
        ribbon(f"CurbFront_{t}", k0, k1, CURB_H, M_CURB, ROAD_Y0, -3.5)
        ribbon(f"CurbRear_{t}", k0, k1, CURB_H, M_CURB, 12.0, ROAD_Y1)
    ribbon("Median", -MEDIAN_W / 2, MEDIAN_W / 2, 0.12, M_GRASS, ROAD_Y0, ROAD_Y1)


build_road()
M_DIRT = mat("Level_Laterite", (0.55, 0.27, 0.12), 1.0)
for sd in (-1, 1):
    k0, k1 = sorted((sd * (LANE_X + LANE_W / 2 + CURB_W), sd * (LANE_X + LANE_W / 2 + CURB_W + 3.0)))
    ribbon(f"Dirt_{sd}_a", k0, k1, 0.02, M_DIRT, ROAD_Y0, -8.0)
    ribbon(f"Dirt_{sd}_b", k0, k1, 0.02, M_DIRT, 16.0, ROAD_Y1)
f205 = mk_box("F205_Road", (0, 0, 0.02), (700, 14, 0.04), M_ASPH, C_ROAD)
f205.location = (0, -40, 0)
for yy_ in (-33.5, -46.5):
    ln_ = mk_box(f"F205_edge{yy_}", (0, 0, 0.045), (700, 0.14, 0.02), M_WHITE, C_ROAD); ln_.location = (0, yy_, 0)

# ---------------------------------------------------------------- imports
gate_objs = import_glb(GATE, C_GATE)
prop_objs = import_glb(PROPS, C_SRC)
car_objs = import_glb(CAR, C_CAR)
print("GATE dims", [round(v, 2) for v in Vector((max(o.dimensions.x for o in gate_objs if o.type == 'MESH'), 0, 0))],
      "gate mesh count", len([o for o in gate_objs if o.type == 'MESH']))
PROPS_BY = {o.name: o for o in prop_objs if o.type == "MESH"}
print("PROPS", sorted(PROPS_BY))


def place(prop, x, y, rotz=0.0, name=None):
    src = PROPS_BY[prop]
    ob = src.copy(); ob.data = src.data                      # linked mesh data = cheap instances
    ob.name = name or f"Obs_{prop}"
    wx_, wy_ = pos(x, y); ob.location = (wx_, wy_, 0); ob.rotation_euler = (0, 0, rotz - theta(y))
    C_OBS.objects.link(ob)
    return ob


# ---------------------------------------------------------------- obstacle layout
random.seed(11)
approach = [(-270, "PR_Barrel", -1), (-255, "PR_Cone", 1), (-240, "PR_TireStack", -1), (-225, "PR_Barrel", 1),
            (-210, "PR_Cone", -1), (-195, "PR_TireStack", 1), (-180, "PR_SpeedBump", 0), (-165, "PR_Barrel", -1),
            (-150, "PR_Cone", 1), (-135, "PR_TireStack", -1), (-120, "PR_Barrel", 1), (-105, "PR_SpeedBump", 0),
            (-92, "PR_Cone", -1), (-80, "PR_Barrel", 1)]
keys = [(ROAD_Y0, 0.0)]
for y, prop, side in approach:                              # car lane (right): obstacle on one side, car weaves to the other
    if prop == "PR_SpeedBump":
        place(prop, LANE_X, y)
        keys.append((y, keys[-1][1]))
        continue
    x = LANE_X + side * 0.95
    n = 3 if prop == "PR_Cone" else 1
    for i in range(n):
        place(prop, x, y + i * 1.2)
    keys.append((y + (n - 1) * 0.6, -side * 0.7))
keys.append((-72.0, 0.0))
place("PR_JumpRamp", LANE_X, RAMP_Y0, name="Obs_PR_JumpRamp")
for sx in (-1, 1):                                          # guide barriers beside the ramp
    place("PR_JerseyBarrier", LANE_X + sx * 2.1, RAMP_Y0 - 3.0)
    place("PR_JerseyBarrier", LANE_X + sx * 2.1, RAMP_Y0 - 6.0 - 0.1)

left = [(-250, "PR_CrateStack"), (-230, "PR_TireStack"), (-205, "PR_JerseyBarrier"), (-180, "PR_SpeedBump"),
        (-150, "PR_BrokenCar"), (-120, "PR_Barrel"), (-100, "PR_RoadBlock"), (-80, "PR_Cone"), (-55, "PR_BrokenCar"),
        (-35, "PR_CrateStack"), (75, "PR_RoadBlock"), (95, "PR_Barrel"), (110, "PR_CrateStack"), (130, "PR_BrokenCar"),
        (148, "PR_TireStack")]
for y, prop in left:
    n = 4 if prop in ("PR_Cone", "PR_Barrel") else 1
    for i in range(n):
        place(prop, -LANE_X + (i % 2) * 0.6 - 0.3, y + i * 1.3)
for y in (80, 100, 125, 145):                               # a few obstacles on the right lane AFTER the landing, off the car line
    place("PR_Barrel", LANE_X + 1.55, y); place("PR_Cone", LANE_X - 1.55, y + 3)

# ---------------------------------------------------------------- scenery, side roads, distractions
GA = os.path.join(ROOT, "Game_Assets")
NAT = os.path.join(GA, "downloads/nature/Models/GLTF format")
_cache = {}


def _g(path):
    return path if os.path.isabs(path) else os.path.join(GA, "exports", path + ".glb")


def put(asset, x, y, rotz=0.0, scale=1.0, coll=None, fresh=False, nat=False):
    """place an asset at lateral x, road station y (centreline-relative), following the curve"""
    coll = coll or C_SCN
    path = os.path.join(NAT, asset + ".glb") if nat else _g(asset)
    (wx, wy), wz = pos(x, y), 0.0
    yaw = rotz - theta(y)
    if not fresh and path in _cache and _cache[path] is not None:
        src = _cache[path]
        ob = src.copy(); ob.data = src.data; coll.objects.link(ob)
        roots = [ob]
    else:
        objs = import_glb(path, coll if fresh else C_SRC)
        roots = [o for o in objs if o.parent is None]
        meshes = [o for o in objs if o.type == "MESH"]
        if not fresh and len(objs) == 1 and len(meshes) == 1:
            _cache[path] = meshes[0]
            src = meshes[0]
            ob = src.copy(); ob.data = src.data; coll.objects.link(ob); roots = [ob]
        else:
            _cache[path] = None
            for o in objs:
                to_col(o, coll)
            if len(roots) > 1 or fresh:
                rt = bpy.data.objects.new(os.path.basename(path) + "_root", None); coll.objects.link(rt)
                for r in roots: r.parent = rt
                roots = [rt]
    for r in roots:
        r.location = (wx, wy, wz); r.rotation_euler = (0, 0, yaw); r.scale = (scale, scale, scale)
    return roots[0]


def side_road(y, side, length=45.0, width=5.0):
    """T-junction branch leaving the main road at station y on the given side (-1 left, +1 right)"""
    xe = side * (LANE_X + LANE_W / 2 + CURB_W)                # outer edge of the kerb
    cx = xe + side * length / 2
    ob = mk_box(f"SideRoad_{y}_{side}", (0, 0, ROAD_T / 2), (length, width, ROAD_T), M_ASPH, C_ROAD)
    ob.location = (*pos(cx, y), 0); ob.rotation_euler = (0, 0, -theta(y))
    ln = mk_box(f"SideLine_{y}_{side}", (0, 0, ROAD_T + 0.01), (length, 0.12, 0.02), M_YEL, C_ROAD)
    ln.location = (*pos(cx, y), 0); ln.rotation_euler = (0, 0, -theta(y))
    # gap in the kerb: paint a white stop line at the junction mouth
    st = mk_box(f"SideStop_{y}_{side}", (0, 0, ROAD_T + 0.01), (0.4, width, 0.02), M_WHITE, C_ROAD)
    st.location = (*pos(xe + side * 3.0, y), 0); st.rotation_euler = (0, 0, -theta(y))


for y, sd in ((-250, -1), (-175, 1), (-115, -1), (-70, 1), (105, -1), (140, 1)):
    side_road(y, sd)

KERB = LANE_X + LANE_W / 2 + CURB_W                          # 6.9 m from centre
rng = random.Random(5)
JUNC = {(-250, -1), (-175, 1), (-115, -1), (-70, 1), (105, -1), (140, 1)}


def near_junction(y, sd):
    return any(abs(y - jy) < 5 and sd == js for jy, js in JUNC)


for y in range(-296, int(ROAD_Y1) - 6, 7):
    if -16 < y < 22 or -50 < y < -30:
        continue                                          # keep the gate zone clear
    for sd in (-1, 1):
        if near_junction(y, sd):
            continue
        r = rng.random()
        if r < 0.5:
            put("plant_bush", sd * (KERB + 1.2 + rng.random() * 0.8), y + rng.random() * 4, rng.random() * 6.28, 1.8 + rng.random(), nat=True)
        elif r < 0.7:
            put("plant_bushLarge", sd * (KERB + 2.0), y, rng.random() * 6.28, 1.8, nat=True)
        elif r < 0.8:
            put("flower_redA", sd * (KERB + 1.0), y, 0, 3.0, nat=True)
for y in range(-292, int(ROAD_Y1) - 6, 14):
    if -20 < y < 26 or -50 < y < -30:
        continue
    for sd in (-1, 1):
        if near_junction(y, sd):
            continue
        t = rng.choice(["tree_palmTall", "tree_palmDetailedTall", "tree_fat", "tree_default", "tree_palmBend", "tree_tall"])
        put(t, sd * (KERB + 5.0 + rng.random() * 5), y + rng.random() * 6, rng.random() * 6.28, 3.0 + rng.random() * 1.5, nat=True)
for y in range(-290, int(ROAD_Y1) - 6, 42):                               # solar lamps both sides, alternating
    if -20 < y < 26 or -50 < y < -30: continue
    put("EN_SolarLamp", (KERB + 0.7) * (-1 if (y // 42) % 2 else 1), y, math.pi / 2 if (y // 42) % 2 else -math.pi / 2)
for y in (-100, 150):                                         # hedges along the verge
    for k in range(0, 60, 4):
        put("EN_Hedge", KERB + 1.2, y + k)
        put("EN_Hedge", -(KERB + 1.2), y + k)
put("EN_WelcomeBillboard", -(KERB + 5), -285, 0)
put("EN_BusStop", KERB + 4.5, -150, math.pi / 2); put("EN_BusStop", -(KERB + 4.5), 60, -math.pi / 2)
put("EN_Kiosk", KERB + 5, -200, math.pi / 2); put("EN_Kiosk", -(KERB + 5), 20 + 70, -math.pi / 2)
put("EN_MarketStall", -(KERB + 3.5), -215, -math.pi / 2); put("EN_MarketStall", KERB + 3.5, -130, math.pi / 2); put("EN_MarketStall", KERB + 3.5, -126, math.pi / 2)
put("EN_SlowSign", KERB + 0.8, -230, math.pi / 2); put("EN_SlowSign", -(KERB + 0.8), 40, -math.pi / 2)
for y, sd in ((-280, 1), (-210, -1), (-140, 1), (-90, -1), (-60, 1), (100, 1), (130, -1)):
    put("EN_HostelBlock", sd * (KERB + 22), y, math.pi / 2 * (-sd))
put("EN_LectureHall", KERB + 24, 40, -math.pi / 2); put("EN_LectureHall", -(KERB + 24), -40, math.pi / 2)
for y, nm in ((-160, "RD_Zebra"), (112, "RD_Zebra"), (-205, "RD_Zebra")):
    for sd in (-1, 1):
        z = put(nm, sd * LANE_X, y, 0.0, scale=0.46, coll=C_ROAD)

# distractions: roadside and on the road edges (behaviour is game logic; here they are placed and posed)
for y, sd in ((-265, 1), (-185, -1), (-135, 1), (-100, -1), (-68, 1), (-45, -1), (95, 1), (125, -1)):
    put("CH_DancingGirl", sd * (KERB + 1.6), y, math.pi / 2 * sd * -1 + math.pi, 1.0, coll=C_DIST, fresh=True)
for y, sd in ((-262, -1), (-190, 1), (-125, -1), (-70, 1)):
    put("EN_PartySpeaker", sd * (KERB + 3.2), y, -sd * math.pi / 2, 1.0, coll=C_DIST)
for y, xo in ((-220, 1.35), (-170, -1.4), (-143, 1.35), (-112, -1.4), (-86, 1.35)):        # stubborns reaching in from the lane edge
    put("CH_Stubborn", LANE_X + xo, y, math.pi if xo > 0 else math.pi, 1.0, coll=C_DIST, fresh=True)
for y in (-245, -158, 118):                                  # hawkers crossing the road
    put("CH_Hawker", LANE_X - 1.4, y, math.pi / 2, 1.0, coll=C_DIST, fresh=True)
for y in (-195, -55, 90):
    put("CH_Lecturer", KERB + 0.9, y, math.pi / 2, 1.0, coll=C_DIST, fresh=True)

# parked buses east of the gate (as in the satellite image) and a deeper forest belt along the whole road
for i in range(14):
    put("VH_GboroBus", 26 + (i % 3) * 5.5 + rng.random(), 6 + (i // 3) * 8.5, math.pi / 2 + (rng.random() - 0.5) * 0.4, 1.0, coll=C_DIST)
for y in range(-290, int(ROAD_Y1) - 6, 10):
    if -50 < y < 30: continue
    for sd in (-1, 1):
        t = rng.choice(["tree_tall", "tree_default", "tree_fat", "tree_detailed", "tree_palmTall", "tree_tall_dark"])
        put(t, sd * (KERB + 16 + rng.random() * 26), y + rng.random() * 8, rng.random() * 6.28, 3.4 + rng.random() * 2.0, nat=True)

# ---- the end of the road: Road 2 junction, graduation arch, Student Union (placeholder), sports complex
E = ROAD_Y1
r2 = mk_box("Road2_Cross", (0, 0, 0.02), (700, 14, 0.04), M_ASPH, C_ROAD)
r2.location = (*pos(0, E - 12), 0); r2.rotation_euler = (0, 0, -theta(E - 12))
put("EN_GraduationArch", 0, E - 110, 0.0, 1.0, coll=C_DIST)
put(os.path.join(ROOT, "AR_StudentUnion/exports/AR_StudentUnion.glb"), 92, E - 30, -math.pi / 2, 1.0, coll=C_DIST)
put("EN_MainBowl", -118, E - 150, math.pi / 2, 1.0, coll=C_DIST)
put("EN_SwimPool", -52, E - 60, 0.0, 1.0, coll=C_DIST)
put("EN_TennisCourts", -52, E - 100, math.pi / 2, 1.0, coll=C_DIST)

# median planting (palms and mango trees) and local traffic: keke napep and danfo
for y in range(130, int(ROAD_Y1) - 60, 22):
    put("tree_palmTall", 0, y, rng.random() * 6.28, 3.4 + rng.random() * 0.8, nat=True)
    put("plant_bushLarge", 0, y + 11, rng.random() * 6.28, 2.2, nat=True)
for y in range(160, int(ROAD_Y1) - 80, 70):
    put("EN_MangoTree", 0, y + 5, rng.random() * 6.28, 1.0)
for y in (-232, -168, -118, -54, 150, 260, 420, 600):                       # oncoming (outbound) traffic on the left carriageway
    put("VH_Danfo" if (y // 7) % 2 else "VH_KekeNapep", -LANE_X + rng.uniform(-0.6, 0.6), y, 0.0, 1.0, coll=C_DIST)
for y in (-205, -95, 190, 330, 510):                                        # broken down / stopped on the car's carriageway edge
    put("VH_KekeNapep" if (y // 5) % 2 else "VH_Danfo", LANE_X + (1.1 if y % 2 else -1.1), y, math.pi + rng.uniform(-0.1, 0.1), 1.0, coll=C_DIST)
for y in (-140, 40 + 60, 240, 380):                                         # parked on the dirt shoulder
    put("VH_KekeNapep", KERB + 2.2, y, math.pi / 2, 1.0, coll=C_DIST); put("VH_Danfo", -(KERB + 2.4), y + 12, -math.pi / 2, 1.0, coll=C_DIST)


# main-campus roundabout at the end of Road 1 (oval lawn island, ring road, kerb), as in the campus aerial photo
def ring_mesh(name, rl0, ra0, rl1, ra1, h, m, centre_station, n=64):
    cx, cy, th = _lk(centre_station)
    def pt(lx, ly): return (cx + lx * math.cos(th) + ly * math.sin(th), cy - lx * math.sin(th) + ly * math.cos(th))
    vs, fs, uvs = [], [], []
    for i in range(n):
        a = 2 * math.pi * i / n; ca, sa = math.cos(a), math.sin(a)
        vs += [(*pt(rl0 * ca, ra0 * sa), h), (*pt(rl1 * ca, ra1 * sa), h)]
    for i in range(n):
        j = (i + 1) % n; fs.append((2 * i, 2 * i + 1, 2 * j + 1, 2 * j))
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    uv = me.uv_layers.new(name="UVMap")
    for p_ in me.polygons:
        for li in p_.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (v.x / 6.0, v.y / 6.0)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); C_ROAD.objects.link(ob); return ob


def oval_mesh(name, rl, ra, h, m, centre_station, n=64):
    cx, cy, th = _lk(centre_station)
    vs = [(cx, cy, h)] + [(cx + rl * math.cos(2 * math.pi * i / n) * math.cos(th) + ra * math.sin(2 * math.pi * i / n) * math.sin(th),
                           cy - rl * math.cos(2 * math.pi * i / n) * math.sin(th) + ra * math.sin(2 * math.pi * i / n) * math.cos(th), h) for i in range(n)]
    fs = [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.update()
    uv = me.uv_layers.new(name="UVMap")
    for p_ in me.polygons:
        for li in p_.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co; uv.data[li].uv = (v.x / 6.0, v.y / 6.0)
    ob = bpy.data.objects.new(name, me); ob.data.materials.append(m); C_ROAD.objects.link(ob); return ob


RB = E - 48
ring_mesh("Roundabout_Ring", 38, 26, 50, 38, ROAD_T + 0.01, M_ASPH, RB)
ring_mesh("Roundabout_Kerb", 36.6, 24.6, 38, 26, 0.2, M_CURB, RB)
oval_mesh("Roundabout_Lawn", 36.6, 24.6, 0.19, M_GRASS, RB)
put("tree_fat", 0, RB, 0.0, 6.0, nat=True)
for k in range(10):
    a = 2 * math.pi * k / 10
    put("plant_bushLarge", 30 * math.cos(a), RB + 19 * math.sin(a), 0.0, 3.0, nat=True)

# ---------------------------------------------------------------- car rig
root = bpy.data.objects.new("Car_Root", None); root.empty_display_type = "ARROWS"; C_CAR.objects.link(root)
cparts = [o for o in car_objs if o.type == "MESH"]
for o in cparts:
    o.parent = root
wheels = [o for o in cparts if "Tire_" in o.name or "Rim_" in o.name]
flames = [o for o in cparts if "Flame" in o.name]
for o in flames:                                            # put the origin at the nozzle so scale.y grows the flame outward
    fl = o.dimensions.y
    o.data.transform(Matrix.Translation((0, fl / 2, 0)))
    o.location.y -= fl / 2

# ---------------------------------------------------------------- path
def smooth(t):
    t = max(0.0, min(1.0, t)); return t * t * (3 - 2 * t)


def lane_x(y):
    if y >= -60:
        return LANE_X
    for (y0, o0), (y1, o1) in zip(keys, keys[1:]):
        if y0 <= y <= y1:
            return LANE_X + o0 + (o1 - o0) * smooth((y - y0) / max(1e-6, y1 - y0))
    return LANE_X


path = []                                                   # (x, y, z) per frame, frame 1 = index 0
y = ROAD_Y0 + 10.0
while y < Y_LIP:
    z = RAMP_H * max(0.0, (y - RAMP_Y0) / RAMP_LEN) if y > RAMP_Y0 else 0.0
    path.append((*pos(lane_x(y), y), z)); y += V1
F_LIP = len(path)
for i in range(1, FLIGHT_FRAMES + 1):
    u = i / FLIGHT_FRAMES
    path.append((LANE_X, Y_LIP + (Y_LAND - Y_LIP) * u, RAMP_H * (1 - u) + HOP * 4 * u * (1 - u)))
y = Y_LAND + V2
while y < ROAD_Y1 - 25:
    path.append((*pos(LANE_X, y), 0.0)); y += V2
N = len(path)
print("frames", N, "launch frame", F_LIP)


def avg(vals, i, w=4):
    lo, hi = max(0, i - w), min(len(vals) - 1, i + w); return sum(vals[lo:hi + 1]) / (hi - lo + 1)


pitch_raw = [math.atan2(path[min(N - 1, i + 1)][2] - path[max(0, i - 1)][2], path[min(N - 1, i + 1)][1] - path[max(0, i - 1)][1]) for i in range(N)]
yaw_raw = [math.atan2(path[min(N - 1, i + 1)][0] - path[max(0, i - 1)][0], path[min(N - 1, i + 1)][1] - path[max(0, i - 1)][1]) for i in range(N)]
dist = 0.0
sc.frame_start, sc.frame_end = 1, N
for i, (x, yy, z) in enumerate(path):
    f = i + 1
    if i:
        dist += math.dist(path[i], path[i - 1])
    root.location = (x, yy, z)
    root.rotation_euler = (-avg(pitch_raw, i), 0.0, math.pi - avg(yaw_raw, i))   # nose is local -Y; yaw pi makes the car face +Y
    root.keyframe_insert("location", frame=f); root.keyframe_insert("rotation_euler", frame=f)
    for w in wheels:
        w.rotation_euler = (dist / WHEEL_R, 0, 0); w.keyframe_insert("rotation_euler", frame=f)
    # rocket: ignite 12 frames before the lip, burn through the flight, fade out 25 frames after landing
    on = (F_LIP - 12) <= i <= (F_LIP + FLIGHT_FRAMES + 25)
    flick = 0.85 + 0.3 * random.random()
    for o in flames:
        k = 1.0 if on else 0.0
        if on and i > F_LIP + FLIGHT_FRAMES:
            k = max(0.0, 1.0 - (i - F_LIP - FLIGHT_FRAMES) / 25.0)
        if i < F_LIP - 12 or i > F_LIP + FLIGHT_FRAMES + 25:
            k = 0.0
        if on and i < F_LIP:
            k = min(1.0, (i - (F_LIP - 12)) / 12.0 + 0.1)
        o.scale = (1.0, max(0.001, k * flick), 1.0); o.keyframe_insert("scale", frame=f)
for obj in [root] + wheels + flames:
    if obj.animation_data and obj.animation_data.action:
        for fc in obj.animation_data.action.fcurves if hasattr(obj.animation_data.action, "fcurves") else []:
            for kp in fc.keyframe_points:
                kp.interpolation = "LINEAR"
if root.animation_data and root.animation_data.action:
    root.animation_data.action.name = "Jump_Over_Gate"

# ---------------------------------------------------------------- lights, cameras (not exported)
w = bpy.data.worlds.new("Sky"); sc.world = w
bg = w.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.5, 0.7, 1.0, 1); bg.inputs["Strength"].default_value = 1.0
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 3.0
sob = bpy.data.objects.new("Sun", sun); sc.collection.objects.link(sob); sob.rotation_euler = (math.radians(50), math.radians(10), math.radians(-30))
cd = bpy.data.cameras.new("CamGate"); cd.lens = 35
cam = bpy.data.objects.new("CamGate", cd); sc.collection.objects.link(cam); cam.location = (-30, -34, 11)
tc = cam.constraints.new("TRACK_TO"); tc.target = root; tc.track_axis = "TRACK_NEGATIVE_Z"; tc.up_axis = "UP_Y"
cd2 = bpy.data.cameras.new("CamChase"); cd2.lens = 28
cam2 = bpy.data.objects.new("CamChase", cd2); sc.collection.objects.link(cam2); cam2.parent = root
cam2.location = (0, 9.0, 3.6); cam2.rotation_euler = (math.radians(80), 0, math.pi)
cd3 = bpy.data.cameras.new("CamTop"); cd3.type = "ORTHO"; cd3.ortho_scale = max(max(_XS) - min(_XS), max(_YS) - min(_YS)) * 1.15 + 200
cam3 = bpy.data.objects.new("CamTop", cd3); sc.collection.objects.link(cam3); cam3.location = ((max(_XS) + min(_XS)) / 2, (max(_YS) + min(_YS)) / 2, 1500); cam3.rotation_euler = (0, 0, 0)
for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "CYCLES"):
    try: sc.render.engine = eng; break
    except TypeError: pass
sc.render.resolution_x, sc.render.resolution_y = 1280, 720
cd3.clip_end = 5000
try: sc.view_settings.view_transform = "Standard"
except Exception: pass

# natural colours for the Kenney nature materials (their palette is stylised teal)
for m_ in bpy.data.materials:
    n_ = m_.name.lower(); b_ = m_.node_tree.nodes.get("Principled BSDF") if m_.use_nodes and m_.node_tree else None
    if not b_: continue
    col = None
    if "leafsgreen" in n_ or n_.startswith("leafs") and "dark" not in n_ and "red" not in n_ and "yellow" not in n_ and "orange" not in n_:
        col = (0.10, 0.42, 0.10)
    elif "dark" in n_ and "leaf" in n_:
        col = (0.05, 0.27, 0.07)
    elif "woodbark" in n_:
        col = (0.33, 0.2, 0.1)
    if col:
        b_.inputs["Base Color"].default_value = (*col, 1)
        print("RECOLOR", m_.name)

# ---------------------------------------------------------------- realism pass (PBR textures, HDRI sky, AgX, haze, ray-traced AO)
PBR = os.path.join(GA, "downloads/pbr")


def pbr(mat_name, folder, tint=None):
    m = bpy.data.materials.get(mat_name)
    if not m: return
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    for n in [n for n in nt.nodes if n.type in ("TEX_IMAGE", "NORMAL_MAP", "SEPARATE_COLOR", "MIX")]:
        nt.nodes.remove(n)

    def img(suffix, cs):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(f"{PBR}/{folder}/{folder}_1K-JPG_{suffix}.jpg", check_existing=True)
        n.image.colorspace_settings.name = cs; n.image.pack(); return n
    c, r, nrm = img("Color", "sRGB"), img("Roughness", "Non-Color"), img("NormalGL", "Non-Color")
    if tint:
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "MULTIPLY"
        mx.inputs[0].default_value = 1.0; mx.inputs[7].default_value = (*tint, 1)
        nt.links.new(c.outputs["Color"], mx.inputs[6]); nt.links.new(mx.outputs[2], b.inputs["Base Color"])
    else:
        nt.links.new(c.outputs["Color"], b.inputs["Base Color"])
    sep = nt.nodes.new("ShaderNodeSeparateColor"); nt.links.new(r.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 1.0
    nt.links.new(nrm.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    print("PBR", mat_name, "<-", folder)


for name_, folder_, tint_ in (("Level_Asphalt", "Asphalt031", None), ("Level_Median", "Grass004", None), ("Level_Ground", "Ground037", None),
                              ("Level_Laterite", "Ground037", (1.0, 0.42, 0.22)), ("Level_Curb", "Concrete034", (0.9, 0.9, 0.88))):
    try:
        pbr(name_, folder_, tint_)
    except Exception as e_:
        print("PBR FAIL", name_, e_)

# sky: real HDRI for light and reflections, plus faint haze for depth
try:
    wnt = sc.world.node_tree
    for n_ in list(wnt.nodes): wnt.nodes.remove(n_)
    out_ = wnt.nodes.new("ShaderNodeOutputWorld"); bgn = wnt.nodes.new("ShaderNodeBackground")
    env = wnt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(os.path.join(PBR, "sky_kloofendal_clear_1k.hdr"))
    wnt.links.new(env.outputs["Color"], bgn.inputs["Color"]); wnt.links.new(bgn.outputs["Background"], out_.inputs["Surface"])
    bgn.inputs["Strength"].default_value = 1.0
except Exception as e_:
    print("SKY FAIL", e_)
sob.data.energy = 3.0; sob.data.angle = math.radians(0.6)
sob.rotation_euler = (math.radians(47), 0, math.radians(35))
for vt in ("AgX", "Filmic", "Standard"):
    try: sc.view_settings.view_transform = vt; break
    except TypeError: pass
try: sc.view_settings.look = "None"
except Exception: pass
sc.view_settings.exposure = 0.0
for attr, val in (("use_raytracing", True), ("use_gtao", True), ("taa_render_samples", 32), ("use_volumetric_shadows", False)):
    try: setattr(sc.eevee, attr, val)
    except Exception as e_: print("EEVEE skip", attr)
for cam_ in (cd, cd2):
    try:
        cam_.sensor_width = 36; cam_.dof.use_dof = False
    except Exception: pass

# ---------------------------------------------------------------- export level (visual + animation, no helpers)
bpy.ops.object.select_all(action="DESELECT")
for c in (C_GATE, C_ROAD, C_OBS, C_CAR, C_SCN, C_DIST):
    for o in c.all_objects:
        o.select_set(True)
bpy.context.view_layer.objects.active = root
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, "Level_GateRun.glb"), export_format="GLB", use_selection=True,
                          export_apply=True, export_animations=True)

# ---------------------------------------------------------------- stills at key moments
stills = [("approach", F_LIP - 40, cam), ("launch", F_LIP + 2, cam), ("climb", F_LIP + 28, cam), ("over_gate", F_LIP + 39, cam),
          ("descent", F_LIP + 62, cam), ("landed", F_LIP + FLIGHT_FRAMES + 12, cam),
          ("chase_launch", F_LIP + 4, cam2), ("chase_gate", F_LIP + 39, cam2), ("chase_ramp", F_LIP - 14, cam2),
          ("top_overview", 60, cam3), ("closeup_scene", 100, cam), ("chase_curve1", 45, cam2), ("chase_curve2", 120, cam2), ("chase_curve3", N - 70, cam2), ("finish_chase", N - 5, cam2), ("finish_view", N - 5, cam)]
for name, f, c in stills:
    sc.frame_set(max(1, min(N, f))); sc.camera = c
    sc.render.filepath = os.path.join(OUT, f"still_{name}.png"); bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action="DESELECT")
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "Level_GateRun.blend"))
print("DONE frames", N)
