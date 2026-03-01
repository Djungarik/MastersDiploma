"""
Configuration management for Adaptive OST backend
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # AI Provider selection: "openai" or "groq"
    ai_provider: str = "groq"  # Default to free Groq
    
    # OpenAI API (paid)
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    
    # Groq API (free!)
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"  # Fast and free
    
    # Mubert API for music generation
    mubert_api_key: str = ""
    mubert_api_url: str = "https://api-b2b.mubert.com/v2"
    
    # Application settings
    app_name: str = "Adaptive OST"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Analysis settings
    min_text_length: int = 10  # Minimum characters to trigger analysis
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()

