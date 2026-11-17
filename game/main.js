import * as THREE from 'three';
import { GLTFLoader } from './vendor/jsm/loaders/GLTFLoader.js';
import { DRACOLoader } from './vendor/jsm/loaders/DRACOLoader.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setSize(innerWidth, innerHeight);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const sky = new THREE.Color(0x9cc4ee);
scene.background = sky;
scene.fog = new THREE.Fog(0xcfe0f3, 160, 800);

const camera = new THREE.PerspectiveCamera(50, innerWidth / innerHeight, 0.1, 800);
scene.add(new THREE.HemisphereLight(0xeaf2ff, 0xa08a62, 1.3));
const sun = new THREE.DirectionalLight(0xfff0d0, 2.6);
sun.position.set(35, 45, 55);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.05;
Object.assign(sun.shadow.camera, { left: -60, right: 60, top: 60, bottom: -60, near: 1, far: 200 });
scene.add(sun); scene.add(sun.target);

// Palettes keyed by the gate's material names (from the real gate photo)
// soft studio-sky environment for clean reflections (no extra files)
{
  const pm = new THREE.PMREMGenerator(renderer), es = new THREE.Scene();
  es.add(new THREE.Mesh(new THREE.SphereGeometry(50, 32, 16), new THREE.ShaderMaterial({ side: THREE.BackSide,
    vertexShader: 'varying vec3 p;void main(){p=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}',
    fragmentShader: 'varying vec3 p;void main(){float h=normalize(p).y;vec3 c=mix(vec3(.55,.5,.42),vec3(.62,.78,1.),smoothstep(-.1,.5,h));c+=vec3(1.)*smoothstep(.8,1.,h)*1.5;gl_FragColor=vec4(c,1.);}' })));
  scene.environment = pm.fromScene(es, 0.04).texture; scene.environmentIntensity = 0.3;
}
const PALETTES = {
  'Real photo': { Cream:'#ecd9a8', Tan:'#b8925a', DarkConcrete:'#3a3e48', GrayBlock:'#555b66', GoldMetal:'#b88a2c', Glass:'#6fa3dc', White:'#f3eee2', PaintWhite:'#f3eee2', Curb:'#b9b2a4' },
  'Warm sand':  { Cream:'#dcb97c', Tan:'#8e5d2e', DarkConcrete:'#2b2d34', GrayBlock:'#4a4640', GoldMetal:'#c08a1f', Glass:'#78a9d8', White:'#efe4cb', PaintWhite:'#efe4cb', Curb:'#a89f8c' },
  'Bright white': { Cream:'#f5f1e8', Tan:'#c9a66b', DarkConcrete:'#1f2a44', GrayBlock:'#34415f', GoldMetal:'#d4a017', Glass:'#7fb4ee', White:'#ffffff', PaintWhite:'#ffffff', Curb:'#c8c3b8' },
};
const mats = {};
let gate;
new GLTFLoader().load('./assets/gate.glb', g => {
  gate = g.scene;
  gate.traverse(o => {
    if (o.isMesh) {
      o.castShadow = o.receiveShadow = true;
      const k = o.material.name.replace('AR_OAUGate_', '');
      mats[k] = o.material;
    }
  });
  // tune the road / grass to a calmer realistic tone
  if (mats.Grass) mats.Grass.color.set('#5f8a3a');
  if (mats.Hedge) mats.Hedge.color.set('#3f6a2c');
  gate.traverse(o => { if (o.isMesh) o.material.envMapIntensity = 0.15; });
  scene.add(gate);
  apply('Warm sand');
});

const ui = document.getElementById('ui');
function apply(name) {
  const p = PALETTES[name];
  for (const k in p) if (mats[k]) {
    if (mats[k].map) { mats[k].map = null; mats[k].needsUpdate = true; }
    mats[k].color.set(p[k]);
  }
  [...ui.children].forEach(b => b.classList.toggle('on', b.textContent === name));
}
Object.keys(PALETTES).forEach(n => {
  const b = document.createElement('button'); b.textContent = n; b.onclick = () => apply(n); ui.appendChild(b);
});

