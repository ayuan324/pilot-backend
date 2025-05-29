"""
Application configuration settings
"""
import os
from typing import Optional, Any, Dict
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # FastAPI Configuration
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "πlot Backend"
    VERSION: str = "1.0.0"

    # Clerk Configuration
    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_JWT_ISSUER: Optional[str] = None

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: Optional[str] = None

    # LiteLLM Configuration
    OPENROUTER_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Sentry Configuration
    SENTRY_DSN: Optional[str] = None

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS Configuration
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,https://localhost:3000,https://same-ublsviolz5y-latest.netlify.app"

    def get_cors_origins(self) -> list[str]:
        """Get CORS origins as a list"""
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [i.strip() for i in self.BACKEND_CORS_ORIGINS.split(",") if i.strip()]
        return []

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
