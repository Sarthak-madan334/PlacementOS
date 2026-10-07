"""Application configuration and settings."""

import json
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    APP_ENV: str = "local"
    APP_NAME: str = "PlacementOS API"
    APP_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite:///./placementos.db"

    # CORS
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ]

    # Identity / Auth
    ALLOW_MOCK_AUTH: bool = False  # Must be explicitly enabled for local/test mock tokens
    AUTH_ISSUER_URL: str | None = None
    AUTH_AUDIENCE: str | None = None
    SUPABASE_JWT_SECRET: str | None = None

    # Storage
    SUPABASE_STORAGE_BUCKET: str = "resumes"
    SUPABASE_URL: str | None = None
    SUPABASE_SERVICE_ROLE_KEY: str | None = None

    # Optional token improves GitHub API rate limits; keep it server-side only.
    GITHUB_TOKEN: str | None = None

    # Limits
    MAX_RESUME_BYTES: int = 5242880  # 5 MiB

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.lstrip().startswith("["):
                parsed = json.loads(v)
                if not isinstance(parsed, list) or not all(isinstance(item, str) for item in parsed):
                    raise ValueError("CORS_ORIGINS must be a list of origin strings")
                return parsed
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        raise ValueError("CORS_ORIGINS must be a list or comma-separated string")


settings = Settings()
