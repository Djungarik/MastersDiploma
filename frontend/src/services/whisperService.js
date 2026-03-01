/**
 * Whisper Transcription Service
 * 
 * Uses @huggingface/transformers to run Whisper locally in the browser
 * Falls back to server-side transcription if local fails
 * 
 * Note: First load downloads ~150MB model, cached after
 */

let pipeline = null
let isLoading = false

/**
 * Initialize the Whisper pipeline
 * Uses whisper-tiny for speed
 */
export async function initWhisper(onProgress = () => {}) {
  if (pipeline) return pipeline
  if (isLoading) {
    // Wait for existing load to complete
    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(() => {
        if (pipeline) {
          clearInterval(checkInterval)
          resolve(pipeline)
        }
      }, 100)
      
      // Timeout after 2 minutes
      setTimeout(() => {
        clearInterval(checkInterval)
        reject(new Error('Whisper initialization timeout'))
      }, 120000)
    })
  }

  isLoading = true

  try {
    // Import the new @huggingface/transformers package
    const { pipeline: createPipeline, env } = await import('@huggingface/transformers')
    
    // Configure environment
    env.allowLocalModels = false
    env.useBrowserCache = true
    
    console.log('🔄 Loading Whisper model...')
    
    // Create the ASR pipeline with whisper-tiny
    pipeline = await createPipeline(
      'automatic-speech-recognition',
      'onnx-community/whisper-tiny.en',
      {
        progress_callback: (progress) => {
          if (progress.status === 'progress' && progress.progress !== undefined) {
            const percent = Math.round(progress.progress)
            onProgress(percent)
            console.log(`📥 Loading: ${percent}%`)
          } else if (progress.status === 'done' || progress.status === 'ready') {
            onProgress(100)
          }
        },
        dtype: 'fp32', // Use fp32 for better browser compatibility
        device: 'wasm', // Use WASM backend (works in all browsers)
      }
    )

    isLoading = false
    console.log('✅ Whisper initialized successfully')
    return pipeline

  } catch (error) {
    isLoading = false
    console.error('Failed to initialize Whisper:', error)
    throw error
  }
}

/**
 * Decode audio blob to Float32Array samples at 16kHz
 * Uses multiple fallback methods for better format support
 */
async function decodeAudioBlob(audioBlob) {
  // Method 1: Try direct decodeAudioData (works for WAV, MP3, some browsers support WebM)
  try {
    const arrayBuffer = await audioBlob.arrayBuffer()
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    
    const audioBuffer = await audioContext.decodeAudioData(arrayBuffer.slice(0))
    
    // Resample to 16kHz if needed
    const audioData = await resampleBuffer(audioBuffer, 16000)
    await audioContext.close()
    
    console.log('✅ Decoded audio using decodeAudioData')
    return audioData
  } catch (e) {
    console.log('⚠️ decodeAudioData failed, trying audio element method:', e.message)
  }

  // Method 2: Use audio element + MediaRecorder loopback (better WebM/Opus support)
  try {
    const audioData = await decodeUsingAudioElement(audioBlob)
    console.log('✅ Decoded audio using audio element method')
    return audioData
  } catch (e) {
    console.log('⚠️ Audio element method failed:', e.message)
    throw new Error(`Unable to decode audio: ${e.message}`)
  }
}

/**
 * Resample an AudioBuffer to target sample rate
 */
async function resampleBuffer(audioBuffer, targetSampleRate) {
  if (audioBuffer.sampleRate === targetSampleRate) {
    const channelData = audioBuffer.getChannelData(0)
    const result = new Float32Array(channelData.length)
    result.set(channelData)
    return result
  }
  
  // Use OfflineAudioContext for high-quality resampling
  const duration = audioBuffer.duration
  const offlineCtx = new OfflineAudioContext(
    1, // mono
    Math.ceil(duration * targetSampleRate),
    targetSampleRate
  )
  
  const source = offlineCtx.createBufferSource()
  source.buffer = audioBuffer
  source.connect(offlineCtx.destination)
  source.start(0)
  
  const renderedBuffer = await offlineCtx.startRendering()
  const channelData = renderedBuffer.getChannelData(0)
  const result = new Float32Array(channelData.length)
  result.set(channelData)
  
  return result
}

/**
 * Decode audio using an HTML audio element with Web Audio capture
 * This method has better codec support including WebM/Opus
 */
