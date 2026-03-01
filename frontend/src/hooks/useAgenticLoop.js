import { useCallback, useRef, useEffect } from 'react'
import useAppStore from '../store/useAppStore'
import { useAudioCapture } from './useAudioCapture'
import { transcribeAudio, isWhisperReady } from '../services/whisperService'
import { analyzeMood, shouldChangeMuaic } from '../services/moodAnalyzer'
import { audioEngine } from '../services/audioEngine'
import { fetchMusicTrack, getBridgeSound } from '../services/musicService'

/**
 * The Agentic Loop - Core innovation of Adaptive OST
 * 
 * This hook orchestrates the continuous cycle of:
 * 1. Capture audio from GM
 * 2. Transcribe locally with Whisper
 * 3. Analyze mood with GPT-4o mini
 * 4. Trigger music changes when mood shifts
 * 
 * The loop runs automatically every N seconds while listening is active.
 */
export function useAgenticLoop() {
  const loopIntervalRef = useRef(null)
  const firstRunTimeoutRef = useRef(null)
  const lastMoodRef = useRef(null)
  const lastIntensityRef = useRef(5)
  const isTransitioningRef = useRef(false)

  const {
    isListening,
    whisperReady,
    analysisInterval,
    currentMood,
    intensity,
    environment,
    isPlaying,
    setTranscribing,
    setTranscribedText,
    setMoodAnalysis,
    setError,
    setPlaying,
    setCurrentTrack,
    startTransition,
    completeTransition,
  } = useAppStore()

  const { getAudioChunk } = useAudioCapture()

  /**
   * Handle music transition with crossfade
   */
  const transitionToNewTrack = useCallback(async (mood, intensity, environment) => {
    if (isTransitioningRef.current) {
      console.log('⏳ Transition already in progress, skipping')
      return
    }

    isTransitioningRef.current = true
    startTransition()

    try {
      // Play bridge sound while loading new track (if available)
      const bridgeSound = getBridgeSound(mood === 'epic' ? 'drums' : 'wind')
      if (bridgeSound) {
        try {
          await audioEngine.playBridge(bridgeSound, 0.5)
        } catch (bridgeError) {
          console.log('Bridge sound unavailable, continuing without:', bridgeError.message)
        }
      }

      // Fetch new track
      console.log(`🎵 Fetching ${mood} track for ${environment}...`)
      const track = await fetchMusicTrack(mood, intensity, environment)
      console.log(`🎵 Got track from ${track.source}:`, track.url)

      // Stop bridge and crossfade to new track
      if (bridgeSound) {
        try {
          await audioEngine.stopBridge(1)
        } catch (e) {
          // Ignore bridge stop errors
        }
      }
      
      if (isPlaying) {
        await audioEngine.crossfadeTo(track.url, 3, mood)
      } else {
        await audioEngine.playImmediate(track.url, mood)
        setPlaying(true)
      }

      setCurrentTrack(track.url)
      completeTransition()

    } catch (error) {
      console.error('Music transition failed:', error)
      setError(`Music error: ${error.message}`)
      completeTransition()
    } finally {
      isTransitioningRef.current = false
    }
  }, [isPlaying, setPlaying, setCurrentTrack, startTransition, completeTransition, setError])

  /**
   * Single iteration of the agentic loop
   */
  const runLoopIteration = useCallback(async () => {
    if (!isListening || !whisperReady) return

    try {
      // Phase A: Get audio chunk
      console.log('🎤 Capturing audio chunk...')
      const audioBlob = await getAudioChunk()
      
      if (!audioBlob || audioBlob.size < 100) {
        console.log('⏭️ Not enough audio captured (size: ' + (audioBlob?.size || 0) + ' bytes), skipping iteration')
        return
      }
      
      console.log(`✅ Got audio chunk: ${audioBlob.size} bytes`)

      // Phase B: Transcribe (local first, then server fallback)
      console.log('📝 Transcribing...')
      setTranscribing(true)
      
      let text = null
      let transcriptionMethod = 'none'
      
      // Try local Whisper first
      try {
        text = await transcribeAudio(audioBlob)
        transcriptionMethod = 'local'
        console.log('✅ Local transcription succeeded')
      } catch (transcribeError) {
        console.warn('⚠️ Local transcription failed:', transcribeError.message)
        
        // Try server fallback
        try {
          console.log('🔄 Trying server transcription...')
          const formData = new FormData()
          formData.append('audio', audioBlob, 'recording.webm')
          const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData,
          })
          if (response.ok) {
            const data = await response.json()
            text = data.text
            transcriptionMethod = 'server'
            console.log('✅ Server transcription succeeded')
          } else {
            console.warn('⚠️ Server returned error:', response.status, response.statusText)
          }
        } catch (serverError) {
          console.warn('⚠️ Server transcription failed:', serverError.message)
        }
      }
      
      setTranscribing(false)
      
      // Check if we got any transcription
      if (!text || text.trim().length === 0) {
        console.log('⏭️ No speech detected in audio')
        return
      }
      
      // Filter out common Whisper artifacts (silence transcriptions)
      const cleanedText = text.trim()
      const artifacts = ['you', 'the', 'thank you', 'thanks for watching', '[music]', '(music)', 'bye']
      if (cleanedText.length < 10 || artifacts.includes(cleanedText.toLowerCase())) {
        console.log('⏭️ Filtered out noise/artifact:', cleanedText)
        return
      }

      setTranscribedText(text)
      console.log('📝 Transcribed:', text.substring(0, 100) + '...')

      // Phase C: Analyze mood with backend
      console.log('🧠 Analyzing mood...')
      let analysis
      
      try {
        analysis = await analyzeMood(text)
      } catch (apiError) {
        console.log('API analysis failed, trying mock endpoint:', apiError.message)
        // Try mock endpoint for testing
        try {
          const mockResponse = await fetch('/api/analyze-mood/mock', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
          })
          if (mockResponse.ok) {
            analysis = await mockResponse.json()
          }
        } catch (mockError) {
          console.error('Mock analysis also failed:', mockError)
        }
      }

      if (!analysis) {
        console.log('⏭️ Could not analyze mood')
        return
      }

      console.log('🎭 Mood analysis:', analysis)
      setMoodAnalysis(analysis)

      // Phase D: Check if music should change
      const shouldChange = shouldChangeMuaic(
        lastMoodRef.current || currentMood,
        analysis.mood,
        lastIntensityRef.current,
        analysis.intensity
      )

      if (shouldChange) {
        console.log(`🎵 Mood changed: ${lastMoodRef.current} → ${analysis.mood}`)
        await transitionToNewTrack(analysis.mood, analysis.intensity, analysis.environment)
      } else {
        console.log('🎵 Mood stable, continuing current track')
      }

      // Update refs for next iteration
      lastMoodRef.current = analysis.mood
      lastIntensityRef.current = analysis.intensity

    } catch (error) {
      console.error('Agentic loop error:', error)
      setError(`Loop error: ${error.message}`)
      setTranscribing(false)
    }
  }, [
    isListening,
    whisperReady,
    currentMood,
    getAudioChunk,
    setTranscribing,
    setTranscribedText,
    setMoodAnalysis,
    setError,
    transitionToNewTrack,
  ])

  /**
   * Start the continuous loop
   */
  const startLoop = useCallback(() => {
    if (loopIntervalRef.current) return

    console.log(`🔄 Starting agentic loop (interval: ${analysisInterval}ms)`)
    
    // Run first iteration after a short delay to collect audio
    firstRunTimeoutRef.current = setTimeout(() => {
      runLoopIteration()
    }, 5000) // Wait 5 seconds before first analysis

    loopIntervalRef.current = setInterval(runLoopIteration, analysisInterval)
  }, [runLoopIteration, analysisInterval])

  /**
   * Stop the continuous loop
   */
  const stopLoop = useCallback(() => {
    if (firstRunTimeoutRef.current) {
      clearTimeout(firstRunTimeoutRef.current)
      firstRunTimeoutRef.current = null
    }
    if (loopIntervalRef.current) {
      console.log('⏹️ Stopping agentic loop')
      clearInterval(loopIntervalRef.current)
      loopIntervalRef.current = null
    }
  }, [])

  // Auto-start/stop based on listening state
  useEffect(() => {
    if (isListening && whisperReady) {
      startLoop()
    } else {
      stopLoop()
    }

    return () => stopLoop()
  }, [isListening, whisperReady, startLoop, stopLoop])

  // Play initial ambient track when first starting
  useEffect(() => {
    if (isListening && whisperReady && !isPlaying) {
      // Start with calm tavern music
      transitionToNewTrack('calm', 5, 'tavern')
    }
  }, [isListening, whisperReady, isPlaying, transitionToNewTrack])

  return {
    runLoopIteration, // For manual trigger
    startLoop,
    stopLoop,
    isLoopRunning: loopIntervalRef.current !== null,
  }
}

export default useAgenticLoop