// simple orbit (drag) around the gate
let yaw = 0.55, pitch = 0.18, dist = 42, drag = false, lx = 0, ly = 0;
addEventListener('pointerdown', e => { drag = true; lx = e.clientX; ly = e.clientY; });
addEventListener('pointerup', () => drag = false);
addEventListener('pointermove', e => {
  if (!drag || !orbit) return;
  yaw -= (e.clientX - lx) * 0.005; pitch = Math.max(0.02, Math.min(1.2, pitch + (e.clientY - ly) * 0.004));
  lx = e.clientX; ly = e.clientY;
});
addEventListener('wheel', e => { dist = Math.max(10, Math.min(120, dist + e.deltaY * 0.05)); });
addEventListener('resize', () => { renderer.setSize(innerWidth, innerHeight); camera.aspect = innerWidth / innerHeight; camera.updateProjectionMatrix(); });

const target = new THREE.Vector3(0, 6, 0);
let orbit = false;
addEventListener('keydown', e => {
  if (e.key === 'o') orbit = !orbit;
  if (e.key === 'c') { orbit = true; target.set(car.position.x, 0.8, car.position.z); dist = 9; yaw = 0.7; pitch = 0.12; }
  if (e.key === 'g') { orbit = true; target.set(0, 6, 0); dist = 42; yaw = 0.55; pitch = 0.18; }
  if (e.key === 'r') resetCar();
  if (e.key === 'v') { orbit = true; target.copy(ev.seat).setY(0.8); dist = 4.2; yaw = Math.atan2(ev.out.x, ev.out.z); pitch = 0.12; }
});
const keys = {};
addEventListener('keydown', e => { keys[e.code] = true; if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault(); });
addEventListener('keyup', e => { keys[e.code] = false; });

// ---- driving state ----
const START_Z = -110;
const st = { x: 4, z: START_Z, h: 0, v: 0, steer: 0, roll: 0, spinA: 0, y: 0, pitch: 0, rz: 0 };
const GJ = { rampZ0: -23.6, z0: -18, L: 36, y0: 3.2, A: 7.5, slope: 3.2 / 5.6 };
const ROAD_X = 5.2, Z_MIN = -290, Z_MAX = 1590;
function resetCar() { Object.assign(st, { x: 4, z: START_Z, h: 0, v: 0, steer: 0, roll: 0, y: 0, pitch: 0, rz: 0 }); }
const camPos = new THREE.Vector3(), camLook = new THREE.Vector3(); let camInit = false;
const hud = document.getElementById('info');
const clock = new THREE.Clock();
const entry = { phase: 'loading', t: 0 };

