import { useCallback, useRef, useEffect } from 'react'
import useAppStore from '../store/useAppStore'
import { useAudioCapture } from './useAudioCapture'
import { transcribeAudio } from '../services/whisperService'
import { analyzeMood, shouldChangeMusic } from '../services/moodAnalyzer'
import { audioEngine } from '../services/audioEngine'
import { fetchMusicTrack, getBridgeSound } from '../services/musicService'
import { createLoopController } from '../services/loopController'

// Delay before the first analysis, so that some audio is collected
const FIRST_ITERATION_DELAY_MS = 5000

// Typical Whisper outputs for silence or background noise
const SILENCE_ARTIFACTS = ['you', 'the', 'thank you', 'thanks for watching', '[music]', '(music)', 'bye']

/**
 * The Agentic Loop - core of Adaptive OST
 *
 * Orchestrates the continuous cycle of:
 * 1. Capture audio from GM
 * 2. Transcribe locally with Whisper
 * 3. Analyze mood on the backend (LLM)
 * 4. Trigger music changes when mood shifts
 *
 * Scheduling is delegated to loopController: iterations run strictly one
 * after another, and results that arrive after the session was stopped are
 * ignored (see the isStale() checks after every await).
 */
export function useAgenticLoop() {
  const lastMoodRef = useRef(null)
  const lastIntensityRef = useRef(5)
  const isTransitioningRef = useRef(false)
  const controllerRef = useRef(null)
  const iterationRef = useRef(null)

  const {
    isListening,
    whisperReady,
    analysisInterval,
    currentMood,
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

  // Latest values for the long-lived loop: read through a ref so that the
  // loop never works with a stale closure and is not restarted on re-render
  const latestRef = useRef({ analysisInterval, currentMood })
  latestRef.current = { analysisInterval, currentMood }

  /**
   * Handle music transition with crossfade
   */
  const transitionToNewTrack = useCallback(async (mood, intensity, environment, isStale = () => false) => {
    if (isTransitioningRef.current) {
      console.log('Transition already in progress, skipping')
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

      const track = await fetchMusicTrack(mood, intensity, environment)

      if (bridgeSound) {
        try {
          await audioEngine.stopBridge(1)
        } catch (e) {
          // Ignore bridge stop errors
        }
      }

      // The session was stopped while the track was being fetched
      if (isStale()) {
        console.log('Session stopped, transition cancelled')
        return
      }

      if (audioEngine.getIsPlaying()) {
        console.log(`[loop] crossfade start -> ${mood}`)
        await audioEngine.crossfadeTo(track.url, 3, mood)
      } else {
        console.log(`[loop] playback start -> ${mood}`)
        await audioEngine.playImmediate(track.url, mood)
        setPlaying(true)
      }

      setCurrentTrack(track.url)
    } catch (error) {
      console.error('Music transition failed:', error)
      setError(`Music error: ${error.message}`)
    } finally {
      completeTransition()
      isTransitioningRef.current = false
    }
  }, [setPlaying, setCurrentTrack, startTransition, completeTransition, setError])

  /**
   * Single iteration of the agentic loop.
   * isStale() becomes true when the session that started it has been stopped.
   */
  const runLoopIteration = useCallback(async ({ isStale = () => false } = {}) => {
    try {
      // Phase A: get audio collected since the previous iteration
      console.log('[loop] iteration start')
      const audioBlob = await getAudioChunk()
      if (isStale()) return

      if (!audioBlob || audioBlob.size < 100) {
        console.log('Not enough audio captured (size: ' + (audioBlob?.size || 0) + ' bytes), skipping iteration')
        return
      }

      // Phase B: transcribe (local first, then server fallback)
      console.log('[loop] transcription start')
      setTranscribing(true)

      let text = null

      try {
        text = await transcribeAudio(audioBlob)
      } catch (transcribeError) {
        console.warn('Local transcription failed:', transcribeError.message)

        try {
          const formData = new FormData()
          formData.append('audio', audioBlob, 'recording.webm')
          const response = await fetch('/api/transcribe', { method: 'POST', body: formData })
          if (response.ok) {
            const data = await response.json()
            text = data.text
          } else {
            console.warn('Server transcription returned error:', response.status, response.statusText)
          }
        } catch (serverError) {
          console.warn('Server transcription failed:', serverError.message)
        }
      }

      setTranscribing(false)
      if (isStale()) return
      console.log('[loop] transcription end')

      if (!text || text.trim().length === 0) {
        console.log('No speech detected in audio')
        return
      }

      // Filter out common Whisper artifacts (silence transcriptions)
      const cleanedText = text.trim()
      if (cleanedText.length < 10 || SILENCE_ARTIFACTS.includes(cleanedText.toLowerCase())) {
        console.log('Filtered out noise/artifact:', cleanedText)
        return
      }

      setTranscribedText(text)
      console.log('[loop] transcribed text:', text)

      // Phase C: analyze mood with backend
      console.log('[loop] analysis start')
      let analysis = null

      try {
        analysis = await analyzeMood(text)
      } catch (apiError) {
        console.log('API analysis failed, trying keyword fallback:', apiError.message)
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
          console.error('Keyword fallback also failed:', mockError)
        }
      }

      // A late response of a stopped session must not change state or music
      if (isStale()) {
        console.log('Session stopped, analysis result ignored')
        return
      }

      if (!analysis) {
        console.log('Could not analyze mood')
        return
      }

      console.log('[loop] analysis end:', JSON.stringify(analysis))
      setMoodAnalysis(analysis)

      // Phase D: check if music should change
      const shouldChange = shouldChangeMusic(
        lastMoodRef.current || latestRef.current.currentMood,
        analysis.mood,
        lastIntensityRef.current,
        analysis.intensity
      )

      if (shouldChange) {
        await transitionToNewTrack(analysis.mood, analysis.intensity, analysis.environment, isStale)
      } else {
        console.log('[loop] mood stable, continuing current track')
      }

      // Update refs for next iteration
      lastMoodRef.current = analysis.mood
      lastIntensityRef.current = analysis.intensity
    } catch (error) {
      console.error('Agentic loop error:', error)
      if (!isStale()) setError(`Loop error: ${error.message}`)
      setTranscribing(false)
    }
  }, [getAudioChunk, setTranscribing, setTranscribedText, setMoodAnalysis, setError, transitionToNewTrack])

  // The controller is created once; it always calls the latest iteration
  iterationRef.current = runLoopIteration
  if (!controllerRef.current) {
    controllerRef.current = createLoopController({
      runIteration: (context) => iterationRef.current(context),
      getInterval: () => latestRef.current.analysisInterval,
      firstDelay: FIRST_ITERATION_DELAY_MS,
      onError: (error) => console.error('Agentic loop error:', error),
    })
  }

  // Start/stop through an effect with cleanup: the loop follows the actual
  // listening state and is always stopped on unmount
  useEffect(() => {
    const controller = controllerRef.current
    if (isListening && whisperReady) {
      console.log(`Starting agentic loop (interval: ${latestRef.current.analysisInterval}ms)`)
      controller.start()
    } else {
      controller.stop()
    }
    return () => controller.stop()
  }, [isListening, whisperReady])

  // Play initial ambient track when first starting
  useEffect(() => {
    if (isListening && whisperReady && !isPlaying) {
      transitionToNewTrack('calm', 5, 'tavern')
    }
  }, [isListening, whisperReady, isPlaying, transitionToNewTrack])

  return {
    runLoopIteration, // For manual trigger
    startLoop: () => controllerRef.current.start(),
    stopLoop: () => controllerRef.current.stop(),
    isLoopRunning: controllerRef.current.isRunning(),
  }
}

export default useAgenticLoop
