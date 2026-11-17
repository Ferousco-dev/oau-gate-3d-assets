"use strict";
/* OAU Run: UI, wallet and flow. No backend, no account. Everything lives in localStorage. */
const PRICE = 0.4, START_CGPA = 5.0, KEY = "oaurun.v2";
const $ = (id) => document.getElementById(id);
const app = $("app");
const today = () => new Date().toLocaleDateString("en-CA");
const nextMidnight = () => { const d = new Date(); d.setHours(24, 0, 0, 0); return d; };
const fmt = (n) => (Math.round(n * 100) / 100).toFixed(2);

/* ---------- state ---------- */
function load() {
  let s = null;
  try { s = JSON.parse(localStorage.getItem(KEY)); } catch (e) {}
  if (!s || typeof s.cgpa !== "number") s = { name: "", cgpa: START_CGPA, day: today(), tickets: 0, muted: false };
  if (s.day !== today()) { s.cgpa = START_CGPA; s.day = today(); }       // a new day resets your CGPA
  return s;
}
let S = load();
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} };
const canBuy = () => S.cgpa + 1e-9 >= PRICE;
const mode = (m) => { app.dataset.mode = m; };
const wallet = () => { $("cgpa").textContent = fmt(S.cgpa); $("hi").textContent = S.name ? "Hi, " + S.name : ""; };
wallet();

/* ---------- landing ---------- */
$("name").value = S.name || "";
let ready = false;
function setReady() { ready = true; $("enter").disabled = false; $("enter").textContent = S.name ? "Continue" : "Enter campus"; $("loadbar").style.display = "none"; }
$("enter").addEventListener("click", () => {
  S.name = ($("name").value.trim() || "Student").slice(0, 16); save(); wallet();
  OAU3D.unlockAudio(); OAU3D.setMuted(S.muted);
  toLobby(true);
});
$("name").addEventListener("keydown", (e) => { if (e.key === "Enter" && ready) $("enter").click(); });

function toLobby(first) {
  OAU3D.enterLobby(first);
  if (!canBuy()) { mode("locked"); tick(); } else mode("lobby");
}

/* ---------- out of CGPA: come back tomorrow ---------- */
let timer;
function tick() {
  clearInterval(timer);
  const run = () => {
    const ms = nextMidnight() - new Date();
    if (ms <= 0 || S.day !== today()) { S = load(); save(); wallet(); clearInterval(timer); mode("lobby"); return; }
    const t = Math.floor(ms / 1000), p = (n) => String(n).padStart(2, "0");
    $("count").textContent = `${p(Math.floor(t / 3600))}:${p(Math.floor(t % 3600 / 60))}:${p(t % 60)}`;
  };
  run(); timer = setInterval(run, 1000);
}

/* ---------- ticket sheet (opens when you tap a hawker) ---------- */
const sheet = $("sheet");
function openSheet(h) {
  if (app.dataset.mode !== "lobby") return;
  $("shName").textContent = h.name; $("shLine").textContent = `"${h.line}"`;
  $("shBal").textContent = fmt(S.cgpa); $("shAfter").textContent = fmt(Math.max(0, S.cgpa - PRICE));
  $("pay").disabled = !canBuy();
  sheet.classList.add("open"); sheet.setAttribute("aria-hidden", "false"); $("scrim").classList.add("on");
}
function closeSheet() { sheet.classList.remove("open", "drag"); sheet.style.transform = ""; sheet.setAttribute("aria-hidden", "true"); $("scrim").classList.remove("on"); }
let y0 = null, dy = 0;
$("grab").addEventListener("pointerdown", (e) => { $("grab").setPointerCapture(e.pointerId); y0 = e.clientY; dy = 0; sheet.classList.add("drag"); });
$("grab").addEventListener("pointermove", (e) => { if (y0 === null) return; dy = Math.max(0, e.clientY - y0); sheet.style.transform = `translateY(${dy}px)`; });
const upSheet = () => { if (y0 === null) return; y0 = null; sheet.classList.remove("drag"); sheet.style.transform = ""; if (dy > 90) closeSheet(); };
$("grab").addEventListener("pointerup", upSheet); $("grab").addEventListener("pointercancel", upSheet);
$("scrim").addEventListener("click", closeSheet); $("cancel").addEventListener("click", closeSheet);

