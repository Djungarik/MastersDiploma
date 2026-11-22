import { test } from 'node:test'
import assert from 'node:assert/strict'
import { audioEngine } from './audioEngine.js'

// Minimal fake of the Web Audio objects used by the engine: records automation calls
function fakeParam(initial = 0) {
  return {
    value: initial,
    calls: [],
    cancelScheduledValues(t) { this.calls.push(['cancel', t]) },
    setValueAtTime(v, t) { this.calls.push(['set', v, t]); this.value = v },
    linearRampToValueAtTime(v, t) { this.calls.push(['ramp', v, t]) },
    connect() {},
  }
}
function fakeNode() {
  return { connect() {}, disconnect() {}, start() {}, stop() {}, frequency: fakeParam(), detune: fakeParam(), Q: fakeParam(), gain: fakeParam() }
}
// Audio clock that follows real time from 10 s, unless it is frozen by the test
function fakeContext() {
  const t0 = Date.now()
  return {
    frozen: null,
    get currentTime() { return this.frozen ?? 10 + (Date.now() - t0) / 1000 },
    state: 'running',
    sampleRate: 48000,
    createOscillator: fakeNode,
    createBiquadFilter: fakeNode,
    createGain: fakeNode,
    createBufferSource: fakeNode,
    createBuffer: () => ({ getChannelData: () => new Float32Array(16) }),
    resume: async () => {},
  }
}
function setup({ gain = 0.7 } = {}) {
  audioEngine.audioContext = fakeContext()
  audioEngine.masterGain = { gain: fakeParam(gain), connect() {} }
  audioEngine.isInitialized = true
  audioEngine.isPlaying = true
  audioEngine.currentMood = 'calm'
  audioEngine.masterVolume = gain
  audioEngine.nodes = []
  audioEngine.transition = null
  return audioEngine.masterGain.gain
}
const ramps = (g) => g.calls.filter((c) => c[0] === 'ramp').map((c) => c[1])

test('transition starts the fade-out from the current gain value (no jump)', async () => {
  const g = setup()
  const done = audioEngine.crossfadeTo(null, 0.2, 'epic')
  await new Promise((r) => setTimeout(r, 20))
  assert.equal(g.calls[0][0], 'cancel')
  assert.deepEqual(g.calls[1].slice(0, 2), ['set', 0.7])
  assert.equal(g.calls[2][0], 'ramp')
  assert.equal(g.calls[2][1], 0)
  await done
})

test('the returned promise resolves only after the fade-in has finished', async () => {
  const g = setup()
  const start = Date.now()
  await audioEngine.crossfadeTo(null, 0.2, 'epic')
  assert.ok(Date.now() - start >= 190, 'resolved before the end of the transition')
  assert.equal(audioEngine.currentMood, 'epic')
  assert.deepEqual(ramps(g), [0, 0.7])
  assert.equal(audioEngine.isTransitioning(), false)
})

test('generators are not stopped before the audio clock reaches the end of the fade-out', async () => {
  setup()
  const ctx = audioEngine.audioContext
  ctx.frozen = 10
  const done = audioEngine.crossfadeTo(null, 0.2, 'mystery')
  await new Promise((r) => setTimeout(r, 150))   // page timer has fired, audio clock has not moved
  assert.equal(audioEngine.currentMood, 'calm')
  assert.equal(audioEngine.isTransitioning(), true)
  ctx.frozen = null                               // audio clock runs again
  await done
  assert.equal(audioEngine.currentMood, 'mystery')
})

test('a command given during an unfinished transition waits for it and does not overlap', async () => {
  const g = setup()
  const first = audioEngine.crossfadeTo(null, 0.2, 'epic')
  const second = audioEngine.crossfadeTo(null, 0.2, 'spooky')
  await new Promise((r) => setTimeout(r, 50))
  assert.equal(audioEngine.isTransitioning(), true)
  await first
  assert.equal(audioEngine.currentMood, 'epic')
  await second
  assert.equal(audioEngine.currentMood, 'spooky')
  // fade-out, fade-in, fade-out, fade-in - strictly one after another
  assert.deepEqual(ramps(g), [0, 0.7, 0, 0.7])
})

test('volume change is a short ramp anchored at the current value', () => {
  const g = setup()
  audioEngine.audioContext.frozen = 10
  audioEngine.setVolume(0.4)
  assert.deepEqual(g.calls, [['cancel', 10], ['set', 0.7, 10], ['ramp', 0.4, 10.1]])
})

test('same mood does not restart the generator', async () => {
  const g = setup()
  await audioEngine.crossfadeTo(null, 3, 'calm')
  assert.equal(g.calls.length, 0)
})
