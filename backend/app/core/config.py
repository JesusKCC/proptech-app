import os
from typing import List
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "PropTech Commercial Asset Management API"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "proptech-super-secret-key-change-in-production-2026"
    WEBHOOK_HMAC_SECRET: str = "proptech-webhook-hmac-secret-2026"
    
    # Dual database support: PostgreSQL/PostGIS in production/Docker, SQLite fallback on local Windows
    DATABASE_URL: str = "sqlite+aiosqlite:///./proptech.db"
    SYNC_DATABASE_URL: str = "sqlite:///./proptech.db"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]
    
    # Blueprints directory
    BLUEPRINTS_DIR: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "static", "blueprints")
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow"
    )

    @field_validator("SYNC_DATABASE_URL", mode="before")
    @classmethod
    def assemble_sync_db_url(cls, v: str | None, info) -> str:
        if v:
            return v
        db_url = info.data.get("DATABASE_URL", "sqlite+aiosqlite:///./proptech.db")
        if db_url.startswith("postgresql+asyncpg://"):
            return db_url.replace("postgresql+asyncpg://", "postgresql://")
        elif db_url.startswith("sqlite+aiosqlite:///"):
            return db_url.replace("sqlite+aiosqlite:///", "sqlite:///")
        return db_url


settings = Settings()
