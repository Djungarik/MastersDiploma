"""
Mood Analysis Router

Analyzes transcribed text using AI to determine:
- Mood (calm, tense, epic, spooky, mystery)
- Intensity (1-10)
- Environment (tavern, dungeon, forest, etc.)

Supports both OpenAI (paid) and Groq (free) as AI providers.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import AsyncOpenAI
import json
import re

from app.config import get_settings

router = APIRouter()


class MoodRequest(BaseModel):
    """Request body for mood analysis"""
    text: str


class MoodResponse(BaseModel):
    """Response body with analyzed mood"""
    mood: str
    intensity: int
    environment: str
    reasoning: str | None = None


# System prompt for the "DJ" AI
SYSTEM_PROMPT = """You are an expert DJ for tabletop role-playing games like D&D. Your job is to analyze the Game Master's narration and determine the perfect musical mood.

Based on the provided text, analyze the narrative and return a JSON object with these exact fields:
- "mood": One of: "calm", "tense", "epic", "spooky", "mystery"
- "intensity": A number from 1 to 10 (1 = very subtle, 10 = overwhelming)
- "environment": One of: "tavern", "dungeon", "forest", "castle", "wilderness", "city", "underwater", "void"
- "reasoning": A brief one-sentence explanation of your choice

Guidelines for mood detection:
- "calm": Peaceful moments, rest, friendly NPC interactions, shopping, traveling safely
- "tense": Suspense, sneaking, negotiations going wrong, before combat, chases
- "epic": Combat, heroic moments, dramatic revelations, boss fights, victories
- "spooky": Horror elements, undead, curses, haunted locations, dark rituals
- "mystery": Investigation, puzzles, discovering secrets, magical phenomena

IMPORTANT: Return ONLY a valid JSON object, no markdown formatting, no code blocks, just the raw JSON."""


def extract_json_from_response(text: str) -> dict:
    """Extract JSON from response, handling markdown code blocks"""
    # Try to parse as-is first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract from markdown code block
    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to find raw JSON object
    json_match = re.search(r'\{[^{}]*"mood"[^{}]*\}', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass
    
    raise ValueError(f"Could not extract JSON from response: {text[:200]}")


@router.post("/analyze-mood", response_model=MoodResponse)
async def analyze_mood(request: MoodRequest) -> MoodResponse:
    """
    Analyze transcribed GM speech to determine mood, intensity, and environment.
    
    Supports both OpenAI and Groq (free) as AI providers.
    Set AI_PROVIDER=groq and GROQ_API_KEY in .env to use free Groq.
    """
    settings = get_settings()
    
    # Determine which provider to use
    provider = settings.ai_provider.lower()
    
    if provider == "groq":
        api_key = settings.groq_api_key
        model = settings.groq_model
        base_url = "https://api.groq.com/openai/v1"
        provider_name = "Groq"
    else:
        api_key = settings.openai_api_key
        model = settings.openai_model
        base_url = None  # Use default OpenAI URL
        provider_name = "OpenAI"
    
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=f"{provider_name} API key not configured. Set {'GROQ_API_KEY' if provider == 'groq' else 'OPENAI_API_KEY'} in .env"
        )
    
    if len(request.text.strip()) < settings.min_text_length:
        raise HTTPException(
            status_code=400,
            detail=f"Text too short. Minimum {settings.min_text_length} characters required."
        )
    
    try:
        # Log for debugging
        print(f"🔍 Analyzing text with {provider_name}: {request.text[:100]}...")
        print(f"🔑 Using model: {model}")
        
        # Create client (works for both OpenAI and Groq since Groq uses OpenAI-compatible API)
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )
        
        # Build request (Groq doesn't support response_format, so we skip it)
        request_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this GM narration:\n\n{request.text}"}
            ],
            "temperature": 0.3,
            "max_tokens": 200,
        }
        
        # Only add response_format for OpenAI (Groq doesn't support it well)
        if provider != "groq":
            request_params["response_format"] = {"type": "json_object"}
        
        response = await client.chat.completions.create(**request_params)
        
        result_text = response.choices[0].message.content
        print(f"✅ {provider_name} response: {result_text}")
        result = extract_json_from_response(result_text)
        
        # Validate and normalize response
        mood = result.get("mood", "calm").lower()
        if mood not in ["calm", "tense", "epic", "spooky", "mystery"]:
            mood = "calm"
        
        intensity = result.get("intensity", 5)
        if not isinstance(intensity, int) or intensity < 1 or intensity > 10:
            intensity = 5
        
        environment = result.get("environment", "tavern").lower()
        valid_environments = ["tavern", "dungeon", "forest", "castle", "wilderness", "city", "underwater", "void"]
        if environment not in valid_environments:
            environment = "tavern"
        
        return MoodResponse(
            mood=mood,
            intensity=intensity,
            environment=environment,
            reasoning=result.get("reasoning"),
        )
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response: {str(e)}"
        )
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f"❌ OpenAI API error: {type(e).__name__}: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Mood analysis failed: {type(e).__name__}: {str(e)}"
        )


@router.post("/analyze-mood/mock", response_model=MoodResponse)
async def analyze_mood_mock(request: MoodRequest) -> MoodResponse:
    """
    Mock endpoint for testing without OpenAI API.
    Returns mood based on simple keyword matching.
    """
    text = request.text.lower()
    
    # Simple keyword-based mood detection for testing
    if any(word in text for word in ["attack", "fight", "battle", "charge", "sword", "dragon"]):
        return MoodResponse(mood="epic", intensity=8, environment="dungeon", reasoning="Combat keywords detected")
    
    if any(word in text for word in ["dark", "shadow", "ghost", "undead", "death", "grave"]):
        return MoodResponse(mood="spooky", intensity=7, environment="dungeon", reasoning="Horror keywords detected")
    
    if any(word in text for word in ["sneak", "careful", "trap", "danger", "hide", "wait"]):
        return MoodResponse(mood="tense", intensity=6, environment="dungeon", reasoning="Suspense keywords detected")
    
    if any(word in text for word in ["clue", "investigate", "strange", "magic", "rune", "puzzle"]):
        return MoodResponse(mood="mystery", intensity=5, environment="castle", reasoning="Investigation keywords detected")
    
    if any(word in text for word in ["tavern", "inn", "drink", "rest", "sleep", "morning"]):
        return MoodResponse(mood="calm", intensity=3, environment="tavern", reasoning="Peaceful keywords detected")
    
    if any(word in text for word in ["forest", "tree", "path", "nature", "river"]):
        return MoodResponse(mood="calm", intensity=4, environment="forest", reasoning="Nature keywords detected")
    
    # Default
    return MoodResponse(mood="calm", intensity=5, environment="tavern", reasoning="No strong keywords detected")

