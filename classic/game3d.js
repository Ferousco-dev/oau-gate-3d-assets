import * as THREE from "./vendor/three.module.js";
import { GLTFLoader } from "./vendor/jsm/loaders/GLTFLoader.js";
import { DRACOLoader } from "./vendor/jsm/loaders/DRACOLoader.js";
import { createSfx } from "./sfx.js";
import { mergeGeometries } from "./vendor/jsm/utils/BufferGeometryUtils.js";

/* ================= tuning ================= */
const LOBBY_S = 255;                                    // station on the road where you stand before the gate
const CRUISE = 33, CHASE0 = 29, CHASE1 = 33.5;          // m/s: your car, chaser at the start, chaser at the end
const BOOST_MULT = 1.4;
const LAT_MIN = -8.5, LAT_MAX = 9.5;
const GAP_Y = 36, GAP_W = 56, CAUGHT_GAP = 7, GATE_S = 300, INTRO_END = 332;
const CAR_SCALE = 0.72, CAR_HW = 0.8, CAR_HL = 2.4;     // smaller car so the road feels wider
const HIT = {                                           // radius (m), CGPA lost, note
  Obs_PR_Barrel: [0.8, 0.05, "Barrel!"], Obs_PR_Cone: [0.5, 0.02, "Cone!"], Obs_PR_TireStack: [1.2, 0.08, "Tyres!"],
  Obs_PR_CrateStack: [1.4, 0.1, "Crates!"], Obs_PR_BrokenCar: [2.3, 0.15, "Broken car!"], Obs_PR_JerseyBarrier: [2.0, 0.1, "Barrier!"],
  Obs_PR_RoadBlock: [2.3, 0.15, "Road block!"], Obs_PR_SpeedBump: [1.7, 0.02, "Speed bump"],
  VH_KekeNapep: [1.6, 0.1, "Keke!"], VH_Danfo: [2.4, 0.12, "Danfo!"],
  CH_Hawker: [0.9, 0.08, "Oops, hawker!"], CH_Lecturer: [0.9, 0.1, "Lecturer! Handout fine"], CH_Stubborn: [1.1, 0.0, "STUBBORN grab!"],
};
const POOLS = [                                         // what can appear, unlocked as you go
  { from: 0.0, names: ["Obs_PR_Cone", "Obs_PR_Barrel", "Obs_PR_TireStack"] },
  { from: 0.22, names: ["Obs_PR_CrateStack", "Obs_PR_JerseyBarrier", "VH_KekeNapep", "CH_Hawker", "CH_Lecturer"] },
  { from: 0.5, names: ["Obs_PR_BrokenCar", "Obs_PR_RoadBlock", "VH_Danfo", "CH_Stubborn"] },
];
const HAWKERS = [
  { name: "Mama Tola", line: "Ticket! Ticket! Last one!" }, { name: "Baba Rasaq", line: "CGPA 5.0 ticket, fresh!" },
  { name: "Sister Bisi", line: "Come buy before e finish!" }, { name: "Mallam Ali", line: "Ticket for gate, oga!" },
  { name: "Aunty Kemi", line: "Ticket! Ticket! Ticket!" },
];
const BASE = "assets/";
const $ = (id) => document.getElementById(id);
const rnd = (a, b) => a + Math.random() * (b - a), pick = (a) => a[(Math.random() * a.length) | 0];

/* ================= module state ================= */
let sun, skyDome, host, renderer, scene, camera, world, dyn, crowdG, car, carModel, flame, shadow, yellow, white;
let D, P, L, A;                                         // level data, path points, path length, assets
let mode = "boot", paused = false, muted = false;
let things = [], lvlThings = [], srcs = {}, ramp = null, picks = [], hawkers = [], walkers = [];
const st = { s: LOBBY_S, u: 1.75, uT: 1.75, v: 0, cgpa: 5, gapY: GAP_Y, gapW: GAP_W, hold: 0, boost: 0, slow: 0, jump: -1, t: 0, shake: 0, meter: 50, boosting: false, air: 0, ground: 0, onRamp: 0, vy: 0, airT: 0, airDur: 0, trick: "", dir: 1, combo: 0, over: false, by: "" };
let runOpt = null, startCgpa = 5;
const view = { az: 0.6, el: 0.28, r: 12, rT: 8, auto: true, idle: 0, dolly: 1 };
const keys = {}; const RAMP_L = 10, RAMP_H = 3.0; let traffic = [], folk = [], ramps = []; const carFlames = []; let rampP = 0, sx = 0, steer = 0, yawS = null, rollS = 0;
let ac = null, callBuf = null, loopTimer = 0;
const sfx = createSfx(() => ac, () => muted); let wasBoost = false, engOn = false, gateSfx = false, lastCombo = 0;

/* ================= path helper ================= */
const at = (s) => {                                     // point, forward, right at station s
  s = Math.max(0, Math.min(L - 0.001, s)); const i = s | 0, f = s - i, a = P[i], b = P[i + 1];
  const x = a.x + (b.x - a.x) * f, z = a.z + (b.z - a.z) * f;
  const j = Math.min(L, i + 3), k = Math.max(0, i - 2); let fx = P[j].x - P[k].x, fz = P[j].z - P[k].z; const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
  return { x, z, fx, fz, rx: -fz, rz: fx, hw: a.hw + (b.hw - a.hw) * f };
};
const worldPos = (s, lat) => { const c = at(s); return new THREE.Vector3(c.x + c.rx * lat, 0, c.z + c.rz * lat); };

/* ================= loading ================= */
function loadAll(onPct) {
  const dr = new DRACOLoader().setDecoderPath("vendor/draco/");
  const gl = new GLTFLoader().setDRACOLoader(dr);
  const get = (url, cb) => new Promise((ok, no) => gl.load(url, ok, (e) => e.total && cb && cb(e.loaded / e.total), no));
  const M = (n) => get(BASE + "models/" + n + ".glb");
  return Promise.all([
    get(BASE + "level.glb", onPct), fetch(BASE + "level_data.json").then((r) => r.json()),
    M("VH_RocketRoadster"), M("EN_ChaserYellowHouse"), M("EN_ChaserWhiteHouse"), M("PK_CGPABoost"), M("PK_RocketFuel"),
    M("CH_Hawker"), M("CH_Lecturer"), M("CH_DancingGirl"), M("CH_Stubborn"), M("CH_PersonFemale"), M("CH_PersonMale"), M("VG_TreeA"), M("VG_Bush"), M("VG_Flower"),
    fetch(BASE + "sound/call.mp3").then((r) => r.arrayBuffer()).catch(() => null),
  ]).then(([lvl, data, car, yel, whi, pk, fuel, hawk, lect, danc, stub, pf, pm, vt, vb, vf, snd]) => ({ lvl, data, car, yel, whi, pk, fuel, hawk, lect, danc, stub, pf, pm, vt, vb, vf, snd }));
}