function drive(dt) {
  const ph = entry.phase, live = ph === 'drive', auto = ph === 'run';
  if (ph === 'jump') { jumpStep(dt); return; }
  const up = auto || (live && (keys.KeyW || keys.ArrowUp)), dn = live && (keys.KeyS || keys.ArrowDown);
  const lt = live && (keys.KeyA || keys.ArrowLeft), rt = live && (keys.KeyD || keys.ArrowRight);
  const boost = live && (keys.ShiftLeft || keys.ShiftRight), hb = live && keys.Space;
  const vmax = auto ? 34 : (boost ? 62 : 44);
  if (up) st.v += (st.v < 0 ? 38 : (auto ? 12 : 20)) * dt * (boost ? 1.6 : 1);
  else if (dn) st.v -= (st.v > 0 ? 40 : 14) * dt;
  else st.v -= Math.sign(st.v) * Math.min(Math.abs(st.v), 7 * dt);
  if (hb) st.v -= Math.sign(st.v) * Math.min(Math.abs(st.v), 30 * dt);
  st.v = Math.max(-12, Math.min(vmax, st.v));
  // smooth steering, less at speed
  const want = ((lt ? 1 : 0) - (rt ? 1 : 0)) * (0.55 - Math.min(0.37, Math.abs(st.v) / 120));
  st.steer += (want - st.steer) * Math.min(1, 9 * dt);
  const L = 2.7; // wheelbase feel
  st.h += (st.v / L) * Math.tan(st.steer) * dt;
  st.x += Math.sin(st.h) * st.v * dt;
  st.z += Math.cos(st.h) * st.v * dt;
  // road edges: slide along, lose speed
  if (Math.abs(st.x) > ROAD_X) { st.x = Math.sign(st.x) * ROAD_X; st.v *= 1 - Math.min(1, 1.5 * dt); st.h *= 1 - Math.min(1, 3 * dt); }
  if (st.z < Z_MIN) { st.z = Z_MIN; st.v = Math.max(0, st.v) * 0.5; }
  if (st.z > Z_MAX) { st.z = Z_MAX; st.v = Math.min(0, st.v) * 0.5; }
  st.h = Math.max(-1.2, Math.min(1.2, st.h));
  st.roll += ((-st.steer * st.v * 0.012) - st.roll) * Math.min(1, 6 * dt);
  st.spinA += st.v * dt / 0.3;

  if (auto) {
    if (st.z >= GJ.rampZ0) { st.y = GJ.slope * (st.z - GJ.rampZ0); st.pitch = Math.atan(GJ.slope); }
    if (st.z >= GJ.z0) { entry.phase = 'jump'; st.y = GJ.y0; }
  } else if (live) { st.y = 0; const k = Math.min(1, 10 * dt); st.pitch -= st.pitch * k; st.rz -= st.rz * k; }
  applyPose();
}
function applyPose() {
  car.position.set(st.x, 0.05 + st.y, st.z);
  car.rotation.set(st.pitch, st.h + Math.PI, st.roll * 0.5 + st.rz, 'YXZ');
  wheels.forEach(w => {
    w.spin.rotation.x = -st.spinA * w.flip;
    w.holder.rotation.y = w.base + (w.front ? st.steer * 0.9 : 0);
  });
}
// scripted flight over the gate: smooth arc, nose follows the path, one barrel roll
function jumpStep(dt) {
  st.z += st.v * dt; st.spinA += st.v * dt / 0.3;
  const u = Math.min(1, (st.z - GJ.z0) / GJ.L), pi = Math.PI;
  st.y = GJ.y0 * (1 - u) + GJ.A * Math.sin(pi * u);
  st.pitch = Math.atan((-GJ.y0 + GJ.A * pi * Math.cos(pi * u)) / GJ.L);
  const r = Math.min(1, Math.max(0, (u - 0.12) / 0.74)); st.rz = 2 * pi * r * r * (3 - 2 * r);
  applyPose();
  if (u >= 1) { entry.phase = 'drive'; st.y = 0; st.rz = 0; }
}


// ---- door + person entering the car ----
let person = null, mixer = null, actions = {}, door = null, doorPivot = null, doorSign = 1, doorOpenAng = 0;
const ev = { stand: new THREE.Vector3(), start: new THREE.Vector3(), seat: new THREE.Vector3(), out: new THREE.Vector3(), doorC: new THREE.Vector3(), front: new THREE.Vector3() };
function setupEntry(m) {
  car.rotation.set(0, st.h + Math.PI, 0, 'YXZ'); car.position.set(st.x, 0.05, st.z); scene.updateMatrixWorld(true);
  m.traverse(o => { if (!door && /left.?door/i.test(o.name)) door = o; });
  if (!door) { entry.phase = 'drive'; return; }
  const wb = new THREE.Box3().setFromObject(door); wb.getCenter(ev.doorC);
  const origin = m.localToWorld(new THREE.Vector3(0, 0, 0));
  const dl = m.worldToLocal(ev.doorC.clone());
  doorSign = Math.sign(dl.x) || -1;
  // hinge = front edge (local -z) of the door, outer vertical axis
  const corners = [wb.min, wb.max].map(v => m.worldToLocal(v.clone()));
  const zmin = Math.min(corners[0].z, corners[1].z), zmax = Math.max(corners[0].z, corners[1].z);
  const xo = dl.x, hy = dl.y;
  const hinge = new THREE.Vector3(xo, hy, zmin);
  doorPivot = new THREE.Group(); doorPivot.position.copy(hinge); m.add(doorPivot); doorPivot.attach(door);
  ev.out.copy(m.localToWorld(new THREE.Vector3(doorSign, 0, 0))).sub(origin).setY(0).normalize();
  ev.front.copy(m.localToWorld(new THREE.Vector3(0, 0, -1))).sub(origin).setY(0).normalize();
  ev.seat.copy(m.localToWorld(new THREE.Vector3(doorSign * 0.28, -0.12, 0.1)));
  ev.seat.y = 0.05;
  ev.stand.copy(ev.doorC).addScaledVector(ev.out, 0.95).setY(0.05);
  ev.start.copy(ev.stand).addScaledVector(ev.out, 2.6).addScaledVector(ev.front, -2.4);
  cl.load('./assets/person.glb', g => {
    person = g.scene; person.traverse(o => { if (o.isMesh) { o.castShadow = true; o.frustumCulled = false; } });
    person.scale.setScalar(1); person.position.set(0, 0, 0); scene.add(person); person.updateMatrixWorld(true);
    let headB = null; person.traverse(o => { if (o.isBone && /^head$/i.test(o.name)) headB = o; });
    const hp = new THREE.Vector3(); headB && headB.getWorldPosition(hp);
    person.scale.setScalar(hp.y > 0.01 ? 1.62 / hp.y : 1); window.__person = person;
    mixer = new THREE.AnimationMixer(person);
    g.animations.forEach(a => actions[a.name] = mixer.clipAction(a));
    person.position.copy(ev.start); faceTo(ev.stand);
    actions.Walk_Loop && actions.Walk_Loop.play();
    entry.phase = 'walk'; entry.t = 0;
  });
}

