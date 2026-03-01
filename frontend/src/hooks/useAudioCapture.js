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
let chunks = []
let animationFrameId = null

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
      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : 'audio/webm'

      mediaRecorder = new MediaRecorder(stream, { mimeType })
      chunks = []

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data)
          console.log(`🎤 Chunk received: ${event.data.size} bytes (total chunks: ${chunks.length})`)
        }
      }

      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error)
      }

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

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        chunks = []
        resolve(blob)
      }

      mediaRecorder.stop()
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

  // Get current audio as blob without stopping
  const getAudioChunk = useCallback(() => {
    return new Promise((resolve) => {
      if (!mediaRecorder || mediaRecorder.state !== 'recording') {
        console.log('⚠️ MediaRecorder not recording, state:', mediaRecorder?.state)
        resolve(null)
        return
      }

      // Request any pending data
      mediaRecorder.requestData()

      // Wait to ensure data is collected
      setTimeout(() => {
        const chunkCount = chunks.length
        console.log(`📊 Audio chunks available: ${chunkCount}`)
        
        if (chunkCount > 0) {
          const blob = new Blob(chunks, { type: 'audio/webm' })
          console.log(`📊 Audio blob size: ${blob.size} bytes`)
          chunks = [] // Clear for next chunk
          resolve(blob)
        } else {
          console.log('⚠️ No chunks available yet')
          resolve(null)
        }
      }, 500)
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
