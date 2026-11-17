/* Procedural sound for OAU Run: engine, wind, siren and one-shot effects, all synthesised with WebAudio (no files). */
export function createSfx(getAc, isMuted) {
  let ac = null, master = null, eng = null, wind = null, sirenN = null, noiseBuf = null, lastSiren = false;
  const ready = () => {
    ac = getAc(); if (!ac) return false;
    if (!master) {
      master = ac.createGain(); master.gain.value = 0.9; master.connect(ac.destination);
      noiseBuf = ac.createBuffer(1, ac.sampleRate * 2, ac.sampleRate); const d = noiseBuf.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    }
    return true;
  };
  const noise = (loop = true) => { const s = ac.createBufferSource(); s.buffer = noiseBuf; s.loop = loop; return s; };
  const env = (g, t, a, peak, d) => { g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(peak, t + a); g.gain.exponentialRampToValueAtTime(0.0001, t + a + d); };
  function engineStart() {
    if (!ready() || eng) return;
    const g = ac.createGain(); g.gain.value = 0; const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 900; lp.connect(g); g.connect(master);
    const o1 = ac.createOscillator(); o1.type = "sawtooth"; const o2 = ac.createOscillator(); o2.type = "square"; const o3 = ac.createOscillator(); o3.type = "sawtooth";
    const g1 = ac.createGain(), g2 = ac.createGain(), g3 = ac.createGain(); g1.gain.value = 0.5; g2.gain.value = 0.18; g3.gain.value = 0.22;
    o1.connect(g1).connect(lp); o2.connect(g2).connect(lp); o3.connect(g3).connect(lp); [o1, o2, o3].forEach((o) => o.start());
    eng = { g, lp, o1, o2, o3 };
    const wg = ac.createGain(); wg.gain.value = 0; const bp = ac.createBiquadFilter(); bp.type = "bandpass"; bp.frequency.value = 900; bp.Q.value = 0.6; const ws = noise(); ws.connect(bp).connect(wg).connect(master); ws.start();
    wind = { g: wg, bp, ws };
  }
  function engineUpdate(v, boost, air) {
    if (!eng || !ac) return;
    const t = ac.currentTime, k = Math.min(1.4, v / 33), f = 48 + k * 70 + (boost ? 38 : 0) + (air ? 25 : 0);
    eng.o1.frequency.setTargetAtTime(f, t, 0.08); eng.o2.frequency.setTargetAtTime(f * 0.5, t, 0.08); eng.o3.frequency.setTargetAtTime(f * 2.01, t, 0.08);
    eng.lp.frequency.setTargetAtTime(500 + k * 900 + (boost ? 900 : 0), t, 0.1);
    eng.g.gain.setTargetAtTime(isMuted() ? 0 : 0.16 + k * 0.1 + (boost ? 0.07 : 0), t, 0.1);
    wind.g.gain.setTargetAtTime(isMuted() ? 0 : Math.min(0.42, k * k * 0.26 + (boost ? 0.14 : 0) + (air ? 0.08 : 0)), t, 0.15); wind.bp.frequency.setTargetAtTime(500 + k * 1100, t, 0.15);
  }
  function engineStop() {
    siren(false);
    if (!ac) return;
    if (eng) { const e = eng; eng = null; e.g.gain.setTargetAtTime(0, ac.currentTime, 0.08); setTimeout(() => { try { e.o1.stop(); e.o2.stop(); e.o3.stop(); } catch (x) {} }, 400); }
    if (wind) { const w = wind; wind = null; w.g.gain.setTargetAtTime(0, ac.currentTime, 0.08); setTimeout(() => { try { w.ws.stop(); } catch (x) {} }, 400); }
  }
  function siren(on) {
    if (on === lastSiren) return; lastSiren = on; if (!ready()) return;
    if (!on) { if (sirenN) { const s = sirenN; sirenN = null; s.g.gain.setTargetAtTime(0, ac.currentTime, 0.05); setTimeout(() => { try { s.o.stop(); s.lfo.stop(); } catch (x) {} }, 300); } return; }
    if (isMuted()) return;
    const o = ac.createOscillator(); o.type = "triangle"; o.frequency.value = 800; const lfo = ac.createOscillator(); lfo.frequency.value = 1.6; const lg = ac.createGain(); lg.gain.value = 220; lfo.connect(lg).connect(o.frequency);
    const g = ac.createGain(); g.gain.value = 0.0001; g.gain.setTargetAtTime(0.07, ac.currentTime, 0.1); o.connect(g).connect(master); o.start(); lfo.start(); sirenN = { o, lfo, g };
  }
  function tone(f0, f1, dur, type, vol, delay = 0) {
    const t = ac.currentTime + delay, o = ac.createOscillator(), g = ac.createGain(); o.type = type; o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    env(g, t, 0.01, vol, dur); o.connect(g).connect(master); o.start(t); o.stop(t + dur + 0.05);
  }
  function burst(freq, q, dur, vol, sweepTo, delay = 0) {
    const t = ac.currentTime + delay, s = noise(false), f = ac.createBiquadFilter(), g = ac.createGain(); f.type = "bandpass"; f.Q.value = q; f.frequency.setValueAtTime(freq, t); if (sweepTo) f.frequency.exponentialRampToValueAtTime(sweepTo, t + dur);
    env(g, t, 0.015, vol, dur); s.connect(f).connect(g).connect(master); s.start(t, Math.random()); s.stop(t + dur + 0.1);
  }
  const FX = {
    launch() { tone(140, 520, 0.55, "sawtooth", 0.16); burst(600, 0.7, 0.5, 0.22, 2400); },
    land() { tone(110, 38, 0.32, "sine", 0.55); burst(220, 0.5, 0.2, 0.3, 90); },
    whoosh() { burst(500, 1.2, 0.35, 0.3, 3200); },
    pickup() { tone(660, 660, 0.12, "triangle", 0.22); tone(990, 990, 0.2, "triangle", 0.22, 0.09); },
    crash() { burst(180, 0.4, 0.45, 0.8, 60); tone(90, 32, 0.4, "square", 0.3); },
    boost() { tone(180, 900, 0.5, "sawtooth", 0.13); burst(900, 0.8, 0.6, 0.26, 3600); },
    combo(n) { const base = 520 + Math.min(n, 8) * 70; tone(base, base, 0.1, "square", 0.1); tone(base * 1.5, base * 1.5, 0.16, "square", 0.1, 0.08); },
    win() { [523, 659, 784, 1047].forEach((f, i) => tone(f, f, 0.35, "triangle", 0.25, i * 0.12)); },
    lose() { [392, 330, 262, 196].forEach((f, i) => tone(f, f * 0.96, 0.4, "sawtooth", 0.16, i * 0.18)); },
    go() { tone(440, 440, 0.12, "square", 0.14); tone(880, 880, 0.3, "square", 0.16, 0.14); },
  };
  return { engineStart, engineUpdate, engineStop, siren, play(n, a) { if (isMuted() || !ready()) return; try { FX[n] && FX[n](a); } catch (e) {} } };
}
