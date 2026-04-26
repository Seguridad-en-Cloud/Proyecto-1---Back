"""Application configuration using pydantic-settings.

In local/dev environments values come from ``.env`` or ``os.environ``.
In production (``GCP_PROJECT_ID`` is set) the sensitive fields
(``JWT_SECRET``, ``IP_HASH_SALT``, ``DATABASE_URL``) are pulled from
GCP Secret Manager via :mod:`app.core.secrets`.
"""
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.secrets import get_secret


class Settings(BaseSettings):
    """Application settings loaded from environment variables / Secret Manager."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_parse_none_str="",
    )

    # ── App ──────────────────────────────────────────────────────────────
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_name: str = Field(default="livemenu-api", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")

    # ── GCP ──────────────────────────────────────────────────────────────
    gcp_project_id: str | None = Field(default=None, alias="GCP_PROJECT_ID")

    # ── CORS ─────────────────────────────────────────────────────────────
    cors_origins: str | list[str] = Field(
        default="http://localhost:3000,http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="after")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Accept either a JSON list or a comma-separated string."""
        if isinstance(v, list):
            return v
        v = v.strip()
        if v.startswith("["):
            import json
            return [str(o).strip() for o in json.loads(v)]
        return [origin.strip() for origin in v.split(",") if origin.strip()]

    # ── Database ─────────────────────────────────────────────────────────
    # When CLOUD_SQL_CONNECTION_NAME is set we connect through the Cloud SQL
    # connector (Unix socket / IAM auth); the database_url field is then
    # treated as a fallback only.
    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://livemenu:livemenu@db:5432/livemenu",
        alias="DATABASE_URL",
    )
    cloud_sql_connection_name: str | None = Field(
        default=None, alias="CLOUD_SQL_CONNECTION_NAME"
    )
    db_user: str | None = Field(default=None, alias="DB_USER")
    db_name: str | None = Field(default=None, alias="DB_NAME")

    # ── JWT ──────────────────────────────────────────────────────────────
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_ttl_min: int = Field(default=15, alias="JWT_ACCESS_TTL_MIN")
    jwt_refresh_ttl_days: int = Field(default=7, alias="JWT_REFRESH_TTL_DAYS")

    # ── Security ─────────────────────────────────────────────────────────
    ip_hash_salt: str = Field(default="change-me-too", alias="IP_HASH_SALT")
    # Number of proxies/load-balancers in front of the app. Used by the rate
    # limiter to pick the correct entry from X-Forwarded-For. On Cloud Run
    # behind a Global LB this is typically 1.
    trusted_proxies: int = Field(default=0, alias="TRUSTED_PROXIES")

    # ── Rate limiting ────────────────────────────────────────────────────
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")

    # ── Logging ──────────────────────────────────────────────────────────
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # ── API Docs ─────────────────────────────────────────────────────────
    enable_docs: bool = Field(default=True, alias="ENABLE_DOCS")

    # ── Object storage ───────────────────────────────────────────────────
    storage_backend: Literal["s3", "gcs"] = Field(
        default="s3", alias="STORAGE_BACKEND"
    )
    # S3/MinIO (used for local dev)
    s3_endpoint: str = Field(default="http://minio:9000", alias="S3_ENDPOINT")
    s3_access_key: str = Field(default="minioadmin", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="minioadmin", alias="S3_SECRET_KEY")
    s3_bucket: str = Field(default="livemenu", alias="S3_BUCKET")
    s3_public_url: str = Field(
        default="http://localhost:9000/livemenu", alias="S3_PUBLIC_URL"
    )
    # GCS (used in GCP)
    gcs_bucket: str | None = Field(default=None, alias="GCS_BUCKET")
    # Optional CDN / custom-domain prefix served in front of the bucket. When
    # unset, public URLs use ``https://storage.googleapis.com/<bucket>``.
    gcs_public_url: str | None = Field(default=None, alias="GCS_PUBLIC_URL")

    # ── Image processing ─────────────────────────────────────────────────
    image_max_size_mb: int = Field(default=5, alias="IMAGE_MAX_SIZE_MB")
    image_worker_count: int = Field(default=4, alias="IMAGE_WORKER_COUNT")


def _build_settings() -> Settings:
    """Build :class:`Settings`, overlaying secrets from Secret Manager.

    On GCP we never want a baked-in ``JWT_SECRET`` to reach memory: the value
    must come from Secret Manager. We therefore resolve secrets *after*
    pydantic loads the file/env, and overwrite the corresponding fields.
    """
    s = Settings()

    if s.gcp_project_id:
        # Each call hits Secret Manager (cached). If a secret is missing we
        # keep whatever pydantic loaded so the failure surfaces at use-site.
        if (jwt := get_secret("JWT_SECRET")):
            s.jwt_secret = jwt
        if (salt := get_secret("IP_HASH_SALT")):
            s.ip_hash_salt = salt
        if (db_url := get_secret("DATABASE_URL")):
            s.database_url = db_url  # type: ignore[assignment]

    return s


settings = _build_settings()
