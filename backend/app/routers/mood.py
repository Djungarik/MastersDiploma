"""
Mood Analysis Router

Analyzes transcribed text using AI to determine:
- Mood (calm, tense, epic, spooky, mystery)
- Intensity (1-10)
- Environment (tavern, dungeon, forest, etc.)

Supports both OpenAI (paid) and Groq (free) as AI providers.
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError
from openai import AsyncOpenAI
import json
import re

from app.config import get_settings

router = APIRouter()


# Allowed categories (must match the system prompt and the frontend enums)
Mood = Literal["calm", "tense", "epic", "spooky", "mystery"]
Environment = Literal[
    "tavern", "dungeon", "forest", "castle", "wilderness", "city", "underwater", "void"
]


class MoodRequest(BaseModel):
    """Request body for mood analysis"""
    text: str = Field(min_length=1, max_length=4000)


class MoodResponse(BaseModel):
    """Response body with analyzed mood (validated against allowed values)"""
    mood: Mood
    intensity: int = Field(ge=1, le=10)
    environment: Environment
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


def validate_model_result(result: dict) -> MoodResponse:
    """
    Validate the parsed model answer.

    Categories are checked against the allowed sets and intensity against 1-10.
    Invalid answers are rejected (ValueError) instead of being silently replaced
    with defaults, so that a malformed answer can never trigger a music change.
    """
    if not isinstance(result, dict):
        raise ValueError("Model response is not a JSON object")

    data = dict(result)
    for key in ("mood", "environment"):
        if isinstance(data.get(key), str):
            data[key] = data[key].strip().lower()
    reasoning = data.get("reasoning")
    if reasoning is not None and not isinstance(reasoning, str):
        data["reasoning"] = str(reasoning)

    try:
        return MoodResponse(**{
            "mood": data.get("mood"),
            "intensity": data.get("intensity"),
            "environment": data.get("environment"),
            "reasoning": data.get("reasoning"),
        })
    except ValidationError as exc:
        raise ValueError(f"Model response failed validation: {exc.errors()}") from exc


def get_provider_config(settings) -> tuple[str, str, str | None, str]:
    """Return (api_key, model, base_url, provider_name) for the configured provider"""
    if settings.ai_provider.lower() == "groq":
        return settings.groq_api_key, settings.groq_model, "https://api.groq.com/openai/v1", "Groq"
    return settings.openai_api_key, settings.openai_model, None, "OpenAI"


def create_client(api_key: str, base_url: str | None) -> AsyncOpenAI:
    """Create the async client (Groq exposes an OpenAI-compatible API)"""
    return AsyncOpenAI(api_key=api_key, base_url=base_url, timeout=10.0, max_retries=0)


@router.post("/analyze-mood", response_model=MoodResponse)
async def analyze_mood(request: MoodRequest) -> MoodResponse:
    """
    Analyze transcribed GM speech to determine mood, intensity, and environment.

    Errors:
    - 400: text shorter than min_text_length
    - 503: API key is not configured
    - 502: the AI provider failed or returned an invalid answer
    """
    settings = get_settings()
    provider = settings.ai_provider.lower()
    api_key, model, base_url, provider_name = get_provider_config(settings)

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

    # 1. Call the provider asynchronously (does not block the event loop)
    try:
        client = create_client(api_key, base_url)
        response = await client.chat.completions.create(**request_params)
        result_text = response.choices[0].message.content or ""
    except Exception as e:
        print(f"{provider_name} API error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Mood analysis service unavailable: {type(e).__name__}"
        )

    # 2. Parse and validate the answer
    try:
        return validate_model_result(extract_json_from_response(result_text))
    except ValueError as e:
        print(f"Invalid {provider_name} response: {str(e)[:300]}")
        raise HTTPException(status_code=502, detail="Invalid model response")


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

