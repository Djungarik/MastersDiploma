"""
Adaptive OST - FastAPI Backend

Main API server that orchestrates:
1. User authentication
2. Mood analysis via AI (Groq/OpenAI)
3. Music generation via Mubert API (planned)
4. Fallback transcription via OpenAI Whisper API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routers import mood, transcribe, music, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    settings = get_settings()
    print(f"[Adaptive OST] {settings.app_name} starting...")
    print(f"   Debug mode: {settings.debug}")
    print(f"   AI Provider: {settings.ai_provider}")
    
    # Initialize database
    await init_db()
    
    yield
    print(f"[Adaptive OST] {settings.app_name} shutting down...")


app = FastAPI(
    title="Adaptive OST API",
    description="AI-powered soundtrack generation for tabletop RPGs",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(mood.router, prefix="/api", tags=["mood"])
app.include_router(transcribe.router, prefix="/api", tags=["transcribe"])
app.include_router(music.router, prefix="/api", tags=["music"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "app": "Adaptive OST",
        "version": "0.1.0",
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    settings = get_settings()
    return {
        "status": "healthy",
        "ai_provider": settings.ai_provider,
        "ai_configured": bool(settings.groq_api_key if settings.ai_provider == "groq" else settings.openai_api_key),
        "mubert_configured": bool(settings.mubert_api_key),
    }