// ---- seated pose (procedural, no sit animation in the model) ----
const SIT = { thigh: -82, calf: 22, armDown: 62, armFwd: 52, fore: 62, seatY: -0.38, back: 0.0 };
let seated = false;
function rotPS(bone, axis, deg) {
  const Qp = person.getWorldQuaternion(new THREE.Quaternion()), pw = bone.parent.getWorldQuaternion(new THREE.Quaternion());
  const Rw = new THREE.Quaternion().setFromAxisAngle(axis.clone().applyQuaternion(Qp), THREE.MathUtils.degToRad(deg));
  bone.quaternion.copy(pw.clone().invert().multiply(Rw).multiply(pw).multiply(bone.quaternion));
  bone.updateMatrixWorld(true);
}
function sitDown() {
  if (!person || seated) return; seated = true;
  Object.values(actions).forEach(a => a.stop());
  let sk = null; person.traverse(o => { if (o.isSkinnedMesh && !sk) sk = o.skeleton; });
  sk.pose(); const B = {}; sk.bones.forEach(b => B[b.name] = b);
  car.attach(person); person.rotation.set(0, Math.PI, 0); person.updateMatrixWorld(true);
  const X = new THREE.Vector3(1, 0, 0), Z = new THREE.Vector3(0, 0, 1);
  ['l', 'r'].forEach(sd => {
    const sg = sd === 'l' ? 1 : -1;
    rotPS(B['thigh_' + sd], X, SIT.thigh); rotPS(B['calf_' + sd], X, SIT.calf);
    rotPS(B['upperarm_' + sd], Z, -sg * SIT.armDown); rotPS(B['upperarm_' + sd], X, -SIT.armFwd);
    rotPS(B['lowerarm_' + sd], X, -SIT.fore);
  });
  rotPS(B['spine_01'], X, -6); // slight recline
  const sp = car.worldToLocal(ev.seat.clone());
  person.position.set(sp.x, SIT.seatY, sp.z + SIT.back);
  window.__B = B;
}
window.__sit = sitDown; window.__SIT = SIT; window.__resit = () => { seated = false; sitDown(); };

