import { useMemo } from 'react'
import useAppStore from '../store/useAppStore'

/**
 * The central mood indicator orb
 * Changes color and glow based on current mood
 */
export function MoodOrb() {
  const { currentMood, intensity, isTransitioning } = useAppStore()

  const orbClasses = useMemo(() => {
    const base = 'mood-orb w-48 h-48 md:w-64 md:h-64 flex items-center justify-center transition-all duration-1000'
    const moodClass = `mood-${currentMood}`
    const pulseClass = isTransitioning ? 'animate-pulse' : ''
    
    return `${base} ${moodClass} ${pulseClass}`
  }, [currentMood, isTransitioning])

  // Scale orb size based on intensity
  const orbStyle = useMemo(() => ({
    transform: `scale(${0.8 + (intensity / 10) * 0.4})`,
  }), [intensity])

  const moodLabel = useMemo(() => {
    const labels = {
      calm: 'Tranquil',
      tense: 'Suspenseful',
      epic: 'Epic',
      spooky: 'Ominous',
      mystery: 'Mysterious',
    }
    return labels[currentMood] || 'Unknown'
  }, [currentMood])

  const moodIcon = useMemo(() => {
    const icons = {
      calm: '🌿',
      tense: '⚡',
      epic: '⚔️',
      spooky: '👁️',
      mystery: '🔮',
    }
    return icons[currentMood] || '✧'
  }, [currentMood])

  return (
    <div className="relative flex flex-col items-center gap-6">
      {/* Outer ring animation */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div 
          className="w-72 h-72 md:w-96 md:h-96 rounded-full border border-gold-400/20 animate-pulse-slow"
          style={{ animationDuration: `${6 - intensity / 2}s` }}
        />
      </div>

      {/* Main orb */}
      <div className={orbClasses} style={orbStyle}>
        <div className="text-center">
          <span className="text-5xl md:text-6xl animate-float" style={{ animationDelay: '0s' }}>
            {moodIcon}
          </span>
        </div>
      </div>

      {/* Mood label */}
      <div className="text-center space-y-2">
        <h2 className="font-display text-3xl md:text-4xl text-parchment-200 tracking-wide">
          {moodLabel}
        </h2>
        <div className="flex items-center gap-2 justify-center">
          <span className="text-parchment-400 text-sm">Intensity</span>
          <div className="flex gap-1">
            {[...Array(10)].map((_, i) => (
              <div
                key={i}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  i < intensity 
                    ? 'bg-gold-400 shadow-sm shadow-gold-400/50' 
                    : 'bg-ink-700'
                }`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default MoodOrb