/* merge thousands of static scenery meshes into a few chunked meshes (far fewer draw calls) */
function optimise(root, keep) {
  root.updateMatrixWorld(true);
  const isKept = (o) => { for (let p = o; p; p = p.parent) if (keep.has(p)) return true; return false; };
  const matKey = (m) => [m.color ? m.color.getHexString() : "", m.map ? m.map.uuid : "", m.normalMap ? m.normalMap.uuid : "", m.roughness, m.metalness, m.transparent, m.side, m.emissive ? m.emissive.getHexString() : ""].join("|");
  const mats = new Map(), groups = new Map(), drop = [];
  root.traverse((o) => {
    if (!o.isMesh || o.isSkinnedMesh || isKept(o)) return;
    const m = Array.isArray(o.material) ? o.material[0] : o.material, k = matKey(m);
    if (!mats.has(k)) mats.set(k, m);
    const g = o.geometry.clone(); g.applyMatrix4(o.matrixWorld);
    for (const n of Object.keys(g.attributes)) if (!["position", "normal", "uv"].includes(n)) g.deleteAttribute(n);
    if (!g.attributes.normal) g.computeVertexNormals();
    if (!g.attributes.uv) g.setAttribute("uv", new THREE.BufferAttribute(new Float32Array(g.attributes.position.count * 2), 2));
    if (!g.index) { const n = g.attributes.position.count, ix = new Uint32Array(n); for (let i = 0; i < n; i++) ix[i] = i; g.setIndex(new THREE.BufferAttribute(ix, 1)); }
    g.computeBoundingBox(); const c = g.boundingBox.getCenter(new THREE.Vector3());
    const ck = k + "#" + Math.floor(c.x / 180) + "," + Math.floor(c.z / 180);
    (groups.get(ck) || groups.set(ck, { k, list: [] }).get(ck)).list.push(g);
    drop.push(o);
  });
  drop.forEach((o) => o.parent && o.parent.remove(o));
  const out = new THREE.Group();
  for (const { k, list } of groups.values()) { const merged = mergeGeometries(list, false); if (merged) out.add(new THREE.Mesh(merged, mats.get(k))); }
  root.add(out);
}

/* ================= build the world once ================= */
function build() {
  D = A.data; P = D.path.map((p) => ({ x: p[0], z: -p[1], lx: p[2], lz: -p[3], hw: p[4] })); L = P.length - 1;
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  host.appendChild(renderer.domElement);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  scene = new THREE.Scene(); const SKY = new THREE.Color(0xd8d9cc); scene.fog = new THREE.Fog(SKY, 150, 560);
  /* gradient sky dome with a low sun glow; also baked into an environment map so the paint and glass reflect the sky */
  const skyMat = new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false, fog: false,
    uniforms: { sunDir: { value: new THREE.Vector3(-0.5, 0.42, 0.35).normalize() } },
    vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }",
    fragmentShader: "varying vec3 vP; uniform vec3 sunDir; void main(){ float h = clamp(vP.y,-0.2,1.0); vec3 top=vec3(0.22,0.46,0.86), mid=vec3(0.62,0.76,0.92), hor=vec3(0.95,0.88,0.74); vec3 c = mix(hor, mid, smoothstep(0.0,0.25,h)); c = mix(c, top, smoothstep(0.2,0.9,h)); float s = max(dot(normalize(vP), sunDir),0.0); c += vec3(1.0,0.82,0.55)*pow(s,24.0)*0.55 + vec3(1.0,0.9,0.7)*pow(s,400.0)*2.0; if(vP.y<0.0) c = mix(hor, vec3(0.55,0.5,0.4), clamp(-vP.y*3.0,0.0,1.0)); gl_FragColor = vec4(c,1.0); }" });
  const dome = new THREE.Mesh(new THREE.SphereGeometry(800, 32, 16), skyMat); dome.renderOrder = -10; dome.frustumCulled = false; scene.add(dome); skyDome = dome;
  { const es = new THREE.Scene(); es.add(new THREE.Mesh(new THREE.SphereGeometry(50, 32, 16), skyMat)); const pm = new THREE.PMREMGenerator(renderer); scene.environment = pm.fromScene(es, 0.02).texture; scene.environmentIntensity = 0.85; pm.dispose(); }
  scene.add(new THREE.HemisphereLight(0xe8f1ff, 0xb8a888, 1.15));
  sun = new THREE.DirectionalLight(0xffe9c4, 2.4); sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.04;
  Object.assign(sun.shadow.camera, { left: -34, right: 34, top: 34, bottom: -34, near: 10, far: 400 }); scene.add(sun, sun.target);
  camera = new THREE.PerspectiveCamera(60, 1, 0.3, 900);

  world = A.lvl.scene; const nodes = new Map(); world.traverse((o) => nodes.set(o.name, o));
  const keep = new Set();
  for (const o of D.objs) {
    const n = nodes.get(o.r); if (!n) continue;
    if (o.n === "Obs_PR_JumpRamp") { n.visible = false; keep.add(n); ramp = o; continue; }
    if (HIT[o.n]) { keep.add(n); srcs[o.n] = srcs[o.n] || n; lvlThings.push({ o, n, p: n.position.clone(), q: n.quaternion.clone() }); }
  }
  world.traverse((o) => { if (o.isMesh) for (const m of [].concat(o.material)) if (m && m.name === "Level_Ground") { m.polygonOffset = true; m.polygonOffsetFactor = 8; m.polygonOffsetUnits = 8; } });
  optimise(world, keep); world.traverse((o) => { if (o.isMesh) o.receiveShadow = true; }); scene.add(world);
  dyn = new THREE.Group(); scene.add(dyn);
  // buildVeg();  // disabled: decimated trees lost their leaves

  /* car (smaller) + boost flame */
  car = new THREE.Group(); carModel = A.car.scene.clone(true); carModel.traverse((o) => { if (o.isMesh) o.castShadow = true; }); carModel.traverse((o) => { if (o.name.startsWith("COL_") || o.name.startsWith("SOCKET_")) o.visible = false; if (o.isMesh && o.material.name === "VH_Paint") { o.material = o.material.clone(); o.material.emissive.setHex(0x3a0a0e); } if (o.name.includes("Flame")) carFlames.push(o); o.visible = o.visible && !o.name.includes("Flame"); }); carModel.scale.setScalar(CAR_SCALE); car.add(carModel); scene.add(car);
  flame = new THREE.Mesh(new THREE.ConeGeometry(0.32, 3.2, 14), new THREE.MeshBasicMaterial({ color: 0xff7a1a, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false }));
  flame.rotation.x = -Math.PI / 2; flame.position.set(0, 0.45, -4.2 * CAR_SCALE - 1.4); flame.visible = false; car.add(flame);
  shadow = new THREE.Mesh(new THREE.CircleGeometry(1.4, 20), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.18 })); shadow.rotation.x = -Math.PI / 2; scene.add(shadow);
  const mkChaser = (src) => { const g = new THREE.Group(), m = src.scene.clone(true); const sz = new THREE.Box3().setFromObject(m).getSize(new THREE.Vector3()); m.scale.setScalar(12 / Math.max(0.01, sz.y)); m.position.y = -new THREE.Box3().setFromObject(m).min.y; g.add(m); g.visible = false; scene.add(g); return g; };
  yellow = mkChaser(A.yel); white = mkChaser(A.whi);
  crowdG = new THREE.Group(); scene.add(crowdG); buildCrowd(); buildFolk();

  /* input */
  const cv = renderer.domElement; let down = false, lx = 0, ly = 0, moved = 0, id = -1;
  cv.addEventListener("pointerdown", (e) => { down = true; lx = e.clientX; ly = e.clientY; moved = 0; id = e.pointerId; cv.setPointerCapture(id); });
  cv.addEventListener("pointermove", (e) => {
    if (!down) return; const dx = e.clientX - lx, dy = e.clientY - ly; lx = e.clientX; ly = e.clientY; moved += Math.abs(dx) + Math.abs(dy);
    if (mode === "run") st.uT += (dx / (cv.clientWidth || 360)) * 20;
    else if (mode === "lobby") { view.az -= dx * 0.008; view.el = Math.max(0.05, Math.min(1.25, view.el + dy * 0.006)); view.auto = false; view.idle = 0; }
  });
  cv.addEventListener("pointerup", (e) => { down = false; if (mode === "lobby" && moved < 8) tapLobby(e); });
  cv.addEventListener("pointercancel", () => (down = false));
  cv.addEventListener("wheel", (e) => { if (mode === "lobby") { view.rT = Math.max(4, Math.min(16, view.rT + e.deltaY * 0.01)); view.auto = false; view.idle = 0; e.preventDefault(); } }, { passive: false });
  addEventListener("keydown", (e) => { keys[e.code] = true; if (e.code === "Space") e.preventDefault(); }); addEventListener("keyup", (e) => { keys[e.code] = false; });
  const b = $("gboost"); const bo = (v) => (e) => { st.boosting = v; e.preventDefault(); };
  b.addEventListener("pointerdown", bo(true)); b.addEventListener("pointerup", bo(false)); b.addEventListener("pointerleave", bo(false)); b.addEventListener("pointercancel", bo(false));
  const resize = () => { const w = host.clientWidth || 360, h = host.clientHeight || 640; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix(); };
  resize(); addEventListener("resize", resize); new ResizeObserver(resize).observe(host);

  if (A.snd) { try { ac = ac || new (window.AudioContext || window.webkitAudioContext)(); ac.decodeAudioData(A.snd.slice(0), (b) => (callBuf = b)); } catch (e) {} }
  enterLobby(true); requestAnimationFrame(frame);
}