function faceTo(v) { if (person) person.rotation.y = Math.atan2(v.x - person.position.x, v.z - person.position.z); }
const lerp = (a, b, t) => a + (b - a) * Math.min(1, Math.max(0, t));
const ease = t => t * t * (3 - 2 * t);
function setDoor(a) { if (doorPivot) doorPivot.rotation.y = doorSign * doorOpenAng * a; }
const camTo = new THREE.Vector3(), lookTo = new THREE.Vector3();
function entryUpdate(dt) {
  entry.t += dt; const t = entry.t;
  if (mixer) mixer.update(dt);
  const WALK = 2.6, OPEN = 1.6, STEP = 1.3, CLOSE = 0.9;
  if (entry.phase === 'walk' && person) {
    const k = Math.min(1, t / WALK); person.position.lerpVectors(ev.start, ev.stand, k); faceTo(ev.stand);
    if (t >= WALK) { entry.phase = 'open'; entry.t = 0; faceTo(ev.doorC);
      actions.Walk_Loop && actions.Walk_Loop.fadeOut(0.2);
      if (actions.Interact) { actions.Interact.reset().setLoop(THREE.LoopOnce, 1); actions.Interact.clampWhenFinished = true; actions.Interact.fadeIn(0.2).play(); }
      else actions.Idle_Loop && actions.Idle_Loop.reset().fadeIn(0.2).play(); }
  } else if (entry.phase === 'open') {
    setDoor(ease((t - 0.35) / 0.9));
    if (t >= OPEN) { entry.phase = 'step'; entry.t = 0; actions.Interact && actions.Interact.fadeOut(0.2); actions.Walk_Loop && actions.Walk_Loop.reset().fadeIn(0.2).play(); }
  } else if (entry.phase === 'step') {
    const k = ease(t / STEP); person.position.lerpVectors(ev.stand, ev.seat, k);
    person.position.y = 0.05 - 0.38 * Math.sin(Math.min(1, t / STEP) * Math.PI / 2); // sink into the seat
    faceTo(ev.seat); person.rotation.y += (0 * k);
    if (t >= STEP) { entry.phase = 'close'; entry.t = 0; sitDown(); }
  } else if (entry.phase === 'close') {
    setDoor(1 - ease(t / CLOSE));
    if (t >= CLOSE) { setDoor(0); entry.phase = 'run'; camInit = true; }
  }
  // cinematic camera: 3/4 view from the door side, easing back
  camTo.copy(ev.doorC).addScaledVector(ev.out, 2.2).addScaledVector(ev.front, 7.5).setY(1.5);
  lookTo.copy(ev.doorC).addScaledVector(ev.out, 0.8).setY(0.8);
  camPos.lerp(camTo, 1 - Math.exp(-3 * dt)); camLook.lerp(lookTo, 1 - Math.exp(-5 * dt));
  if (!camInit) { camPos.copy(camTo); camLook.copy(lookTo); camInit = true; }
  camera.position.copy(camPos); camera.lookAt(camLook);
}
function replayEntry() {
  if (!person) return; resetCar(); setDoor(0); if (seated) { scene.attach(person); seated = false; } person.visible = true; person.position.copy(ev.start); faceTo(ev.stand);
  Object.values(actions).forEach(a => a.stop()); actions.Walk_Loop && actions.Walk_Loop.reset().play(); entry.phase = 'walk'; entry.t = 0; camInit = false;
}
window.__ff = sec => { for (let i = 0; i < sec * 30; i++) { if (entry.phase === 'drive') break; entryUpdate(1 / 30); } };
window.__entry = entry; window.__replay = replayEntry;
addEventListener('keydown', e => { if (e.key === 'p' || e.key === 'P') replayEntry(); });
addEventListener('keydown', e => { if (e.code === 'Enter' && entry.phase !== 'drive' && entry.phase !== 'loading') { setDoor(0); sitDown(); entry.phase = 'run'; } });

function chase(dt) {
  const back = 7.5 + Math.abs(st.v) * 0.05, hgt = 2.6 + Math.abs(st.v) * 0.012;
  const want = new THREE.Vector3(st.x - Math.sin(st.h) * back, hgt, st.z - Math.cos(st.h) * back);
  const look = new THREE.Vector3(st.x + Math.sin(st.h) * 6, 1.0, st.z + Math.cos(st.h) * 6);
  if (!camInit) { camPos.copy(want); camLook.copy(look); camInit = true; }
  const k = 1 - Math.exp(-6 * dt);
  camPos.lerp(want, k); camLook.lerp(look, 1 - Math.exp(-10 * dt));
  camera.position.copy(camPos); camera.lookAt(camLook);
  const fov = 50 + Math.min(22, Math.abs(st.v) * 0.35);
  if (Math.abs(camera.fov - fov) > 0.05) { camera.fov += (fov - camera.fov) * Math.min(1, 4 * dt); camera.updateProjectionMatrix(); }
}

