"""Application configuration using pydantic-settings."""
from typing import Any

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="",  # Don't try to parse empty strings
    )

    # App settings
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_name: str = Field(default="livemenu-api", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    
    # CORS settings
    cors_origins: str | list[str] = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS"
    )
    
    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    # Database settings
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://livemenu:livemenu@db:5432/livemenu",
        alias="DATABASE_URL"
    )
    
    # JWT settings
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_ttl_min: int = Field(default=15, alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(default=7, alias="JWT_REFRESH_TTL_DAYS")
    
    # Security settings
    ip_hash_salt: str = Field(default="change-me-too", alias="IP_HASH_SALT")
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    
    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # API Docs (disable in production)
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")


# Global settings instance
settings = Settings()
