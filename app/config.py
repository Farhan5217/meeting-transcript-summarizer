import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    API_TITLE: str = "Meeting Transcript Summarizer"
    API_DESCRIPTION: str = "API for summarizing meeting transcripts using AI"
    API_VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    
    # CORS Settings
    CORS_ORIGINS: list = ["*"]  
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # AI Models
    OPENAI_CHUNK_MODEL: str = os.getenv("OPENAI_CHUNK_MODEL", "gpt-4o")
    OPENAI_FINAL_MODEL: str = os.getenv("OPENAI_FINAL_MODEL", "gpt-4o")
    ANTHROPIC_CHUNK_MODEL: str = os.getenv("ANTHROPIC_CHUNK_MODEL", "claude-3-haiku-20240307")
    ANTHROPIC_FINAL_MODEL: str = os.getenv("ANTHROPIC_FINAL_MODEL", "claude-3-5-sonnet-20240620")
    
    # Chunking Configuration
    TARGET_CHUNKS: int = int(os.getenv("TARGET_CHUNKS", "10"))
    MIN_CHUNK_SIZE: int = int(os.getenv("MIN_CHUNK_SIZE", "50"))
    MAX_CHUNK_SIZE: int = int(os.getenv("MAX_CHUNK_SIZE", "100"))
    DEFAULT_CHUNK_OVERLAP: int = int(os.getenv("DEFAULT_CHUNK_OVERLAP", "5"))
    
    # Job Configuration
    JOB_EXPIRY_HOURS: int = int(os.getenv("JOB_EXPIRY_HOURS", "24"))
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns:
        Settings instance
    """
    return Settings()