/* ================= lobby: the crowd ================= */

/* real (Poly Haven, CC0) trees, shrubs and flowers, instanced in 160 m chunks so off-screen ones are culled */
function buildVeg() {
  const rs = (() => { let x = 12345; return () => ((x = (x * 1664525 + 1013904223) >>> 0) / 4294967296); })();
  const groups = new Map(), src = { tree: A.vt, bush: A.vb, flower: A.vf };
  let n = 0;
  for (const [k, bx, by, rz, , i, lat] of D.veg) {
    n++; if (k === "bush" && n % 2) continue; if (k === "tree" && Math.abs(lat) > 24 && n % 2) continue;
    const key = k + ":" + Math.floor(i / 160); if (!groups.has(key)) groups.set(key, []); groups.get(key).push([bx, -by, rz]);
  }
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0), p = new THREE.Vector3(), sc = new THREE.Vector3(), off = new THREE.Matrix4();
  const vg = new THREE.Group(); scene.add(vg);
  for (const [key, list] of groups) {
    const kind = key.split(":")[0], model = src[kind].scene, mats = [];
    model.updateMatrixWorld(true);
    const insts = [];
    for (const [x, z, rz] of list) {
      if (kind === "flower") { const c = 5 + Math.floor(rs() * 3); for (let j = 0; j < c; j++) insts.push([x + (rs() - 0.5) * 1.6, z + (rs() - 0.5) * 1.6, rs() * 6.28, 0.9 + rs() * 0.8]); }
      else insts.push([x, z, rz, kind === "tree" ? 1.35 + rs() * 0.9 : 0.28 + rs() * 0.22]);
    }
    model.traverse((o) => {
      if (!o.isMesh) return;
      const im = new THREE.InstancedMesh(o.geometry, o.material, insts.length); o.material.side = THREE.DoubleSide;
      insts.forEach(([x, z, r, s], idx) => { q.setFromAxisAngle(up, r); p.set(x, 0, z); sc.setScalar(s); m4.compose(p, q, sc).multiply(o.matrixWorld); im.setMatrixAt(idx, m4); });
      im.instanceMatrix.needsUpdate = true; im.computeBoundingSphere(); im.frustumCulled = true; vg.add(im);
    });
  }
}
function cloneSkinned(src) {
  const c = src.clone(true), bm = {};
  c.traverse((o) => { if (o.isBone) bm[o.name] = o; });
  c.traverse((o) => { if (o.isSkinnedMesh) { const sk = new THREE.Skeleton(o.skeleton.bones.map((b) => bm[b.name]), o.skeleton.boneInverses); o.bind(sk, o.bindMatrix); o.material = o.material.clone(); } });
  return c;
}
function person(female, anim, scale) {
  const src = female ? A.pf : A.pm, m = cloneSkinned(src.scene); const g = new THREE.Group(); g.add(m); crowdG.add(g); g.scale.setScalar(scale);
  const sh = new THREE.Color().setHSL(Math.random(), rnd(0.5, 0.75), rnd(0.35, 0.5)), pn = new THREE.Color().setHSL(rnd(0.55, 0.7), rnd(0.15, 0.4), rnd(0.15, 0.3));
  m.traverse((o) => { if (o.isMesh) { if (o.material.name === "Shirt") o.material.color.copy(sh); else if (o.material.name === "Pants") o.material.color.copy(pn); } });
  const mx = new THREE.AnimationMixer(m), clip = src.animations.find((c) => c.name === anim) || src.animations[0], act = mx.clipAction(clip); act.play(); mx.update(rnd(0, 3));
  return { g, m, mx, act };
}
function buildCrowd() {
  const lob = at(LOBBY_S);
  const spot = (r, a) => worldPos(LOBBY_S + Math.sin(a) * r, lob.hw + 1.75 + Math.cos(a) * r);          // around the car
  const lab = $("labels");
  HAWKERS.forEach((h, i) => {
    const p0 = person(i % 2 === 0, "Interact", rnd(0.95, 1.05)), g = p0.g;
    const a = (i / HAWKERS.length) * Math.PI * 2 + 0.5, r = rnd(6.5, 10.5), p = spot(r, a); g.position.copy(p);
    const el = document.createElement("div"); el.className = "hl"; el.textContent = "🎟 " + h.line; lab.appendChild(el);
    el.addEventListener("click", () => pickHawker(i));
    hawkers.push({ g, mx: p0.mx, home: p.clone(), ph: rnd(0, 6), h, el, i });
  });
  for (let i = 0; i < 12; i++) {
    const p0 = person(i % 2 === 1, "Walk_Loop", rnd(0.92, 1.06)), p = spot(rnd(5, 24), rnd(0, 6.28)); p0.g.position.copy(p);
    walkers.push({ g: p0.g, mx: p0.mx, tgt: p.clone(), sp: rnd(1.0, 1.5), ph: rnd(0, 6) });
  }
  [[8, 0.9, 1], [-9, 2.4, 0], [12, 4.2, 1]].forEach(([r, a, f]) => {
    const p0 = person(!!f, "Dance_Loop", 1); p0.g.position.copy(spot(r, a)); p0.g.rotation.y = rnd(0, 6.28);
    walkers.push({ g: p0.g, mx: p0.mx, dance: true });
  });
}
function buildFolk() {                                                      // pedestrians along the whole route
  for (let k = 0; k < 26; k++) {
    const p0 = person(k % 2 === 0, "Walk_Loop", rnd(0.95, 1.05)), s0 = LOBBY_S + 70 + (k / 26) * (L - LOBBY_S - 140) + rnd(-20, 20), left = k % 3 === 0;
    p0.g.visible = false; folk.push({ g: p0.g, mx: p0.mx, s: s0, s0, u: left ? -2 * at(s0).hw - 8.6 - rnd(0, 1) : 8.0 + rnd(0, 1.4), dir: Math.random() < 0.5 ? 1 : -1 });
  }
}
function updateCrowd(dt, t) {
  const cp = car.position;
  for (const h of hawkers) {
    h.mx.update(dt);
    h.g.position.set(h.home.x + Math.sin(t * 0.6 + h.ph) * 0.5, 0, h.home.z + Math.cos(t * 0.5 + h.ph) * 0.5);
    h.g.rotation.y = Math.atan2(cp.x - h.g.position.x, cp.z - h.g.position.z);
  }
  for (const w of walkers) {
    w.mx.update(dt);
    if (w.dance) continue;
    const dx = w.tgt.x - w.g.position.x, dz = w.tgt.z - w.g.position.z, d = Math.hypot(dx, dz);
    if (d < 0.6) { const q = worldPos(LOBBY_S + rnd(-26, 30), rnd(-12, 16)); if (q.distanceTo(cp) > 4.5) w.tgt.copy(q); }
    else { w.g.position.x += (dx / d) * w.sp * dt; w.g.position.z += (dz / d) * w.sp * dt; w.g.rotation.y = Math.atan2(dx, dz); }
  }
}
const proj = new THREE.Vector3();
function updateLabels() {
  const w = host.clientWidth, h = host.clientHeight;
  for (const hk of hawkers) {
    proj.copy(hk.g.position); proj.y += 2.25; proj.project(camera);
    const vis = proj.z < 1 && Math.abs(proj.x) < 1.15 && proj.y > -1.1;
    hk.el.style.display = vis ? "block" : "none";
    if (vis) hk.el.style.transform = `translate(${((proj.x + 1) / 2) * w}px,${((1 - proj.y) / 2) * h}px) translate(-50%,-100%)`;
  }
}
function pickHawker(i) { const h = HAWKERS[i]; shout(); window.OAUUI.openSheet(h); }
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
function tapLobby(e) {
  const r = renderer.domElement.getBoundingClientRect(); ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObjects(hawkers.map((h) => h.g), true)[0];
  if (hit) { const hk = hawkers.find((h) => { for (let o = hit.object; o; o = o.parent) if (o === h.g) return true; }); if (hk) pickHawker(hk.i); }
}

