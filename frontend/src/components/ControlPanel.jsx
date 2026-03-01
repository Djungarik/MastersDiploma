import { useState, useCallback } from 'react'
import useAppStore from '../store/useAppStore'
import { useAudioCapture } from '../hooks/useAudioCapture'
import { initWhisper, transcribeAudio, isWhisperReady } from '../services/whisperService'
import { audioEngine } from '../services/audioEngine'

/**
 * Main control buttons for the application
 */
export function ControlPanel() {
  const [whisperProgress, setWhisperProgress] = useState(0)
  const [isInitializing, setIsInitializing] = useState(false)

  const { 
    whisperReady, 
    setWhisperReady, 
    setError,
    isListening,
    setTranscribing,
    setTranscribedText,
    analysisInterval,
    setAnalysisInterval,
  } = useAppStore()

  const { startCapture, stopCapture, getAudioChunk } = useAudioCapture()

  // Initialize Whisper model
  const handleInitialize = useCallback(async () => {
    setIsInitializing(true)
    try {
      await initWhisper((progress) => {
        setWhisperProgress(progress)
      })
      setWhisperReady(true)
      
      // Also init audio engine
      await audioEngine.init()
      
    } catch (error) {
      setError(`Failed to initialize: ${error.message}`)
    } finally {
      setIsInitializing(false)
    }
  }, [setWhisperReady, setError])

  // Toggle listening on/off
  const handleToggleListening = useCallback(async () => {
    if (isListening) {
      // Stop listening
      await stopCapture()
    } else {
      // Start listening
      await startCapture()
    }
  }, [isListening, startCapture, stopCapture])

  // Handle interval change
  const handleIntervalChange = useCallback((e) => {
    const value = parseInt(e.target.value, 10)
    setAnalysisInterval(value)
  }, [setAnalysisInterval])

  return (
    <div className="glass-card p-6 space-y-4">
      <h3 className="font-display text-lg text-parchment-200 flex items-center gap-2">
        <span className="text-xl">⚙️</span>
        Controls
      </h3>

      {/* Initialize button */}
      {!whisperReady && (
        <button
          onClick={handleInitialize}
          disabled={isInitializing}
          className="w-full py-3 px-4 bg-gradient-to-r from-mystic-600 to-mystic-500 
                     hover:from-mystic-500 hover:to-mystic-400
                     disabled:from-ink-700 disabled:to-ink-700 disabled:cursor-not-allowed
                     text-parchment-100 font-display text-sm tracking-wide
                     rounded-lg transition-all duration-300
                     shadow-lg shadow-mystic-600/20 hover:shadow-mystic-500/30"
        >
          {isInitializing ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Loading AI... {whisperProgress}%
            </span>
          ) : (
            '✨ Initialize Whisper AI'
          )}
        </button>
      )}

      {/* Listen toggle */}
      {whisperReady && (
        <>
          <button
            onClick={handleToggleListening}
            className={`w-full py-4 px-4 rounded-lg font-display text-sm tracking-wide
                        transition-all duration-300 shadow-lg
                        ${isListening 
                          ? 'bg-gradient-to-r from-blood-600 to-blood-500 hover:from-blood-500 hover:to-blood-400 shadow-blood-600/20'
                          : 'bg-gradient-to-r from-forest-600 to-forest-500 hover:from-forest-500 hover:to-forest-400 shadow-forest-600/20'
                        }
                        text-parchment-100`}
          >
            {isListening ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3 h-3 bg-parchment-100 rounded-sm" />
                Stop Listening
              </span>
            ) : (
              <span className="flex items-center justify-center gap-2">
                <span className="w-3 h-3 bg-parchment-100 rounded-full" />
                Start Listening
              </span>
            )}
          </button>

          {/* Analysis Interval Setting */}
          <div className="space-y-2 pt-2">
            <label className="flex items-center justify-between text-sm">
              <span className="text-parchment-400">Analysis Interval</span>
              <span className="text-parchment-200 font-display">
                {analysisInterval / 1000}s
              </span>
            </label>
            <input
              type="range"
              min="10000"
              max="60000"
              step="5000"
              value={analysisInterval}
              onChange={handleIntervalChange}
              disabled={isListening}
              className="w-full h-2 bg-ink-700 rounded-full appearance-none cursor-pointer
                         disabled:opacity-50 disabled:cursor-not-allowed
                         [&::-webkit-slider-thumb]:appearance-none
                         [&::-webkit-slider-thumb]:w-4
                         [&::-webkit-slider-thumb]:h-4
                         [&::-webkit-slider-thumb]:rounded-full
                         [&::-webkit-slider-thumb]:bg-mystic-400
                         [&::-webkit-slider-thumb]:shadow-lg
                         [&::-webkit-slider-thumb]:cursor-grab"
            />
            <p className="text-xs text-parchment-600">
              How often to analyze GM speech (shorter = more responsive)
            </p>
          </div>
        </>
      )}

      {/* Quick tips */}
      <div className="pt-2 border-t border-gold-400/10">
        <p className="text-xs text-parchment-500 italic">
          {!whisperReady 
            ? '💡 First time? Click Initialize to download the AI model (~150MB, cached after).'
            : isListening
            ? '🎙️ Listening... Speak naturally as you narrate your adventure!'
            : '💡 Click Start Listening, then narrate your adventure. The music will follow!'}
        </p>
      </div>
    </div>
  )
}

export default ControlPanel
