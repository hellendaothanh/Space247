import json
from typing import Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Space247"
    PROJECT_NAME: str = "Space247 Real Estate API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/real_estate_db"

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_ENABLED: bool = True
    PROPERTY_CACHE_TTL_SECONDS: int = 900  # 15 minutes default

    # pgvector embedding dimension (default 768 for multilingual models like multilingual-e5-base)
    VECTOR_DIM: int = 768
    EMBEDDING_MODEL: str = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

    # JWT Authentication
    SECRET_KEY: str = "space247-super-secret-jwt-key-for-development-change-in-production-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8081"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass
        elif isinstance(v, list):
            return [str(item) for item in v]
        return ["http://localhost:3000", "http://localhost:8081"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()


def get_settings() -> Settings:
    return settings
