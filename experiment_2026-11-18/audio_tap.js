// Injected before page scripts: taps everything routed to AudioContext.destination
// and stores a 10 ms envelope (RMS, peak, max sample-to-sample step) with context timestamps.
(() => {
  const BLOCK = 480 // 10 ms at 48 kHz (recomputed from sampleRate)
  const rec = { sr: 0, t: [], rms: [], peak: [], step: [], marks: [] }
  window.__rec = rec
  const taps = new WeakMap()
  const origConnect = AudioNode.prototype.connect
  function tapFor(ctx) {
    let tap = taps.get(ctx)
    if (tap) return tap
    const sp = ctx.createScriptProcessor(4096, 1, 1)
    const mute = ctx.createGain()
    mute.gain.value = 0
    origConnect.call(sp, mute)
    origConnect.call(mute, ctx.destination)
    rec.sr = ctx.sampleRate
    window.__ctx = ctx
    const block = Math.round(ctx.sampleRate / 100)
    let last = 0
    sp.onaudioprocess = (e) => {
      const x = e.inputBuffer.getChannelData(0)
      for (let o = 0; o + block <= x.length; o += block) {
        let s = 0, p = 0, st = 0
        for (let i = o; i < o + block; i++) {
          const v = x[i]
          s += v * v
          const a = v < 0 ? -v : v
          if (a > p) p = a
          const d = v - last
          const ad = d < 0 ? -d : d
          if (ad > st) st = ad
          last = v
        }
        rec.t.push(e.playbackTime + o / ctx.sampleRate)
        rec.rms.push(Math.sqrt(s / block))
        rec.peak.push(p)
        rec.step.push(st)
      }
    }
    tap = sp
    taps.set(ctx, tap)
    return tap
  }
  AudioNode.prototype.connect = function (dest, ...rest) {
    const r = origConnect.call(this, dest, ...rest)
    try {
      if (dest instanceof AudioDestinationNode && !(this === tapFor(this.context))) {
        origConnect.call(this, tapFor(this.context))
      }
    } catch (e) { /* ignore */ }
    return r
  }
  window.__mark = (label) => {
    const ctx = window.__ctx
    rec.marks.push({ label, t: ctx ? ctx.currentTime : null, wall: Date.now() })
  }
})()
