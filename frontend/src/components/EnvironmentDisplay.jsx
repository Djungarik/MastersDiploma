import { useMemo } from 'react'
import useAppStore from '../store/useAppStore'

/**
 * Displays the detected environment with thematic icon
 */
export function EnvironmentDisplay() {
  const { environment } = useAppStore()

  const envData = useMemo(() => {
    const data = {
      tavern: { icon: '🍺', label: 'Tavern', color: 'text-amber-400' },
      dungeon: { icon: '🏰', label: 'Dungeon', color: 'text-stone-400' },
      forest: { icon: '🌲', label: 'Forest', color: 'text-emerald-400' },
      castle: { icon: '👑', label: 'Castle', color: 'text-yellow-400' },
      wilderness: { icon: '🏔️', label: 'Wilderness', color: 'text-slate-400' },
      city: { icon: '🏛️', label: 'City', color: 'text-blue-400' },
      underwater: { icon: '🌊', label: 'Underwater', color: 'text-cyan-400' },
      void: { icon: '✨', label: 'The Void', color: 'text-purple-400' },
    }
    return data[environment] || data.tavern
  }, [environment])

  return (
    <div className="glass-card p-4 text-center">
      <p className="text-xs text-parchment-500 uppercase tracking-widest mb-2">Environment</p>
      <div className="flex items-center justify-center gap-2">
        <span className="text-2xl">{envData.icon}</span>
        <span className={`font-display text-xl ${envData.color}`}>
          {envData.label}
        </span>
      </div>
    </div>
  )
}

export default EnvironmentDisplay

