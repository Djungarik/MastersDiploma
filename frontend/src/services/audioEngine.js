/**
 * Audio Engine - Professional ambient music generation
 * 
 * Creates rich, evolving ambient soundscapes using Web Audio API
 * Much more musical than simple oscillators
 */

class AudioEngine {
  constructor() {
    this.audioContext = null
    this.masterGain = null
    this.nodes = []
    this.isInitialized = false
    this.masterVolume = 0.7
    this.currentMood = null
    this.isPlaying = false
  }

  /**
   * Initialize the audio engine
   */
  async init() {
    if (this.isInitialized) return

    this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
    
    // Master gain
    this.masterGain = this.audioContext.createGain()
    this.masterGain.connect(this.audioContext.destination)
    this.masterGain.gain.value = 0

    this.isInitialized = true
    console.log('🔊 Audio engine initialized')
  }

  /**
   * Resume audio context if suspended
   */
  async resume() {
    if (this.audioContext?.state === 'suspended') {
      await this.audioContext.resume()
    }
  }

  /**
   * Smoothly move the master gain from its current value to `value` over `seconds`.
   * The ramp is anchored at the current value: without setValueAtTime() a linear ramp
   * starts from the time of the previous automation event, which makes the gain jump.
   */
  rampTo(value, seconds) {
    const gain = this.masterGain.gain
    const now = this.audioContext.currentTime
    const current = gain.value
    gain.cancelScheduledValues(now)
    gain.setValueAtTime(current, now)
    gain.linearRampToValueAtTime(value, now + seconds)
  }

  /**
   * Stop all playing sounds
   */
  stopAll() {
    this.nodes.forEach(node => {
      try {
        if (node.stop) node.stop()
        if (node.disconnect) node.disconnect()
      } catch (e) {}
    })
    this.nodes = []
    if (this.masterGain) {
      this.masterGain.gain.cancelScheduledValues(0)
      this.masterGain.gain.value = 0
    }
    this.isPlaying = false
    this.currentMood = null
  }

  /**
   * Create a filtered oscillator with envelope
   */
  createVoice(freq, type, filterFreq, filterQ, gainValue, detune = 0) {
    const osc = this.audioContext.createOscillator()
    const filter = this.audioContext.createBiquadFilter()
    const gain = this.audioContext.createGain()
    
    osc.type = type
    osc.frequency.value = freq
    osc.detune.value = detune
    
    filter.type = 'lowpass'
    filter.frequency.value = filterFreq
    filter.Q.value = filterQ
    
    gain.gain.value = gainValue
    
    osc.connect(filter)
    filter.connect(gain)
    gain.connect(this.masterGain)
    
    osc.start()
    this.nodes.push(osc, filter, gain)
    
    return { osc, filter, gain }
  }

  /**
   * Create LFO for modulation
   */
  createLFO(freq, amount, target) {
    const lfo = this.audioContext.createOscillator()
    const lfoGain = this.audioContext.createGain()
    
    lfo.type = 'sine'
    lfo.frequency.value = freq
    lfoGain.gain.value = amount
    
    lfo.connect(lfoGain)
    lfoGain.connect(target)
    lfo.start()
    
    this.nodes.push(lfo, lfoGain)
    return { lfo, gain: lfoGain }
  }

  /**
   * Generate CALM ambient - peaceful, warm pads
   */
  generateCalm() {
    // Warm pad chord: C major (C3, E3, G3, C4)
    const baseFreq = 130.81 // C3
    const notes = [1, 1.26, 1.5, 2] // C, E, G, C octave
    
    notes.forEach((ratio, i) => {
      const freq = baseFreq * ratio
      // Main pad voice
      const v1 = this.createVoice(freq, 'sine', 800, 1, 0.08, Math.random() * 5)
      // Detuned layer for warmth
      const v2 = this.createVoice(freq, 'triangle', 600, 0.5, 0.04, 7 + Math.random() * 3)
      
      // Slow filter sweep
      this.createLFO(0.05 + Math.random() * 0.03, 200, v1.filter.frequency)
      // Gentle volume swell
      this.createLFO(0.08, 0.02, v1.gain.gain)
    })
    
    // Add subtle sub bass
    this.createVoice(baseFreq / 2, 'sine', 200, 1, 0.1)
  }