const sideCamT = new THREE.Vector3(), sideLook = new THREE.Vector3();
function sideCam(dt) {
  // swing out to the side of the gate to watch the car fly over it
  sideCamT.set(st.x + 15, 3.4, -24);
  sideLook.set(st.x, 0.05 + st.y + 0.6, st.z + (entry.phase === 'jump' ? 2 : 0));
  camPos.lerp(sideCamT, 1 - Math.exp(-2.2 * dt)); camLook.lerp(sideLook, 1 - Math.exp(-9 * dt));
  camera.position.copy(camPos); camera.lookAt(camLook);
  if (Math.abs(camera.fov - 60) > 0.05) { camera.fov += (60 - camera.fov) * Math.min(1, 3 * dt); camera.updateProjectionMatrix(); }
}
function tick(dt) {
  if (car.children.length) drive(dt);
  sun.target.position.set(st.x, 0, st.z); sun.position.set(st.x + 35, 50, st.z - 55);
  if (orbit) {
    camera.position.set(
      target.x + Math.sin(yaw) * Math.cos(pitch) * dist,
      target.y + Math.sin(pitch) * dist,
      target.z + Math.cos(yaw) * Math.cos(pitch) * dist);
    camera.lookAt(target);
  } else if (entry.phase === 'jump' || (entry.phase === 'run' && st.z > -52)) sideCam(dt);
  else if (entry.phase !== 'drive' && entry.phase !== 'run') entryUpdate(dt);
  else chase(dt);
  hud.textContent = 'OAU Run · ' + Math.round(Math.abs(st.v) * 3.6) + ' km/h · W/S gas/brake · A/D steer · Shift boost · Space handbrake · R reset · O free-look';
  renderer.render(scene, camera);
}
window.__tick = tick; window.__r = renderer; window.__cam = camera;
renderer.setAnimationLoop(() => tick(Math.min(0.05, clock.getDelta())));


// ---- road extension beyond the gate model's own road (ends at z=70) ----
function buildRoad(Z0, Z1) {
  const len = Z1 - Z0, zc = (Z0 + Z1) / 2;
  const mk = (w, h, x, y, color, rough = 0.95, tex) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, len), new THREE.MeshStandardMaterial({ color, roughness: rough, map: tex || null }));
    m.position.set(x, y, zc); m.receiveShadow = true; scene.add(m); return m;
  };
  // asphalt with a dashed edge line texture
  const c = document.createElement('canvas'); c.width = 64; c.height = 256; const g = c.getContext('2d');
  g.fillStyle = '#2b2b30'; g.fillRect(0, 0, 64, 256);
  for (let i = 0; i < 900; i++) { g.fillStyle = `rgba(${90 + Math.random() * 60},${90 + Math.random() * 60},${90 + Math.random() * 60},0.12)`; g.fillRect(Math.random() * 64, Math.random() * 256, 1.5, 1.5); }
  g.fillStyle = '#e8e4d4'; g.fillRect(2, 0, 2, 256); g.fillRect(60, 0, 2, 256);          // edge lines
  g.fillStyle = '#e8e4d4'; g.fillRect(31, 20, 2, 90);                                    // centre dash
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(1, len / 12); tex.anisotropy = 8;
  [-3.65, 3.65].forEach(x => mk(3.4, 0.1, x, 0.0, 0xffffff, 0.9, tex));
  mk(3.7, 0.24, 0, 0.0, 0x5f8a3a);                 // green median
  [-6.15, 6.15].forEach(x => mk(1.7, 0.3, x, 0.0, 0xb9b2a4)); // pavements
}
buildRoad(69.5, 1600);       // campus road beyond the gate
buildRoad(-300, -39.5);      // approach road before the gate
{
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(2400, 2400), new THREE.MeshStandardMaterial({ color: 0x6f8a45, roughness: 1 }));
  ground.rotation.x = -Math.PI / 2; ground.position.set(0, -0.03, 450); ground.receiveShadow = true; scene.add(ground);
  // launch ramp in the right-hand lane
  const GJr = { z0: -23.6, z1: -18, h: 3.2 }, rl = Math.hypot(GJr.z1 - GJr.z0, GJr.h), ang = Math.atan2(GJr.h, GJr.z1 - GJr.z0);
  const ramp = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.25, rl), new THREE.MeshStandardMaterial({ color: 0xd9a520, roughness: 0.7 }));
  ramp.position.set(4, GJr.h / 2 - 0.1, (GJr.z0 + GJr.z1) / 2); ramp.rotation.x = -ang; ramp.castShadow = ramp.receiveShadow = true; scene.add(ramp);
}

