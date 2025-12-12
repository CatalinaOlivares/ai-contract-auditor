from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    GEMINI_API_KEY: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./contracts.db"

    # Server
    DEBUG: bool = True

    # LLM Settings
    GEMINI_MODEL: str = "gemini-2.5-flash"

    class Config:
        env_file = "../.env"
        extra = "ignore"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
