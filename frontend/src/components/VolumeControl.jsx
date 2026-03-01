import useAppStore from '../store/useAppStore'
import { audioEngine } from '../services/audioEngine'

/**
 * Master volume slider with visual feedback
 */
export function VolumeControl() {
  const { volume, setVolume, isPlaying } = useAppStore()

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    audioEngine.setVolume(newVolume)
  }

  return (
    <div className="glass-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-parchment-400 text-sm">Volume</span>
        <span className="text-parchment-200 text-sm font-display">
          {Math.round(volume * 100)}%
        </span>
      </div>
      
      <div className="relative">
        <input
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={volume}
          onChange={handleVolumeChange}
          className="w-full h-2 bg-ink-700 rounded-full appearance-none cursor-pointer
                     [&::-webkit-slider-thumb]:appearance-none
                     [&::-webkit-slider-thumb]:w-4
                     [&::-webkit-slider-thumb]:h-4
                     [&::-webkit-slider-thumb]:rounded-full
                     [&::-webkit-slider-thumb]:bg-gold-400
                     [&::-webkit-slider-thumb]:shadow-lg
                     [&::-webkit-slider-thumb]:shadow-gold-400/30
                     [&::-webkit-slider-thumb]:cursor-grab
                     [&::-webkit-slider-thumb]:active:cursor-grabbing"
          style={{
            background: `linear-gradient(to right, #d4af37 0%, #d4af37 ${volume * 100}%, #1f1d1a ${volume * 100}%, #1f1d1a 100%)`,
          }}
        />
      </div>

      {/* Playback indicator */}
      <div className="flex items-center gap-2 text-xs">
        <span className={`w-1.5 h-1.5 rounded-full ${isPlaying ? 'bg-forest-400 animate-pulse' : 'bg-parchment-500'}`} />
        <span className="text-parchment-500">
          {isPlaying ? 'Playing' : 'No track'}
        </span>
      </div>
    </div>
  )
}

export default VolumeControl

