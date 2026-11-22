import { useCallback, useEffect } from 'react'
import useAppStore from '../store/useAppStore'

/**
 * Audio Capture Service (Singleton)
 * 
 * Module-level variables ensure all hook instances share the same recorder
 */
let mediaRecorder = null
let audioContext = null
let analyser = null
let stream = null
let animationFrameId = null

/**
 * Create a MediaRecorder that keeps its own list of recorded chunks
 */
function createRecorder(mediaStream) {
  const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
    ? 'audio/webm;codecs=opus'
    : 'audio/webm'

  const recorder = new MediaRecorder(mediaStream, { mimeType })
  recorder.recordedChunks = []

  recorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      recorder.recordedChunks.push(event.data)
    }
  }

  recorder.onerror = (event) => {
    console.error('MediaRecorder error:', event.error)
  }

  return recorder
}

/**
 * Hook for capturing audio from the user's microphone
 * Uses a singleton pattern so all components share the same recorder
 */
export function useAudioCapture() {
  const { 
    isListening, 
    setListening, 
    setAudioLevel,
    setError 
  } = useAppStore()

  // Monitor audio levels for visualization
  const monitorAudioLevel = useCallback(() => {
    if (!analyser) return

    const dataArray = new Uint8Array(analyser.frequencyBinCount)
    analyser.getByteFrequencyData(dataArray)

    // Calculate RMS (root mean square) for more accurate level
    const rms = Math.sqrt(
      dataArray.reduce((acc, val) => acc + val * val, 0) / dataArray.length
    )
    
    // Normalize to 0-1 range
    const normalizedLevel = Math.min(rms / 128, 1)
    setAudioLevel(normalizedLevel)

    if (mediaRecorder && mediaRecorder.state === 'recording') {
      animationFrameId = requestAnimationFrame(monitorAudioLevel)
    }
  }, [setAudioLevel])

  // Start capturing audio
  const startCapture = useCallback(async () => {
    // Already recording
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      console.log('🎤 Already recording')
      return
    }

    try {
      console.log('🎤 Requesting microphone access...')
      
      // Request microphone access
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      })

      console.log('🎤 Microphone access granted')

      // Set up audio context for level monitoring
      audioContext = new (window.AudioContext || window.webkitAudioContext)()
      analyser = audioContext.createAnalyser()
      analyser.fftSize = 256

      const source = audioContext.createMediaStreamSource(stream)
      source.connect(analyser)

      // Set up media recorder
      mediaRecorder = createRecorder(stream)

      setListening(true)
      mediaRecorder.start(1000) // Collect data every second
      console.log('🎤 Recording started')
      monitorAudioLevel()

    } catch (error) {
      console.error('Failed to start audio capture:', error)
      setError(`Microphone access denied: ${error.message}`)
    }
  }, [setListening, setError, monitorAudioLevel])

  // Stop capturing and return audio blob
  const stopCapture = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state === 'inactive') {
        resolve(null)
        return
      }

      const recorder = mediaRecorder
      recorder.onstop = () => {
        const blob = new Blob(recorder.recordedChunks, { type: 'audio/webm' })
        recorder.recordedChunks = []
        resolve(blob)
      }

      recorder.stop()
      setListening(false)
      setAudioLevel(0)

      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
        animationFrameId = null
      }

      // Clean up
      if (stream) {
        stream.getTracks().forEach(track => track.stop())
        stream = null
      }
      if (audioContext) {
        audioContext.close()
        audioContext = null
      }
      analyser = null
      mediaRecorder = null

      console.log('🎤 Recording stopped')
    })
  }, [setListening, setAudioLevel])

  // Get the audio recorded since the previous call as a standalone file.
  //
  // Only the first blob produced by a MediaRecorder contains the WebM header,
  // so slicing one long recording gives fragments that cannot be decoded.
  // The current recorder is therefore stopped (its blob is a complete WebM
  // file) and a new one is started on the same stream right away.
  const getAudioChunk = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state !== 'recording' || !stream) {
        console.log('MediaRecorder not recording, state:', mediaRecorder?.state)
        resolve(null)
        return
      }

      const finished = mediaRecorder
      finished.onstop = () => {
        const parts = finished.recordedChunks
        finished.recordedChunks = []
        if (parts.length > 0) {
          const blob = new Blob(parts, { type: 'audio/webm' })
          console.log(`Audio blob size: ${blob.size} bytes`)
          resolve(blob)
        } else {
          console.log('No audio data available yet')
          resolve(null)
        }
      }

      // Start the next recorder first so that no speech is lost in between
      mediaRecorder = createRecorder(stream)
      mediaRecorder.start(1000)
      finished.stop()
    })
  }, [])

  // Cleanup on unmount (only if this was the last instance)
  useEffect(() => {
    return () => {
      if (animationFrameId) {
        cancelAnimationFrame(animationFrameId)
      }
    }
  }, [])

  return {
    isListening,
    startCapture,
    stopCapture,
    getAudioChunk,
  }
}

export default useAudioCapture