function decodeUsingAudioElement(audioBlob) {
  return new Promise((resolve, reject) => {
    const audio = document.createElement('audio')
    const url = URL.createObjectURL(audioBlob)
    let audioContext = null
    let analyser = null
    let timeoutId = null
    
    const cleanup = () => {
      if (timeoutId) clearTimeout(timeoutId)
      URL.revokeObjectURL(url)
      if (audioContext && audioContext.state !== 'closed') {
        audioContext.close().catch(() => {})
      }
      audio.pause()
      audio.src = ''
      audio.remove()
    }

    audio.src = url
    audio.preload = 'auto'
    audio.muted = true // Mute to avoid playing audio aloud
    
    audio.onloadedmetadata = async () => {
      try {
        let duration = audio.duration
        
        // Handle cases where duration is not immediately available
        if (!duration || !isFinite(duration) || duration <= 0) {
          // Seek to end to force duration calculation
          audio.currentTime = 1e101
          await new Promise(r => setTimeout(r, 200))
          duration = audio.duration
          audio.currentTime = 0
          await new Promise(r => setTimeout(r, 100))
        }
        
        if (!duration || !isFinite(duration) || duration < 0.1) {
          cleanup()
          reject(new Error('Could not determine audio duration'))
          return
        }

        console.log(`🎵 Audio duration: ${duration.toFixed(2)}s`)
        
        // Create AudioContext and capture stream
        audioContext = new (window.AudioContext || window.webkitAudioContext)()
        
        // Create source from audio element
        const source = audioContext.createMediaElementSource(audio)
        
        // Create script processor to capture raw samples
        const bufferSize = 4096
        const processor = audioContext.createScriptProcessor(bufferSize, 1, 1)
        
        const samples = []
        let capturing = true
        
        processor.onaudioprocess = (e) => {
          if (!capturing) return
          const input = e.inputBuffer.getChannelData(0)
          // Make a copy since buffer gets reused
          samples.push(new Float32Array(input))
        }
        
        // Connect: source -> processor -> destination
        source.connect(processor)
        processor.connect(audioContext.destination)
        
        // Unmute for capture but keep volume at 0
        audio.muted = false
        audio.volume = 0
        
        audio.onended = async () => {
          capturing = false
          
          // Wait a bit for final samples
          await new Promise(r => setTimeout(r, 100))
          
          // Combine all samples
          const totalLength = samples.reduce((acc, s) => acc + s.length, 0)
          if (totalLength === 0) {
            cleanup()
            reject(new Error('No audio samples captured'))
            return
          }
          
          const combined = new Float32Array(totalLength)
          let offset = 0
          for (const chunk of samples) {
            combined.set(chunk, offset)
            offset += chunk.length
          }
          
          // Resample to 16kHz
          const sourceSampleRate = audioContext.sampleRate
          let finalSamples = combined
          
          if (sourceSampleRate !== 16000) {
            finalSamples = resampleLinear(combined, sourceSampleRate, 16000)
          }
          
          cleanup()
          resolve(finalSamples)
        }
        
        audio.onerror = () => {
          capturing = false
          cleanup()
          reject(new Error(`Audio playback error: ${audio.error?.message || 'Unknown'}`))
        }
        
        // Start playback to capture
        await audio.play()
        
      } catch (err) {
        cleanup()
        reject(err)
      }
    }

    audio.onerror = () => {
      cleanup()
      reject(new Error(`Audio loading error: ${audio.error?.message || 'Unknown'}`))
    }

    // Timeout after 30 seconds
    timeoutId = setTimeout(() => {
      cleanup()
      reject(new Error('Audio decoding timeout'))
    }, 30000)
  })
}

/**
 * Simple linear resampling (fast, acceptable quality for speech)
 */
function resampleLinear(samples, fromRate, toRate) {
  if (fromRate === toRate) return samples
  
  const ratio = fromRate / toRate
  const newLength = Math.round(samples.length / ratio)
  const result = new Float32Array(newLength)
  
  for (let i = 0; i < newLength; i++) {
    const srcIndex = i * ratio
    const srcIndexFloor = Math.floor(srcIndex)
    const srcIndexCeil = Math.min(srcIndexFloor + 1, samples.length - 1)
    const t = srcIndex - srcIndexFloor
    
    result[i] = samples[srcIndexFloor] * (1 - t) + samples[srcIndexCeil] * t
  }
  
  return result
}

/**
 * Transcribe an audio blob to text
 * @param {Blob} audioBlob - Audio data (webm, wav, etc.)
 * @returns {Promise<string>} - Transcribed text
 */
export async function transcribeAudio(audioBlob) {
  if (!pipeline) {
    throw new Error('Whisper not initialized. Call initWhisper() first.')
  }

  try {
    // Decode audio to raw samples at 16kHz
    const audioData = await decodeAudioBlob(audioBlob)
    
    if (audioData.length < 1600) { // Less than 0.1 seconds
      console.log('⚠️ Audio too short to transcribe')
      return ''
    }
    
    console.log(`🎤 Transcribing ${audioData.length} samples (${(audioData.length / 16000).toFixed(1)}s)...`)
    
    // Run transcription - pass Float32Array directly
    // Note: Don't pass language/task for English-only models like whisper-tiny.en
    const result = await pipeline(audioData, {
      chunk_length_s: 30,
      stride_length_s: 5,
      return_timestamps: false,
    })

    const text = result.text?.trim() || ''
    console.log(`📝 Transcribed: "${text.substring(0, 100)}..."`)
    
    return text

  } catch (error) {
    console.error('Transcription failed:', error)
    throw error
  }
}

/**
 * Fallback: Send audio to backend for server-side transcription
 * Useful if local Whisper fails or for higher accuracy
 */
export async function transcribeOnServer(audioBlob) {
  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')

  const response = await fetch('/api/transcribe', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`Server transcription failed: ${response.statusText}`)
  }

  const data = await response.json()
  return data.text
}

/**
 * Check if Whisper is ready
 */
export function isWhisperReady() {
  return pipeline !== null
}

/**
 * Clean up resources
 */
export function disposeWhisper() {
  pipeline = null
}
