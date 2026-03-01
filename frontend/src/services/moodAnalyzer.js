/**
 * Mood Analyzer Service
 * 
 * Sends transcribed text to backend for GPT-4o mini analysis
 * Returns mood, intensity, and environment classification
 */

import { MOODS, ENVIRONMENTS } from '../store/useAppStore'

/**
 * Analyze transcribed text to determine mood/vibe
 * @param {string} text - Transcribed speech from GM
 * @returns {Promise<{mood: string, intensity: number, environment: string}>}
 */
export async function analyzeMood(text) {
  if (!text || text.trim().length < 10) {
    return null // Not enough content to analyze
  }

  try {
    const response = await fetch('/api/analyze-mood', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ text }),
    })

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.statusText}`)
    }

    const data = await response.json()
    
    // Validate and normalize response
    return {
      mood: normalizeMood(data.mood),
      intensity: normalizeIntensity(data.intensity),
      environment: normalizeEnvironment(data.environment),
      reasoning: data.reasoning || null,
    }

  } catch (error) {
    console.error('Mood analysis failed:', error)
    throw error
  }
}

/**
 * Normalize mood to valid enum value
 */
function normalizeMood(mood) {
  const moodMap = {
    'calm': MOODS.CALM,
    'peaceful': MOODS.CALM,
    'relaxed': MOODS.CALM,
    'tense': MOODS.TENSE,
    'suspense': MOODS.TENSE,
    'anxious': MOODS.TENSE,
    'epic': MOODS.EPIC,
    'battle': MOODS.EPIC,
    'action': MOODS.EPIC,
    'heroic': MOODS.EPIC,
    'spooky': MOODS.SPOOKY,
    'horror': MOODS.SPOOKY,
    'scary': MOODS.SPOOKY,
    'creepy': MOODS.SPOOKY,
    'mystery': MOODS.MYSTERY,
    'mysterious': MOODS.MYSTERY,
    'intrigue': MOODS.MYSTERY,
  }

  const normalized = mood?.toLowerCase()
  return moodMap[normalized] || MOODS.CALM
}

/**
 * Normalize intensity to 1-10 range
 */
function normalizeIntensity(intensity) {
  const num = parseInt(intensity, 10)
  if (isNaN(num)) return 5
  return Math.max(1, Math.min(10, num))
}

/**
 * Normalize environment to valid enum value
 */
function normalizeEnvironment(environment) {
  const envMap = {
    'tavern': ENVIRONMENTS.TAVERN,
    'inn': ENVIRONMENTS.TAVERN,
    'bar': ENVIRONMENTS.TAVERN,
    'dungeon': ENVIRONMENTS.DUNGEON,
    'cave': ENVIRONMENTS.DUNGEON,
    'crypt': ENVIRONMENTS.DUNGEON,
    'forest': ENVIRONMENTS.FOREST,
    'woods': ENVIRONMENTS.FOREST,
    'jungle': ENVIRONMENTS.FOREST,
    'castle': ENVIRONMENTS.CASTLE,
    'palace': ENVIRONMENTS.CASTLE,
    'throne': ENVIRONMENTS.CASTLE,
    'wilderness': ENVIRONMENTS.WILDERNESS,
    'plains': ENVIRONMENTS.WILDERNESS,
    'mountain': ENVIRONMENTS.WILDERNESS,
    'city': ENVIRONMENTS.CITY,
    'town': ENVIRONMENTS.CITY,
    'market': ENVIRONMENTS.CITY,
    'underwater': ENVIRONMENTS.UNDERWATER,
    'ocean': ENVIRONMENTS.UNDERWATER,
    'sea': ENVIRONMENTS.UNDERWATER,
    'void': ENVIRONMENTS.VOID,
    'astral': ENVIRONMENTS.VOID,
    'ethereal': ENVIRONMENTS.VOID,
  }

  const normalized = environment?.toLowerCase()
  return envMap[normalized] || ENVIRONMENTS.TAVERN
}

/**
 * Check if mood has changed significantly enough to warrant new music
 * @param {string} currentMood 
 * @param {string} newMood 
 * @param {number} currentIntensity 
 * @param {number} newIntensity 
 * @returns {boolean}
 */
export function shouldChangeMuaic(currentMood, newMood, currentIntensity, newIntensity) {
  // Always change if mood is different
  if (currentMood !== newMood) return true
  
  // Change if intensity shifted by 3 or more
  if (Math.abs(currentIntensity - newIntensity) >= 3) return true
  
  return false
}

