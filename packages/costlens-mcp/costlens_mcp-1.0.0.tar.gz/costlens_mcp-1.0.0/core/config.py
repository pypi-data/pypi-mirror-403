"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment."""
    
    # API
    app_name: str = "CostLens"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # CORS
    cors_origins: list[str] = [
        "http://localhost:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # GCP (optional - for precise estimation)
    gcp_project_id: str | None = None
    google_application_credentials: str | None = None
    
    # Cache
    redis_url: str | None = None
    cache_ttl_seconds: int = 3600  # 1 hour
    
    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