/* ================= the "ticket, ticket" sound: your clip, repeated forever with variation ================= */
function shout(pan) {
  if (!ac || !callBuf || muted) return;
  const src = ac.createBufferSource(); src.buffer = callBuf; src.playbackRate.value = rnd(0.9, 1.12);
  const g = ac.createGain(); g.gain.value = rnd(0.35, 0.7); let node = g;
  if (ac.createStereoPanner) { const p = ac.createStereoPanner(); p.pan.value = pan === undefined ? rnd(-0.8, 0.8) : pan; g.connect(p); node = p; }
  src.connect(g); node.connect(ac.destination); src.start();
}
function startCalls() { stopCalls(); const loop = () => { if (mode === "lobby" && !muted) shout(); loopTimer = setTimeout(loop, rnd(450, 1000)); }; loop(); }
function stopCalls() { clearTimeout(loopTimer); loopTimer = 0; }

/* ================= lobby / run control ================= */
function enterLobby(first) {
  mode = "lobby"; paused = false; st.over = true; runOpt = null;
  for (const t of things) if (t.clone) dyn.remove(t.node); things = [];
  for (const p of picks) dyn.remove(p.w); picks = [];
  for (const t of lvlThings) { t.n.position.copy(t.p); t.n.quaternion.copy(t.q); t.n.rotation.set(0, 0, 0, "XYZ"); t.n.quaternion.copy(t.q); t.n.visible = false; }
  hawkers.forEach((h) => (h.g.visible = true)); walkers.forEach((w) => (w.g.visible = true)); folk.forEach((f) => (f.g.visible = false));
  yellow.visible = white.visible = false; flame.visible = false; for (const f of carFlames) f.visible = false;
  const c = at(LOBBY_S), p = worldPos(LOBBY_S, c.hw + 1.75); car.position.copy(p); car.position.y = 0.02; car.rotation.set(0, Math.atan2(c.fx, c.fz), 0);
  shadow.position.set(p.x, 0.06, p.z); shadow.scale.setScalar(1);
  st.s = LOBBY_S; st.u = st.uT = 1.75; st.v = 0;
  hawkers.forEach((h) => (h.el.style.display = "block"));
  view.az = Math.atan2(c.fx, c.fz) + 2.3; view.el = 0.3; view.r = first ? 22 : 14; view.rT = 8.5; view.auto = true; view.idle = 0;
  startCalls();
}
function spawn() {
  /* the original level obstacles after the gate, thinned out; then generated ones with rising difficulty */
  const cand = lvlThings.filter((t) => t.o.i > LOBBY_S + 70 && t.o.i < L - 140).sort((a, b) => a.o.i - b.o.i);
  let lastI = -1e9, lastKept = false, lastKeptI = -1e9; const keepSet = new Set();
  for (const t of cand) { const near = t.o.i - lastI < 4.5; const k = near ? lastKept : t.o.i - lastKeptI >= 30; lastI = t.o.i; lastKept = k; if (k) { lastKeptI = t.o.i; keepSet.add(t); } }
  for (const t of lvlThings) {
    if (keepSet.has(t)) { t.n.visible = true; const s = HIT[t.o.n]; things.push({ node: t.n, name: t.o.n, i: t.o.i, u: t.o.lat - at(t.o.i).hw, r: s[0], dmg: s[1], note: s[2], hit: false, t: 0 }); }
  }
  const place = (name, s, u) => {
    const src = srcs[name]; if (!src) return; const n = src.clone(true); n.visible = true; const c = at(s), lat = c.hw + u;
    n.position.set(c.x + c.rx * lat, 0, c.z + c.rz * lat); const mover = name.startsWith("VH_"), vel = mover ? (u < 0 ? -rnd(12, 18) : rnd(8, 14)) : 0; n.rotation.set(0, Math.atan2(c.fx, c.fz) + (vel < 0 ? Math.PI : 0), 0); n.scale.set(1, 1, 1); dyn.add(n);
    const sp = HIT[name]; things.push({ node: n, name, i: s, u, r: sp[0], dmg: sp[1], note: sp[2], hit: false, t: 0, clone: true, vel });
  };
  const RIGHT = [0.9, 1.75, 2.6, 4.4, 6.0];
  let s = LOBBY_S + 130;
  while (s < L - 130) {
    const prog = (s - LOBBY_S) / (L - LOBBY_S); const pool = []; POOLS.forEach((p) => { if (prog >= p.from) pool.push(...p.names); });
    if (!things.some((t) => Math.abs(t.i - s) < 16)) {
      const name = pick(pool), hw = at(s).hw, left = Math.random() < 0.2, base = pick(RIGHT), u = left ? -2 * hw - base : base;
      if (name === "Obs_PR_Cone") for (let k = 0; k < 3; k++) place(name, s + k * 1.3, u); else place(name, s, u);
      if (!left && prog > 0.35 && Math.random() < 0.35) { const other = RIGHT.filter((x) => Math.abs(x - base) > 3.4); if (other.length) place(pick(pool), s + 4, pick(other)); }   // second blocker, always leaving a gap
    }
    s += 78 - 34 * prog + rnd(0, 16);
  }
  /* stunt ramps: hit one and you fly, spin and land for bonus CGPA */
  const RW = 4.6, RLn = RAMP_L, RH = RAMP_H, shp = new THREE.Shape(); shp.moveTo(0, 0); shp.lineTo(RLn, 0); shp.lineTo(RLn, RH); shp.lineTo(0, 0);
  const rg = new THREE.ExtrudeGeometry(shp, { depth: RW, bevelEnabled: false }); rg.translate(-RLn / 2, 0, -RW / 2);
  const rm = new THREE.MeshStandardMaterial({ color: 0xf2b81c, roughness: 0.55 }), rs = new THREE.MeshStandardMaterial({ color: 0x2a2112, roughness: 0.8 });
  for (let rS = LOBBY_S + 160; rS < L - 160; rS += 100 + rnd(0, 40)) {
    const ru = pick([1.9, 3.2, 4.6]), c = at(rS), lat = c.hw + ru, m = new THREE.Mesh(rg, [rm, rs]);
    m.position.set(c.x + c.rx * lat, 0.02, c.z + c.rz * lat); m.rotation.y = Math.atan2(c.fx, c.fz) - Math.PI / 2; m.castShadow = false; dyn.add(m);
    ramps.push({ s: rS, u: ru, m, used: false });
    for (const t of things) if (!t.hit && t.i > rS - 14 && t.i < rS + 62 && Math.abs(t.u - ru) < 4.4) { t.hit = true; t.t = 5; t.node.visible = false; }
  }
  for (const v of traffic) dyn.remove(v.n); traffic = [];
  for (let ts = LOBBY_S + 80; ts < L - 40; ts += 38 + rnd(0, 34)) {                           // life on the other carriageway
    const nm = pick(["VH_Danfo", "VH_KekeNapep", "VH_KekeNapep", "VH_Danfo"]), src = srcs[nm]; if (!src) continue;
    const n = src.clone(true); n.visible = false; dyn.add(n); traffic.push({ n, i: ts, u: -2 * at(ts).hw - pick([1.75, 3.3]), v: -rnd(13, 20) });
  }
  for (let ps = LOBBY_S + 90; ps < L - 150; ps += 85) {                                              // pickups: CGPA boost (+boost meter) and rocket fuel
    let u = pick([0.9, 1.75, 3.2, 5.2]); if (things.some((t) => Math.abs(t.i - ps) < 14 && Math.abs(t.u - u) < 3) || ramps.some((r) => Math.abs(r.s - ps) < 22)) u = u > 2.5 ? 1.0 : 4.8;
    const fuel = Math.random() < 0.4, src = fuel ? A.fuel : A.pk, g = src.scene.clone(true); const sz = new THREE.Box3().setFromObject(g).getSize(new THREE.Vector3()); g.scale.setScalar(1.3 / Math.max(0.01, sz.y));
    const w = new THREE.Group(); w.add(g); dyn.add(w); picks.push({ w, s: ps, u, got: false, fuel });
  }
}
function prepareRun() { for (const r of ramps) dyn.remove(r.m); ramps = []; for (const v of traffic) dyn.remove(v.n); traffic = []; folk.forEach((f, k) => { f.s = f.s0; }); yawS = null; steer = 0; rollS = 0; for (const t of things) if (t.clone) dyn.remove(t.node); things = []; for (const p of picks) dyn.remove(p.w); picks = []; spawn(); stopCalls(); }
function run(opt) {
  runOpt = opt; startCgpa = opt.cgpa; mode = "run"; paused = false;
  Object.assign(st, { s: LOBBY_S, u: 1.75, uT: 1.75, v: 0, cgpa: opt.cgpa, gapY: GAP_Y, gapW: GAP_W, hold: 0, boost: 0, slow: 0, jump: -1, t: 0, shake: 0, meter: 50, boosting: false, air: 0, ground: 0, onRamp: 0, vy: 0, airT: 0, airDur: 0, trick: "", dir: 1, combo: 0, over: false, by: "" });
  const mr = $("mirror"); if (mr) mr.style.display = "none"; gateSfx = false; lastCombo = 0; wasBoost = false; sfx.play("go");
  hawkers.forEach((h) => (h.g.visible = false)); walkers.forEach((w) => (w.g.visible = false));
  yellow.visible = white.visible = true; hawkers.forEach((h) => (h.el.style.display = "none")); stopCalls();
}
function finish(kind) {
  if (st.over) return; st.over = true;
  let cg = Math.max(0, st.cgpa); if (kind === "caught") cg = Math.max(0, cg - 0.3);
  sfx.engineStop(); engOn = false; sfx.play(kind === "grad" ? "win" : "lose");
  runOpt.onEnd({ kind, cgpa: cg, start: startCgpa, by: st.by || "The Yellow House" });
}
const toast = (t, good) => { if (good) { const f = $("gflash"); f.className = "good"; f.style.animation = "none"; void f.offsetWidth; f.style.animation = ""; } else $("gflash").className = "";
   const el = $("gtoast"); el.textContent = t; el.className = good ? "good" : "bad"; el.style.animation = "none"; void el.offsetWidth; el.style.animation = ""; };