// ---- car (Jaagrav test model, Draco) ----
const dl = new DRACOLoader(); dl.setDecoderPath('./vendor/draco/');
const cl = new GLTFLoader(); cl.setDRACOLoader(dl);
const car = new THREE.Group(); scene.add(car); const wheels = [];
cl.load('./assets/car_chassis.glb', g => {
  const m = g.scene;
  m.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  const box = new THREE.Box3().setFromObject(m), sz = box.getSize(new THREE.Vector3());
  window.__carInfo = { size: sz.toArray(), min: box.min.toArray() };
  const k = 4.4 / Math.max(sz.x, sz.z); m.scale.setScalar(k);
  const b2 = new THREE.Box3().setFromObject(m); m.position.y -= b2.min.y; m.position.x -= (b2.min.x + b2.max.x) / 2; m.position.z -= (b2.min.z + b2.max.z) / 2;
  m.traverse(o => { if (o.isMesh) { const ms = Array.isArray(o.material) ? o.material : [o.material]; ms.forEach(x => { x.envMapIntensity = 0.4; if (x.name === 'car_paint') { x.color.set('#c8141c'); x.metalness = 0.55; x.roughness = 0.22; x.envMapIntensity = 0.9; x.color.set('#b30f18'); } }); } });
  cl.load('./assets/car_wheel.glb', w => {
    const wb = new THREE.Box3().setFromObject(w.scene), ws = wb.getSize(new THREE.Vector3());
    window.__wheelInfo = ws.toArray();
    const R = ws.y / 2, cx = (wb.min.x + wb.max.x) / 2, cy = (wb.min.y + wb.max.y) / 2, cz = (wb.min.z + wb.max.z) / 2;
    const WS = 0.86, WX = 0.54, WZ = 1.0; window.__wp = { WS, WX, WZ };
    [[-1, 1], [1, 1], [-1, -1], [1, -1]].forEach(([sx, sz]) => {
      const wc = w.scene.clone(true); wc.traverse(o => { if (o.isMesh) { o.castShadow = true; (Array.isArray(o.material) ? o.material : [o.material]).forEach(q => q.envMapIntensity = 0.4); } });
      const holder = new THREE.Group(); holder.scale.setScalar(WS); wc.position.set(-cx, -cy, -cz); const spin = new THREE.Group(); spin.add(wc); holder.add(spin);
      if (sx < 0) holder.rotation.y = Math.PI;
      holder.position.set(sx * WX, -0.375 - 0.09 + R * WS, sz * WZ); m.add(holder); wheels.push({ holder, spin, front: sz < 0, base: holder.rotation.y, flip: sx < 0 ? -1 : 1 });
    });
  });
  const rcast = new THREE.Raycaster();
  window.groundY = (x, z) => { rcast.set(new THREE.Vector3(x, 50, z), new THREE.Vector3(0, -1, 0)); const h = rcast.intersectObject(gate, true)[0]; return h ? h.point.y : null; };
  window.__ground = [-9, -7, -5, -3, -1, 0, 1, 3, 5, 7, 9].map(x => [x, window.groundY(x, 18)]);
  car.add(m); m.position.y += 0.09 * k; car.position.set(4, 0.05, 18);
  doorOpenAng = 1.0; setupEntry(m);
  window.__car = car;
}, undefined, () => {
  // No car model in assets/ (the licensed-unclear one is not shipped): use a simple placeholder car.
  const body = new THREE.Mesh(new THREE.BoxGeometry(1.8, 0.5, 4.2), new THREE.MeshStandardMaterial({ color: '#b30f18', roughness: 0.3, metalness: 0.5 }));
  body.position.y = 0.55; body.castShadow = true;
  const cab = new THREE.Mesh(new THREE.BoxGeometry(1.5, 0.4, 1.8), new THREE.MeshStandardMaterial({ color: '#222a33', roughness: 0.2 }));
  cab.position.set(0, 0.97, 0.2); cab.castShadow = true;
  const g = new THREE.Group(); g.add(body, cab);
  [[-0.95, 1.3], [0.95, 1.3], [-0.95, -1.3], [0.95, -1.3]].forEach(([x, z]) => {
    const w = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.3, 20), new THREE.MeshStandardMaterial({ color: '#111', roughness: 0.8 }));
    w.rotation.z = Math.PI / 2; w.position.set(x, 0.36, z); w.castShadow = true; g.add(w);
  });
  car.add(g); car.position.set(4, 0.05, 18); entry.phase = 'drive'; window.__car = car;
});
