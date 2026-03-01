"""
Music Generation Router

Integrates with Mubert API to generate music based on mood.
Provides pre-defined track URLs as fallback when API is unavailable.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

from app.config import get_settings

router = APIRouter()


class MusicRequest(BaseModel):
    """Request body for music generation"""
    mood: str
    intensity: int = 5
    environment: str = "tavern"
    duration: int = 60  # seconds


class MusicResponse(BaseModel):
    """Response body with generated music URL"""
    url: str
    source: str  # "mubert", "fallback", or "cache"
    mood: str
    duration: int


# Fallback track URLs (royalty-free ambient loops)
# In production, these would be real URLs to hosted audio files
FALLBACK_TRACKS = {
    "calm": {
        "tavern": "/audio/calm_tavern.mp3",
        "forest": "/audio/calm_forest.mp3",
        "default": "/audio/calm_ambient.mp3",
    },
    "tense": {
        "dungeon": "/audio/tense_dungeon.mp3",
        "default": "/audio/tense_suspense.mp3",
    },
    "epic": {
        "dungeon": "/audio/epic_battle.mp3",
        "castle": "/audio/epic_heroic.mp3",
        "default": "/audio/epic_combat.mp3",
    },
    "spooky": {
        "dungeon": "/audio/spooky_dungeon.mp3",
        "void": "/audio/spooky_void.mp3",
        "default": "/audio/spooky_ambient.mp3",
    },
    "mystery": {
        "castle": "/audio/mystery_castle.mp3",
        "default": "/audio/mystery_ambient.mp3",
    },
}


# Mubert tags mapping for each mood
MUBERT_TAGS = {
    "calm": ["ambient", "peaceful", "relaxing", "acoustic"],
    "tense": ["suspense", "tension", "dramatic", "cinematic"],
    "epic": ["orchestral", "action", "heroic", "powerful"],
    "spooky": ["dark", "horror", "eerie", "atmospheric"],
    "mystery": ["mysterious", "curious", "ethereal", "subtle"],
}


def get_fallback_track(mood: str, environment: str) -> str:
    """Get fallback track URL based on mood and environment"""
    mood_tracks = FALLBACK_TRACKS.get(mood, FALLBACK_TRACKS["calm"])
    return mood_tracks.get(environment, mood_tracks["default"])


@router.post("/generate-music", response_model=MusicResponse)
async def generate_music(request: MusicRequest) -> MusicResponse:
    """
    Generate music based on mood, intensity, and environment.
    
    Uses Mubert API if configured, otherwise returns fallback tracks.
    """
    settings = get_settings()
    
    # Try Mubert API if configured
    if settings.mubert_api_key:
        try:
            return await generate_mubert_track(request, settings)
        except Exception as e:
            print(f"Mubert generation failed, using fallback: {e}")
    
    # Use fallback tracks
    track_url = get_fallback_track(request.mood, request.environment)
    
    return MusicResponse(
        url=track_url,
        source="fallback",
        mood=request.mood,
        duration=request.duration,
    )


async def generate_mubert_track(request: MusicRequest, settings) -> MusicResponse:
    """
    Generate track using Mubert API.
    
    Documentation: https://api-b2b.mubert.com/apidocs/
    """
    tags = MUBERT_TAGS.get(request.mood, MUBERT_TAGS["calm"])
    
    # Adjust BPM based on intensity
    base_bpm = {
        "calm": 70,
        "tense": 90,
        "epic": 120,
        "spooky": 60,
        "mystery": 80,
    }
    bpm = base_bpm.get(request.mood, 80) + (request.intensity - 5) * 5
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get a track token
        response = await client.post(
            f"{settings.mubert_api_url}/GetTrackInfo",
            json={
                "method": "GetTrack",
                "params": {
                    "license": settings.mubert_api_key,
                    "duration": request.duration,
                    "tags": tags,
                    "bpm": bpm,
                    "intensity": request.intensity / 10,  # Mubert uses 0-1
                    "format": "mp3",
                }
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Mubert API error: {response.status_code}"
            )
        
        data = response.json()
        
        if "error" in data:
            raise HTTPException(
                status_code=502,
                detail=f"Mubert error: {data['error']}"
            )
        
        track_url = data.get("data", {}).get("track_url")
        
        if not track_url:
            raise HTTPException(
                status_code=502,
                detail="Mubert did not return a track URL"
            )
        
        return MusicResponse(
            url=track_url,
            source="mubert",
            mood=request.mood,
            duration=request.duration,
        )


@router.get("/bridge-sounds")
async def get_bridge_sounds():
    """
    Get URLs for bridge/transition sounds.
    
    These ambient loops fill gaps while new music generates.
    """
    return {
        "drum_roll": "/audio/bridge/drum_roll.mp3",
        "wind": "/audio/bridge/ambient_wind.mp3",
        "crowd_murmur": "/audio/bridge/crowd_murmur.mp3",
        "heartbeat": "/audio/bridge/heartbeat.mp3",
        "magic_hum": "/audio/bridge/magic_hum.mp3",
    }