/* ================= the frame ================= */
let last = performance.now(), T = 0; const camPos = new THREE.Vector3(), camLook = new THREE.Vector3(); let camInit = false;
function frame(now) {
  if (!window.__step) requestAnimationFrame(frame);
  if (window.__pause && !window.__step) return;
  const dt = Math.max(0, Math.min(0.05, (now - last) / 1000)); last = now; T += dt;
  const live = mode === "run" && !paused && !st.over;
  if (live && !engOn) { engOn = true; sfx.engineStart(); } else if (!live && engOn) { engOn = false; sfx.engineStop(); }
  if (mode === "lobby") lobby(dt); else if (live) drive(dt);
  poseCar(dt);
  { const f = mode === "run" ? car.position : car.position; sun.target.position.copy(f); sun.position.set(f.x - 70, f.y + 110, f.z + 50); skyDome.position.copy(camera.position); }
  camera.updateProjectionMatrix();
  renderer.render(scene, camera);
  if (mode === "run" && !st.over && st.s >= INTRO_END - 10) renderMirror();
}
/* rear-view mirror: a small second render looking backwards so you can see the Houses chasing you */
const rear = new THREE.PerspectiveCamera(40, 2.6, 0.3, 400); const mir = { x: 0, y: 0, w: 0, h: 0 };
function renderMirror() {
  const el = $("mirror"); if (!el) return; el.style.display = "block";
  const c = at(st.s), W = host.clientWidth, H = host.clientHeight, mw = Math.min(200, W * 0.5), mh = mw * 0.4, top = 118;
  Object.assign(el.style, { width: mw + "px", height: mh + "px", top: top + "px" });
  rear.aspect = mw / mh; rear.updateProjectionMatrix();
  rear.position.set(car.position.x - c.fx * 1.2, 1.9, car.position.z - c.fz * 1.2);
  rear.lookAt(car.position.x - c.fx * 40, 3.2, car.position.z - c.fz * 40);
  car.visible = false; shadow.visible = false;
  renderer.setScissorTest(true); const x = (W - mw) / 2, y = H - top - mh;
  renderer.setViewport(x, y, mw, mh); renderer.setScissor(x, y, mw, mh); renderer.setClearColor(0xa9bfdc, 1); renderer.clear(); renderer.render(scene, rear);
  renderer.setScissorTest(false); renderer.setViewport(0, 0, W, H);
  car.visible = true; shadow.visible = true;
}

