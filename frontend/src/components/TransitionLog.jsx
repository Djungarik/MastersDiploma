import { useState, useEffect } from 'react'
import useAppStore from '../store/useAppStore'

/**
 * Displays a log of mood transitions
 */
export function TransitionLog() {
  const [transitions, setTransitions] = useState([])
  const { currentMood, previousMood, intensity, environment, lastAnalysis } = useAppStore()

  // Log transitions when mood changes
  useEffect(() => {
    if (lastAnalysis && previousMood && currentMood !== previousMood) {
      setTransitions(prev => [
        {
          id: Date.now(),
          from: previousMood,
          to: currentMood,
          intensity,
          environment,
          timestamp: new Date().toLocaleTimeString(),
        },
        ...prev.slice(0, 9), // Keep last 10
      ])
    }
  }, [currentMood, previousMood, intensity, environment, lastAnalysis])

  const getMoodEmoji = (mood) => {
    const emojis = {
      calm: '🌿',
      tense: '⚡',
      epic: '⚔️',
      spooky: '👁️',
      mystery: '🔮',
    }
    return emojis[mood] || '✧'
  }

  return (
    <div className="glass-card p-4 space-y-3">
      <h3 className="font-display text-sm text-parchment-400 uppercase tracking-widest">
        Transition Log
      </h3>
      
      <div className="space-y-2 max-h-48 overflow-y-auto">
        {transitions.length === 0 ? (
          <div className="text-xs text-parchment-500">
            <p className="italic">No transitions yet...</p>
            <p className="text-parchment-600 mt-1">
              Mood changes will be logged here as the AI detects narrative shifts.
            </p>
          </div>
        ) : (
          transitions.map((t) => (
            <div 
              key={t.id}
              className="flex items-center gap-2 text-xs p-2 bg-ink-800/50 rounded"
            >
              <span className="text-parchment-600 w-16 shrink-0">
                {t.timestamp}
              </span>
              <span>{getMoodEmoji(t.from)}</span>
              <span className="text-parchment-500">→</span>
              <span>{getMoodEmoji(t.to)}</span>
              <span className="text-parchment-300 capitalize">
                {t.to}
              </span>
              <span className="text-parchment-600 ml-auto">
                ⚡{t.intensity}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default TransitionLog

