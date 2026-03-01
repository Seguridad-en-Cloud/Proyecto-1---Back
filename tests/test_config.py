"""Unit tests for Settings configuration."""
from app.core.config import Settings, settings


class TestSettings:
    def test_singleton_exists(self):
        assert settings is not None

    def test_default_app_name(self):
        assert settings.app_name == "livemenu-api"

    def test_default_jwt_algorithm(self):
        assert settings.jwt_algorithm == "HS256"

    def test_default_jwt_access_ttl(self):
        assert settings.jwt_access_ttl_min == 15

    def test_default_jwt_refresh_ttl(self):
        assert settings.jwt_refresh_ttl_days == 7

    def test_default_rate_limit(self):
        assert settings.rate_limit_per_minute == 100

    def test_default_image_max_size(self):
        assert settings.image_max_size_mb == 5

    def test_default_image_worker_count(self):
        assert settings.image_worker_count == 4

    def test_cors_origins_is_list(self):
        assert isinstance(settings.cors_origins, list)

    def test_cors_origins_parsing(self):
        s = Settings(CORS_ORIGINS="http://a.com, http://b.com")
        assert len(s.cors_origins) == 2
        assert "http://a.com" in s.cors_origins

    def test_cors_origins_from_list(self):
        s = Settings(CORS_ORIGINS=["http://a.com", "http://b.com"])
        assert len(s.cors_origins) == 2

    def test_s3_defaults(self):
        assert settings.s3_bucket == "livemenu"
        assert "minio" in settings.s3_endpoint or "localhost" in settings.s3_endpoint

    def test_log_level_default(self):
        assert settings.log_level.upper() in ("DEBUG", "INFO", "WARNING", "ERROR")

    def test_enable_docs_default(self):
        assert isinstance(settings.enable_docs, bool)