function lobby(dt) {
  updateCrowd(dt, T);
  view.idle += dt; if (!view.auto && view.idle > 3) view.auto = true;
  if (view.auto) view.az += dt * 0.28;
  view.r += (view.rT - view.r) * Math.min(1, 1.6 * dt);
  const c = car.position, cosE = Math.cos(view.el);
  camera.position.set(c.x + Math.sin(view.az) * cosE * view.r, 0.9 + Math.sin(view.el) * view.r, c.z + Math.cos(view.az) * cosE * view.r);
  camera.lookAt(c.x, 0.9, c.z); camera.fov = camera.aspect < 0.8 ? 62 : 48; camInit = false;
  updateLabels();
  for (const hk of hawkers) hk.el.classList.toggle("hot", Math.sin(T * 5 + hk.ph) > 0.7);
}

function drive(dt) {
  st.t += dt;
  const hw0 = at(st.s).hw;
  const intro = st.s < INTRO_END;                                         // cinematic: the car flies the gate by itself, then you take over
  if (intro) st.uT = 1.75; else { if (keys.ArrowLeft || keys.KeyA) st.uT -= 14 * dt; if (keys.ArrowRight || keys.KeyD) st.uT += 14 * dt; }
  st.uT = Math.max(-(2 * hw0) - 7.5, Math.min(7.5, st.uT));               // u = metres right of the median edge (0 = edge, 1.75 = lane centre)
  const pl = st.u; st.u += (st.uT - st.u) * Math.min(1, 7 * dt); sx = (st.u - pl) / Math.max(dt, 1e-3); sx = sx;
  /* boost: hold the button / Space / Shift. It uses the boost meter. */
  const wantBoost = !intro && (st.boosting || keys.Space || keys.ShiftLeft || keys.ShiftRight);
  const boosting = wantBoost && st.meter > 0 && st.t > 1.2;
  if (boosting) st.meter = Math.max(0, st.meter - 30 * dt); else st.meter = Math.min(100, st.meter + 3 * dt);
  st.isBoost = boosting; if (boosting && !wasBoost) sfx.play("boost"); wasBoost = boosting;
  if (intro && !gateSfx && st.s > GATE_S - 26) { gateSfx = true; sfx.play("launch"); }
  sfx.engineUpdate(st.v, boosting, st.air > 0 || (intro && st.s > GATE_S - 24 && st.s < GATE_S + 24));
  let target = CRUISE * Math.min(1, 0.25 + st.t / 1.6) * (boosting ? BOOST_MULT : 1) * (st.boost > 0 ? 1.15 : 1);
  if (st.hold > 0) { target = Math.min(target, 11); st.hold -= dt; if (Math.abs(sx) > 4) st.hold -= dt * 2; }
  if (st.slow > 0) { target *= 0.45; st.slow -= dt; }
  st.boost -= dt; st.v += (target - st.v) * Math.min(1, (target < st.v ? 6 : 5) * dt);
  st.s += st.v * dt;
  /* ramps and air */
  st.ground = 0;
  if (st.air <= 0 && !intro) for (const r of ramps) {
    if (Math.abs(st.u - r.u) > 2.3) continue;
    const a = r.s - RAMP_L / 2, f = (st.s - a) / RAMP_L;
    if (f > 0 && f < 1 && !r.used) { st.ground = RAMP_H * f; st.onRamp = 1; }
    if (f >= 0.97 && !r.used) {
      r.used = true; st.vy = 12 + st.v * 0.07; st.air = RAMP_H; st.ground = 0; st.airT = 0; st.airDur = (st.vy + Math.sqrt(st.vy * st.vy + 2 * 22 * RAMP_H)) / 22;
      const dirIn = st.uT - st.u, side = dirIn < -0.4 || keys.ArrowLeft || keys.KeyA || dirIn > 0.4 || keys.ArrowRight || keys.KeyD; st.dir = dirIn < -0.4 || keys.ArrowLeft || keys.KeyA ? -1 : 1; st.trick = side ? "BARREL ROLL" : "BACKFLIP";
      toast("AIRBORNE!", true); sfx.play("launch");
    }
  }
  if (st.air > 0) { st.airT += dt; st.vy -= 22 * dt; st.air += st.vy * dt; if (st.air <= 0 && st.vy < 0) {
    st.air = 0; st.vy = 0; st.combo++; const bonus = st.combo >= 2 ? 0.08 : 0.05; st.cgpa = Math.min(5, st.cgpa + bonus); st.meter = Math.min(100, st.meter + 25); st.shake = 0.25;
    sfx.play("land"); sfx.play("combo", st.combo); toast(`${st.trick} +${bonus.toFixed(2)} CGPA${st.combo >= 2 ? "  x" + st.combo + " COMBO" : ""}`, true); st.trick = ""; } }
  /* chasers */
  const prog = (st.s - LOBBY_S) / (L - LOBBY_S), vc = (CHASE0 + (CHASE1 - CHASE0) * prog) * Math.min(1, st.t / 2.5);
  st.gapY += (st.v - vc) * dt; st.gapW += (st.v - (vc - 0.6)) * dt; st.gapY = Math.min(st.gapY, 46); st.gapW = Math.min(st.gapW, 70);
  if (Math.min(st.gapY, st.gapW) <= CAUGHT_GAP) { st.by = st.gapY <= st.gapW ? "The Yellow House" : "The White House"; finish("caught"); }
  /* the road is alive: moving cars, oncoming traffic, people on the verge */
  const mv = (n, i, u, back) => { const c = at(i), lat = c.hw + u; n.position.set(c.x + c.rx * lat, 0, c.z + c.rz * lat); n.rotation.y = Math.atan2(c.fx, c.fz) + (back ? Math.PI : 0); };
  for (const t of things) if (t.vel && !t.hit) { t.i += t.vel * dt; mv(t.node, t.i, t.u, t.vel < 0); }
  for (const v of traffic) { v.i += v.v * dt; const near = Math.abs(v.i - st.s) < 240; v.n.visible = near; if (near) mv(v.n, v.i, v.u, true); }
  for (const f of folk) { const near = Math.abs(f.s - st.s) < 110; f.g.visible = near; if (!near) continue; f.s += f.dir * 1.3 * dt; f.mx.update(dt); mv(f.g, f.s, f.u, f.dir < 0); }
  /* collisions */
  for (const t of things) {
    if (t.hit || Math.abs(t.i - st.s) > 5) continue;
    if (st.air > 0.9) continue;
    if (!t.near && Math.abs(t.i - st.s) < 0.8) { t.near = true; const gap = Math.abs(t.u - st.u) - (t.r + CAR_HW); if (gap > 0 && gap < 0.9 && t.dmg > 0) { st.combo++; st.cgpa = Math.min(5, st.cgpa + 0.02); st.meter = Math.min(100, st.meter + 8); toast("NEAR MISS +0.02", true); sfx.play("whoosh"); sfx.play("combo", st.combo); } }
    if (Math.abs(t.i - st.s) < t.r + CAR_HL && Math.abs(t.u - st.u) < t.r + CAR_HW) {
      st.combo = 0; sfx.play("crash");
      t.hit = true; st.cgpa = Math.max(0, st.cgpa - t.dmg); st.shake = 0.5; const f = $("gflash"); f.style.animation = "none"; void f.offsetWidth; f.style.animation = "";
      if (t.name === "CH_Stubborn") st.hold = 2.6; else st.slow = t.name.includes("SpeedBump") ? 0.3 : 0.9;
      toast(t.note + (t.dmg ? `  −${t.dmg.toFixed(2)} CGPA` : "  swerve to shake him off!"), false);
      if (st.cgpa <= 0.001) { st.by = "Your own results"; finish("caught"); }
    }
  }
  for (const p of picks) if (!p.got && Math.abs(p.s - st.s) < 2.8 && Math.abs(p.u - st.u) < 2.0) {
    p.got = true; p.w.visible = false; st.gapY += 10; st.gapW += 10;
    sfx.play("pickup"); if (p.fuel) { st.meter = Math.min(100, st.meter + 40); toast("Rocket fuel +boost", true); } else { st.cgpa = Math.min(5, st.cgpa + 0.05); st.meter = Math.min(100, st.meter + 15); toast("CGPA boost +0.05", true); }
  }
  if (st.s >= L - 30) finish("grad");
  /* hud */
  $("gprog").style.width = Math.min(100, ((st.s - LOBBY_S) / (L - 30 - LOBBY_S)) * 100) + "%";
  const danger = 1 - Math.min(1, (Math.min(st.gapY, st.gapW) - CAUGHT_GAP) / 60); $("ggap").style.width = danger * 100 + "%"; $("ggap").parentNode.parentNode.className = "gbar warn" + (danger > 0.7 ? " hot" : "");
  $("gspeed").textContent = "CGPA " + st.cgpa.toFixed(2);
  { const stars = danger > 0.15 ? Math.min(5, Math.ceil(danger * 5)) : 0; $("heat").textContent = "HEAT " + "★".repeat(stars) + "☆".repeat(5 - stars); $("hud").classList.toggle("siren", danger > 0.7); sfx.siren(danger > 0.7); const cb = $("combo"); if (st.combo !== lastCombo) { lastCombo = st.combo; cb.textContent = st.combo >= 2 ? "COMBO x" + st.combo : ""; cb.style.animation = "none"; void cb.offsetWidth; cb.style.animation = ""; } }
  $("gbooststat").style.width = st.meter + "%"; $("hud").classList.toggle("fast", !!boosting); const gb = $("gboost"); gb.classList.toggle("on", !!boosting); gb.classList.toggle("empty", st.meter <= 0);
  for (const t of things) if (t.hit && t.t < 1.2) { t.t += dt; t.node.position.y += (7 - t.t * 8) * dt; t.node.rotation.x += 9 * dt; t.node.rotation.z += 6 * dt; if (t.t >= 1.2) t.node.visible = false; }
}

