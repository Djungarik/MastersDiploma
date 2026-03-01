import useAppStore from '../store/useAppStore'

/**
 * Shows audio capture status with waveform visualization
 */
export function ListenerStatus() {
  const { 
    isListening, 
    audioLevel, 
    isTranscribing,
    transcribedText 
  } = useAppStore()

  return (
    <div className="glass-card p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="font-display text-lg text-parchment-200 flex items-center gap-2">
          <span className="text-xl">👂</span>
          The Listener
        </h3>
        <div className={`flex items-center gap-2 text-sm ${isListening ? 'text-forest-400' : 'text-parchment-500'}`}>
          <span className={`w-2 h-2 rounded-full ${isListening ? 'bg-forest-400 animate-pulse' : 'bg-parchment-500'}`} />
          {isListening ? 'Active' : 'Idle'}
        </div>
      </div>

      {/* Waveform visualization */}
      <div className="flex items-end justify-center gap-1 h-8">
        {[...Array(9)].map((_, i) => (
          <div
            key={i}
            className={`waveform-bar w-1 bg-gold-400 rounded-full transition-all ${
              isListening ? '' : 'animation-paused'
            }`}
            style={{
              height: isListening 
                ? `${4 + audioLevel * 20 + Math.sin(i * 0.5) * 4}px`
                : '4px',
              opacity: isListening ? 0.6 + audioLevel * 0.4 : 0.3,
              animationPlayState: isListening ? 'running' : 'paused',
            }}
          />
        ))}
      </div>

      {/* Transcription status */}
      {isTranscribing && (
        <div className="flex items-center gap-2 text-sm text-mystic-400">
          <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <span>Transcribing...</span>
        </div>
      )}

      {/* Last transcription */}
      {transcribedText && !isTranscribing && (
        <div className="space-y-1">
          <p className="text-xs text-parchment-500 uppercase tracking-wide">Last heard:</p>
          <p className="text-parchment-300 text-sm italic leading-relaxed line-clamp-3">
            "{transcribedText}"
          </p>
        </div>
      )}
    </div>
  )
}

export default ListenerStatus