  /**
   * Generate TENSE ambient - minor, unsettling
   */
  generateTense() {
    // A minor with added tension (A2, C3, E3, G3)
    const baseFreq = 110 // A2
    const notes = [1, 1.19, 1.5, 1.78] // Minor with 7th
    
    notes.forEach((ratio, i) => {
      const freq = baseFreq * ratio
      const v = this.createVoice(freq, 'sawtooth', 400 + i * 100, 2, 0.04)
      
      // Faster, unsettling modulation
      this.createLFO(0.15 + Math.random() * 0.1, 150, v.filter.frequency)
    })
    
    // Pulsing sub bass
    const sub = this.createVoice(baseFreq / 2, 'sine', 150, 1, 0.12)
    this.createLFO(0.5, 0.06, sub.gain.gain)
    
    // High dissonant tone
    this.createVoice(baseFreq * 7.1, 'sine', 2000, 1, 0.015)
  }

  /**
   * Generate EPIC ambient - powerful, heroic
   */
  generateEpic() {
    // Power chord: D (D2, A2, D3, A3, D4)
    const baseFreq = 73.42 // D2
    const notes = [1, 1.5, 2, 3, 4]
    
    notes.forEach((ratio, i) => {
      const freq = baseFreq * ratio
      const v = this.createVoice(freq, 'sawtooth', 1200, 1.5, 0.05)
      
      // Powerful sweep
      this.createLFO(0.1, 400, v.filter.frequency)
    })
    
    // Strong bass pulse
    const bass = this.createVoice(baseFreq, 'square', 300, 2, 0.08)
    this.createLFO(1, 0.04, bass.gain.gain) // Rhythmic pulse
    
    // High shimmer
    this.createVoice(baseFreq * 8, 'sine', 3000, 0.5, 0.02)
    this.createVoice(baseFreq * 12, 'sine', 4000, 0.5, 0.01)
  }

  /**
   * Generate SPOOKY ambient - eerie, haunting
   */
  generateSpooky() {
    // Diminished chord + tritone: B, D, F, Ab
    const baseFreq = 61.74 // B1
    const notes = [1, 1.19, 1.41, 1.68, 2.83] // Diminished + tritone
    
    notes.forEach((ratio, i) => {
      const freq = baseFreq * ratio
      const v = this.createVoice(freq, 'triangle', 300, 3, 0.04)
      
      // Slow, creepy modulation
      this.createLFO(0.03 + Math.random() * 0.02, 100, v.filter.frequency)
      // Random volume swells (ghostly)
      this.createLFO(0.07 + Math.random() * 0.05, 0.02, v.gain.gain)
    })
    
    // Whisper noise
    const noise = this.createNoiseVoice(200, 0.02)
    this.createLFO(0.1, 100, noise.filter.frequency)
    
    // Distant high tone
    this.createVoice(baseFreq * 16, 'sine', 2000, 0.5, 0.008)
  }

  /**
   * Generate MYSTERY ambient - curious, magical
   */
  generateMystery() {
    // Whole tone scale feeling: C, D, E, F#, G#
    const baseFreq = 130.81 // C3
    const notes = [1, 1.12, 1.26, 1.41, 1.59]
    
    notes.forEach((ratio, i) => {
      const freq = baseFreq * ratio
      const v = this.createVoice(freq, 'sine', 1000, 1, 0.05)
      
      // Shimmering modulation
      this.createLFO(0.2 + i * 0.1, 200, v.filter.frequency)
      
      // Add sparkle octave
      if (i % 2 === 0) {
        const sparkle = this.createVoice(freq * 2, 'sine', 2000, 0.5, 0.02)
        this.createLFO(0.3, 0.01, sparkle.gain.gain)
      }
    })
    
    // Magical chime-like high notes
    this.createVoice(baseFreq * 4, 'sine', 3000, 1, 0.015)
    this.createVoice(baseFreq * 6, 'sine', 4000, 1, 0.01)
  }