function poseCar(dt) {
  if (mode !== "run") { if (mode === "lobby") { car.position.y = 0.02 + Math.sin(T * 9) * 0.004; flame.visible = false; } return; }
  const c = at(st.s), lat = c.hw + st.u, px = c.x + c.rx * lat, pz = c.z + c.rz * lat;
  const a0 = GATE_S - 24, a1 = GATE_S + 24, jt = Math.max(0, Math.min(1, (st.s - a0) / (a1 - a0)));
  const air = st.s < INTRO_END ? 11 * Math.sin(Math.PI * jt) : st.air, pitch = st.s < INTRO_END ? -Math.atan(11 * Math.PI / (a1 - a0) * Math.cos(Math.PI * jt)) * 0.8 : 0;
  car.position.set(px, 0.02 + air + st.ground, pz);
  /* smooth steering: ease toward the lane error, never use the raw per-frame velocity */
  const tgtSteer = Math.max(-0.22, Math.min(0.22, (st.uT - st.u) * 0.035));
  steer += (tgtSteer - steer) * Math.min(1, 5 * dt);
  const hd = Math.atan2(c.fx, c.fz);
  if (yawS === null) yawS = hd;
  let dd = hd - yawS; dd = Math.atan2(Math.sin(dd), Math.cos(dd)); yawS += dd * Math.min(1, 10 * dt);
  /* stunts: scripted barrel roll over the gate; ramp jumps pick a roll or a backflip */
  const ss = (x) => { x = Math.max(0, Math.min(1, x)); return x * x * (3 - 2 * x); };
  let tAng = 0, tRoll = true, base = pitch;
  rampP += ((st.ground > 0 ? -Math.atan(RAMP_H / RAMP_L) : 0) - rampP) * Math.min(1, 14 * dt); if (st.s >= INTRO_END && st.air <= 0) base = rampP;
  if (st.s < INTRO_END) tAng = Math.PI * 2 * ss((jt - 0.12) / 0.7);
  else if (st.air > 0 && st.airDur > 0) { const fr = Math.min(1, st.airT / st.airDur); tAng = Math.PI * 2 * ss(fr / 0.85); tRoll = st.trick === "BARREL ROLL"; base = -0.35 * Math.cos(Math.PI * fr); }
  car.rotation.order = "YXZ"; car.rotation.set(tRoll ? base : base - tAng, yawS + steer * 0.9, 0);
  rollS += ((-steer * 0.35) - rollS) * Math.min(1, 6 * dt);
  car.rotation.z = rollS + (tRoll ? tAng * (st.dir || 1) : 0);
  for (const f of carFlames) f.visible = !!st.isBoost;
  flame.visible = false; if (st.isBoost) { flame.scale.set(1 + Math.random() * 0.3, 1 + Math.random() * 0.6, 1); flame.material.opacity = 0.6 + Math.random() * 0.35; }
  shadow.position.set(px, 0.06, pz); shadow.scale.setScalar(1 / (1 + air * 0.25));
  const put = (obj, gap, f) => { const q = at(st.s - gap); const l = q.hw + st.u * f; obj.position.set(q.x + q.rx * l, Math.sin(T * 3 + gap) * 0.25, q.z + q.rz * l); obj.rotation.y = Math.atan2(q.fx, q.fz); };
  put(yellow, st.gapY, 0.8); put(white, st.gapW, 1.1);
  for (const p of picks) if (!p.got) { const q = at(p.s), pl = q.hw + p.u; p.w.position.set(q.x + q.rx * pl, 1.2 + Math.sin(T * 3 + p.s) * 0.2, q.z + q.rz * pl); p.w.rotation.y = T * 2; }
  /* chase camera, tuned for a tall phone screen */
  const portrait = camera.aspect < 0.8, back = portrait ? 8.8 : 10.5, high = portrait ? 4.0 : 3.8;
  const introK = st.s < INTRO_END, t01 = Math.max(0, Math.min(1, (st.s - (GATE_S - 34)) / 66)), phi = introK ? Math.sin(Math.PI * t01) * 1.3 : 0;
  if (introK) {                                                           // swing round to the side, watch the jump, come back behind
    const b = back * 1.05, ca = Math.cos(phi), sa = Math.sin(phi);
    camPos.set(px - c.fx * b * ca + c.rx * b * sa * 1.1, high + air * 0.55 + sa * 0.8, pz - c.fz * b * ca + c.rz * b * sa * 1.1);
    camLook.set(px + c.fx * (3 + 5 * ca), 1.2 + air * 0.75, pz + c.fz * (3 + 5 * ca));
  } else {
    camPos.set(c.x + c.rx * lat * 0.8 - c.fx * (back + air * 0.5), high + air * 0.45, c.z + c.rz * lat * 0.8 - c.fz * (back + air * 0.5));
    camLook.set(c.x + c.rx * lat * 0.92 + c.fx * 14, 1.3 + air * 0.5, c.z + c.rz * lat * 0.92 + c.fz * 14);
  }
  camera.position.lerp(camPos, Math.min(1, (st.t < 0.5 ? 3 : introK ? 8 : 6) * dt)); camInit = true;
  if (st.shake > 0) { st.shake -= dt; camera.position.x += (Math.random() - 0.5) * st.shake * 0.8; camera.position.y += (Math.random() - 0.5) * st.shake * 0.6; }
  camera.lookAt(camLook);
  const baseFov = portrait ? 74 : 62; camera.fov += (baseFov + Math.min(10, st.v * 0.1) + (st.isBoost ? 12 : 0) - camera.fov) * Math.min(1, 3 * dt);
}

/* ================= public API for the UI ================= */
window.OAU3D = {
  enterLobby, prepareRun, run,
  pause(v) { paused = !!v; if (!v) last = performance.now(); },
  setMuted(m) { muted = !!m; },
  unlockAudio() { try { ac = ac || new (window.AudioContext || window.webkitAudioContext)(); ac.resume(); if (!callBuf && A && A.snd) ac.decodeAudioData(A.snd.slice(0), (b) => (callBuf = b)); } catch (e) {} },
  dbg: () => ({ THREE, scene, camera, car, st, get things() { return things; }, get ramps() { return ramps; }, frame, mode: () => mode, hawkers, walkers }),
};
host = $("canvasHost");
loadAll((p) => window.OAUUI.progress(p * 0.9)).then((a) => { A = a; window.OAUUI.progress(1); build(); window.OAUUI.setReady(); }).catch((e) => window.OAUUI.failed(e));
