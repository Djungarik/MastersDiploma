"""
Transcription Router

Provides server-side transcription as a fallback
when client-side Whisper fails or for higher accuracy.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import AsyncOpenAI
import tempfile
import os

from app.config import get_settings

router = APIRouter()


class TranscriptionResponse(BaseModel):
    """Response body with transcribed text"""
    text: str
    duration: float | None = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> TranscriptionResponse:
    """
    Transcribe audio file using OpenAI Whisper API.
    
    This is a fallback for when client-side transcription fails
    or when higher accuracy is needed.
    
    Supported formats: webm, mp3, wav, m4a, ogg
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in .env"
        )
    
    # Validate file type
    allowed_types = ["audio/webm", "audio/mp3", "audio/mpeg", "audio/wav", "audio/m4a", "audio/ogg"]
    if audio.content_type and audio.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format: {audio.content_type}"
        )
    
    try:
        # Save uploaded file to temp location
        suffix = ".webm" if "webm" in (audio.content_type or "") else ".mp3"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await audio.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            
            with open(temp_path, "rb") as audio_file:
                response = await client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                )
            
            return TranscriptionResponse(
                text=response.text,
                duration=response.duration if hasattr(response, "duration") else None,
            )
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