  /**
   * Create filtered noise voice
   */
  createNoiseVoice(filterFreq, volume) {
    const bufferSize = this.audioContext.sampleRate * 2
    const buffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate)
    const data = buffer.getChannelData(0)
    
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1
    }
    
    const noise = this.audioContext.createBufferSource()
    noise.buffer = buffer
    noise.loop = true
    
    const filter = this.audioContext.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = filterFreq
    filter.Q.value = 1
    
    const gain = this.audioContext.createGain()
    gain.gain.value = volume
    
    noise.connect(filter)
    filter.connect(gain)
    gain.connect(this.masterGain)
    
    noise.start()
    this.nodes.push(noise, filter, gain)
    
    return { noise, filter, gain }
  }

  /**
   * Generate ambient for mood
   */
  generateAmbient(mood) {
    switch (mood) {
      case 'calm':
        this.generateCalm()
        break
      case 'tense':
        this.generateTense()
        break
      case 'epic':
        this.generateEpic()
        break
      case 'spooky':
        this.generateSpooky()
        break
      case 'mystery':
        this.generateMystery()
        break
      default:
        this.generateCalm()
    }
  }

  /**
   * Play immediately
   */
  async playImmediate(url, mood = 'calm') {
    await this.init()
    await this.resume()

    // Short fade-out instead of a hard cut when something is already playing
    if (this.isPlaying) {
      this.rampTo(0, 0.15)
      await new Promise(resolve => setTimeout(resolve, 150))
    }

    this.stopAll()
    this.currentMood = mood
    this.generateAmbient(mood)

    // Fade in
    this.rampTo(this.masterVolume, 2)
    
    this.isPlaying = true
    console.log('🎵 Playing ambient soundscape for mood:', mood)
  }

  /**
   * Crossfade to new mood
   */
  /**
   * Wait until the audio clock reaches `audioTime`. The page timer can drift from the
   * audio clock under load, so the audio clock is checked again after every timer;
   * a stalled audio clock is not waited for longer than `maxWaitMs`.
   */
  waitForAudioTime(audioTime, maxWaitMs) {
    const deadline = Date.now() + maxWaitMs
    return new Promise((resolve) => {
      const check = () => {
        const left = audioTime - this.audioContext.currentTime
        if (left > 0.005 && Date.now() < deadline) {
          setTimeout(check, left * 1000 + 5)
          return
        }
        resolve()
      }
      check()
    })
  }

  /**
   * Transition to another mood: the current ambient fades out to zero, then the
   * ambient of the new mood is started and fades in (the two never sound together).
   * Returns a promise that resolves when the fade-in has finished. Transitions are
   * serialised: a call made while a transition is running starts after it ends.
   */
  crossfadeTo(url, durationSeconds = 3, mood = 'calm') {
    const run = () => this.runTransition(durationSeconds, mood)
    this.transition = (this.transition || Promise.resolve()).then(run, run)
    return this.transition
  }

  async runTransition(durationSeconds, mood) {
    if (mood === this.currentMood) {
      console.log('🎵 Same mood, no change needed')
      return
    }

    await this.init()
    await this.resume()

    this.transitioning = true
    const half = durationSeconds / 2
    try {
      // Fade out the current ambient (anchored at the current gain, see rampTo)
      this.rampTo(0, half)
      await this.waitForAudioTime(this.audioContext.currentTime + half, half * 1000 + 1000)

      // Switch generators only after the fade-out has really ended
      this.stopAll()
      this.currentMood = mood
      this.generateAmbient(mood)
      this.isPlaying = true
      console.log('🎵 Crossfaded to mood:', mood)

      // Fade in the new ambient
      this.rampTo(this.masterVolume, half)
      await this.waitForAudioTime(this.audioContext.currentTime + half, half * 1000 + 1000)
    } finally {
      this.transitioning = false
    }
  }

  /**
   * True while a transition (fade-out, switch, fade-in) is running
   */
  isTransitioning() {
    return Boolean(this.transitioning)
  }

  /**
   * Play bridge sound (no-op for generated audio)
   */
  async playBridge(url, fadeInDuration = 1) {}

  /**
   * Stop bridge sound (no-op)
   */
  async stopBridge(fadeOutDuration = 1) {}

  /**
   * Set master volume
   */
  setVolume(value) {
    this.masterVolume = Math.max(0, Math.min(1, value))
    if (this.masterGain && this.isPlaying) {
      this.rampTo(this.masterVolume, 0.1)
    }
  }

  /**
   * Get current volume
   */
  getVolume() {
    return this.masterVolume
  }

  /**
   * Check if playing
   */
  getIsPlaying() {
    return this.isPlaying
  }

  /**
   * Cleanup
   */
  dispose() {
    this.stopAll()
    if (this.audioContext) {
      this.audioContext.close()
    }
    this.isInitialized = false
  }
}

// Singleton
export const audioEngine = new AudioEngine()
export default audioEngine
