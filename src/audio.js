// Web Audio API — synthetic sound effects for casting (no mp3 files)

let _ctx = null

function getCtx() {
  if (!_ctx) _ctx = new (window.AudioContext || window.webkitAudioContext)()
  if (_ctx.state === 'suspended') _ctx.resume()
  return _ctx
}

export function isSoundOn() {
  return localStorage.getItem('kd-sound') !== 'off'
}

export function setSoundEnabled(on) {
  localStorage.setItem('kd-sound', on ? 'on' : 'off')
}

// Sound 1: Tung đồng xu — metallic spin, ~1s
// Three layers: initial strike + spinning AM tone + high overtone
export function playCoinToss() {
  if (!isSoundOn()) return
  const ctx = getCtx()
  const t = ctx.currentTime

  // Initial metallic strike
  const s = ctx.createOscillator()
  const sg = ctx.createGain()
  s.type = 'triangle'
  s.frequency.setValueAtTime(2800, t)
  s.frequency.exponentialRampToValueAtTime(550, t + 0.09)
  sg.gain.setValueAtTime(0.38, t)
  sg.gain.exponentialRampToValueAtTime(0.001, t + 0.12)
  s.connect(sg); sg.connect(ctx.destination)
  s.start(t); s.stop(t + 0.15)

  // Spinning tone with LFO amplitude modulation (creates "brr" flip effect)
  const spin = ctx.createOscillator()
  const spinEnv = ctx.createGain()
  const lfo = ctx.createOscillator()
  const lfoAmp = ctx.createGain()
  spin.type = 'sine'
  spin.frequency.setValueAtTime(1100, t + 0.04)
  spin.frequency.exponentialRampToValueAtTime(190, t + 1.0)
  spinEnv.gain.setValueAtTime(0.0, t)
  spinEnv.gain.linearRampToValueAtTime(0.22, t + 0.1)
  spinEnv.gain.exponentialRampToValueAtTime(0.001, t + 1.0)
  lfo.type = 'sine'
  lfo.frequency.setValueAtTime(17, t)
  lfo.frequency.exponentialRampToValueAtTime(3, t + 1.0)
  lfoAmp.gain.setValueAtTime(0.18, t)
  lfoAmp.gain.linearRampToValueAtTime(0.03, t + 1.0)
  lfo.connect(lfoAmp); lfoAmp.connect(spinEnv.gain)
  spin.connect(spinEnv); spinEnv.connect(ctx.destination)
  lfo.start(t); lfo.stop(t + 1.05)
  spin.start(t + 0.04); spin.stop(t + 1.05)

  // High metallic ring (fades faster)
  const h = ctx.createOscillator()
  const hg = ctx.createGain()
  h.type = 'triangle'
  h.frequency.setValueAtTime(4600, t)
  h.frequency.exponentialRampToValueAtTime(1400, t + 0.65)
  hg.gain.setValueAtTime(0.09, t)
  hg.gain.exponentialRampToValueAtTime(0.001, t + 0.65)
  h.connect(hg); hg.connect(ctx.destination)
  h.start(t); h.stop(t + 0.7)
}

// Sound 2: Đồng xu rơi — metal hitting wood, 0.2s
// Low thud + short metallic click on impact
export function playCoinLand() {
  if (!isSoundOn()) return
  const ctx = getCtx()
  const t = ctx.currentTime

  // Woody thud
  const o1 = ctx.createOscillator()
  const g1 = ctx.createGain()
  o1.type = 'sine'
  o1.frequency.setValueAtTime(210, t)
  o1.frequency.exponentialRampToValueAtTime(58, t + 0.18)
  g1.gain.setValueAtTime(0.52, t)
  g1.gain.exponentialRampToValueAtTime(0.001, t + 0.2)
  o1.connect(g1); g1.connect(ctx.destination)
  o1.start(t); o1.stop(t + 0.22)

  // Metallic click
  const o2 = ctx.createOscillator()
  const g2 = ctx.createGain()
  o2.type = 'triangle'
  o2.frequency.setValueAtTime(4200, t)
  o2.frequency.exponentialRampToValueAtTime(950, t + 0.065)
  g2.gain.setValueAtTime(0.2, t)
  g2.gain.exponentialRampToValueAtTime(0.001, t + 0.08)
  o2.connect(g2); g2.connect(ctx.destination)
  o2.start(t); o2.stop(t + 0.1)
}

// Sound 3: Hoàn thành 1 hào — soft bell, 0.15s
export function playLineComplete() {
  if (!isSoundOn()) return
  const ctx = getCtx()
  const t = ctx.currentTime

  const o = ctx.createOscillator()
  const g = ctx.createGain()
  o.type = 'sine'
  o.frequency.setValueAtTime(1047, t)  // C6
  g.gain.setValueAtTime(0.0, t)
  g.gain.linearRampToValueAtTime(0.26, t + 0.006)
  g.gain.exponentialRampToValueAtTime(0.001, t + 0.15)
  o.connect(g); g.connect(ctx.destination)
  o.start(t); o.stop(t + 0.18)
}

// Sound 4: Hoàn thành 6 hào — resonant bell chime, 0.5s
// Three harmonics for a richer "ancient bowl" feel
export function playHexagramComplete() {
  if (!isSoundOn()) return
  const ctx = getCtx()
  const t = ctx.currentTime

  const bell = (freq, amp, dur) => {
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'sine'
    o.frequency.setValueAtTime(freq, t)
    g.gain.setValueAtTime(0.0, t)
    g.gain.linearRampToValueAtTime(amp, t + 0.012)
    g.gain.exponentialRampToValueAtTime(0.001, t + dur)
    o.connect(g); g.connect(ctx.destination)
    o.start(t); o.stop(t + dur + 0.05)
  }

  bell(523, 0.32, 0.5)   // C5 — fundamental
  bell(659, 0.17, 0.38)  // E5 — major third
  bell(784, 0.11, 0.28)  // G5 — fifth
  bell(1047, 0.13, 0.32) // C6 — octave
}
