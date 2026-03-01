import { useState } from 'react'
import useAppStore from '../store/useAppStore'
import { audioEngine } from '../services/audioEngine'
import { fetchMusicTrack } from '../services/musicService'

/**
 * Advanced settings and testing panel
 */
export function SettingsPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [testMood, setTestMood] = useState('epic')
  const [isTesting, setIsTesting] = useState(false)

  const {
    setMoodAnalysis,
    setPlaying,
    setCurrentTrack,
    startTransition,
    completeTransition,
    setError,
  } = useAppStore()

  // Test a specific mood manually
  const handleTestMood = async () => {
    setIsTesting(true)
    try {
      // Update mood display
      setMoodAnalysis({
        mood: testMood,
        intensity: testMood === 'epic' ? 8 : testMood === 'spooky' ? 7 : 5,
        environment: testMood === 'calm' ? 'tavern' : 'dungeon',
      })

      startTransition()

      // Fetch and play track
      const track = await fetchMusicTrack(testMood, 7, 'dungeon')
      
      await audioEngine.init()
      await audioEngine.playImmediate(track.url, testMood)
      
      setPlaying(true)
      setCurrentTrack(track.url)
      completeTransition()

    } catch (error) {
      setError(`Test failed: ${error.message}`)
    } finally {
      setIsTesting(false)
    }
  }

  // Stop all audio
  const handleStopAudio = () => {
    audioEngine.stopAll()
    setPlaying(false)
    setCurrentTrack(null)
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="glass-card p-3 w-full text-sm text-parchment-500 hover:text-parchment-300 
                   transition-colors flex items-center justify-center gap-2"
      >
        <span>🔧</span>
        <span>Developer Tools</span>
      </button>
    )
  }

  return (
    <div className="glass-card p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-display text-sm text-parchment-400 uppercase tracking-widest">
          Developer Tools
        </h3>
        <button
          onClick={() => setIsOpen(false)}
          className="text-parchment-600 hover:text-parchment-300"
        >
          ✕
        </button>
      </div>

      {/* Manual mood test */}
      <div className="space-y-2">
        <label className="text-xs text-parchment-500">Test Mood Manually</label>
        <div className="flex gap-2">
          <select
            value={testMood}
            onChange={(e) => setTestMood(e.target.value)}
            className="flex-1 bg-ink-800 border border-gold-400/20 rounded px-3 py-2 
                       text-parchment-200 text-sm focus:outline-none focus:border-gold-400/50"
          >
            <option value="calm">🌿 Calm</option>
            <option value="tense">⚡ Tense</option>
            <option value="epic">⚔️ Epic</option>
            <option value="spooky">👁️ Spooky</option>
            <option value="mystery">🔮 Mystery</option>
          </select>
          <button
            onClick={handleTestMood}
            disabled={isTesting}
            className="px-4 py-2 bg-mystic-600 hover:bg-mystic-500 disabled:bg-ink-700
                       text-parchment-100 text-sm rounded transition-colors"
          >
            {isTesting ? '...' : 'Play'}
          </button>
        </div>
      </div>

      {/* Stop button */}
      <button
        onClick={handleStopAudio}
        className="w-full py-2 bg-blood-600/50 hover:bg-blood-600 
                   text-parchment-200 text-sm rounded transition-colors"
      >
        ⏹️ Stop All Audio
      </button>

      {/* API Status */}
      <div className="pt-2 border-t border-gold-400/10 space-y-1">
        <p className="text-xs text-parchment-600">
          Backend: <span className="text-parchment-400">http://localhost:8000</span>
        </p>
        <p className="text-xs text-parchment-600">
          Music: Generated ambient audio (fallback mode)
        </p>
      </div>
    </div>
  )
}

export default SettingsPanel

