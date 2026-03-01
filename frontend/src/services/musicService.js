/**
 * Music Service
 * 
 * Fetches music tracks from:
 * 1. Backend API with Mubert (if configured)
 * 2. Falls back to generated audio (handled by audioEngine)
 */

/**
 * Fetch a music track for the given mood/environment
 * Tries backend API first, otherwise returns null for fallback to generated audio
 */
export async function fetchMusicTrack(mood, intensity, environment) {
  try {
    // Try the backend API (which may use Mubert if configured)
    const response = await fetch('/api/generate-music', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mood, intensity, environment, duration: 120 }),
    })

    if (response.ok) {
      const data = await response.json()
      // Only use backend URL if it's a real external URL (not a placeholder)
      if (data.url && data.url.startsWith('http') && data.source === 'mubert') {
        return {
          url: data.url,
          source: 'mubert',
          mood,
        }
      }
    }
  } catch (error) {
    // Backend not available - that's fine, will use generated audio
    console.log('Backend API unavailable, using generated audio')
  }

  // Return null URL - audioEngine will use generated ambient audio
  return {
    url: null,
    source: 'generated',
    mood,
  }
}

/**
 * Get a bridge sound URL for transitions
 * Returns null - bridge sounds use generated audio
 */
export function getBridgeSound(type = 'wind') {
  return null
}

export default {
  fetchMusicTrack,
  getBridgeSound,
}