$("pay").addEventListener("click", () => {
  if (!canBuy()) return;
  S.cgpa = Math.round((S.cgpa - PRICE) * 100) / 100; S.tickets++; save();
  $("wallet").classList.remove("hit"); void $("wallet").offsetWidth; $("wallet").classList.add("hit"); wallet();
  closeSheet(); sfx("pay"); countdown();
});

function countdown() {                       // no 3-2-1: the car starts by itself and flies the gate
  OAU3D.prepareRun(); startRun();
  const el = $("countdown"); el.textContent = "GO!"; el.style.animation = "none"; void el.offsetWidth; el.style.animation = ""; setTimeout(() => (el.textContent = ""), 700);
}
function startRun() {
  mode("run"); sfx("engine");
  OAU3D.run({ cgpa: S.cgpa, name: S.name, onEnd: (r) => {
    S.cgpa = Math.round(r.cgpa * 100) / 100; save(); wallet(); mode("end");
    showEnd(r);
  } });
}
function showEnd(r) {
  const g = r.kind === "grad";
  $("end").innerHTML = g
    ? `<div class="card"><div class="cap">🎓</div><h1>${S.name}, you graduated!</h1><p class="sub">You reached the Students' Union without a carryover.</p><div class="bignum">${fmt(r.cgpa)}</div><small>final CGPA (was ${fmt(r.start)})</small><button class="cta">Back to the gate</button></div>`
    : `<div class="card caught"><div class="cap">📚</div><h1>Carryover!</h1><p class="sub">${r.by} caught you. −0.30 CGPA.</p><div class="bignum">${fmt(r.cgpa)}</div><small>CGPA left (was ${fmt(r.start)})</small><button class="cta">Back to the gate</button></div>`;
  $("end").querySelector("button").onclick = () => toLobby(false);
}

/* ---------- pause ---------- */
$("gpause").addEventListener("click", () => { OAU3D.pause(true); mode("pause"); });
$("resume").addEventListener("click", () => { OAU3D.pause(false); mode("run"); });
$("quit").addEventListener("click", () => { OAU3D.pause(false); toLobby(false); });

/* ---------- sound ---------- */
const SFX = {};
function sfx(n) { if (S.muted) return; try { (SFX[n] || (SFX[n] = new Audio(`assets/sound/${n}.mp3`))).cloneNode().play().catch(() => {}); } catch (e) {} }
$("mute").textContent = S.muted ? "🔇" : "🔊";
$("mute").addEventListener("click", () => { S.muted = !S.muted; save(); $("mute").textContent = S.muted ? "🔇" : "🔊"; if (window.OAU3D) OAU3D.setMuted(S.muted); });

/* ---------- developer cheat: tap the logo 7 times (or ?dev=1) ---------- */
let taps = 0, tt;
$("logo").addEventListener("click", () => { taps++; clearTimeout(tt); tt = setTimeout(() => (taps = 0), 1500); if (taps >= 7) { taps = 0; dev(); } });
function dev() { S.cgpa = START_CGPA; S.day = today(); save(); wallet(); if (app.dataset.mode === "locked") { clearInterval(timer); mode("lobby"); } }
window.oauDev = dev;
if (/[?&]dev=1/.test(location.search)) dev();

/* ---------- hooks the 3D module calls ---------- */
window.OAUUI = { setReady, openSheet, progress: (p) => { $("gpct").style.width = Math.round(p * 100) + "%"; }, failed: (e) => { $("enter").textContent = "Could not load"; $("enter").disabled = true; console.error(e); } };
if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

/* keyboard: Esc or P pauses / resumes */
addEventListener("keydown", (e) => {
  if (e.code !== "Escape" && e.code !== "KeyP") return;
  if (app.dataset.mode === "run") { OAU3D.pause(true); mode("pause"); } else if (app.dataset.mode === "pause") { OAU3D.pause(false); mode("run"); }
});
