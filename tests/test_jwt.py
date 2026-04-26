"""Unit tests for JWT token utilities."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt, JWTError

from app.core.security.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_access_token,
    verify_refresh_token,
)
from app.core.config import settings


class TestCreateAccessToken:
    """Tests for create_access_token."""

    def test_returns_string(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, "a@b.com")
        assert isinstance(token, str)

    def test_payload_contains_required_fields(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, "a@b.com")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == str(uid)
        assert payload["email"] == "a@b.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_token_expiry_matches_setting(self):
        uid = uuid.uuid4()
        token = create_access_token(uid, "a@b.com")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        # exp - iat should be close to jwt_access_ttl_min * 60
        diff = payload["exp"] - payload["iat"]
        expected = settings.jwt_access_ttl_min * 60
        assert abs(diff - expected) < 5  # within 5 seconds tolerance


class TestCreateRefreshToken:
    """Tests for create_refresh_token."""

    def test_returns_string(self):
        token = create_refresh_token(uuid.uuid4(), "a@b.com")
        assert isinstance(token, str)

    def test_type_is_refresh(self):
        token = create_refresh_token(uuid.uuid4(), "a@b.com")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "refresh"

    def test_token_expiry_matches_setting(self):
        uid = uuid.uuid4()
        token = create_refresh_token(uid, "a@b.com")
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        diff = payload["exp"] - payload["iat"]
        expected = settings.jwt_refresh_ttl_days * 86400
        assert abs(diff - expected) < 5


class TestDecodeToken:
    """Tests for decode_token."""

    def test_decodes_valid_token(self):
        token = create_access_token(uuid.uuid4(), "x@y.com")
        payload = decode_token(token)
        assert payload["email"] == "x@y.com"

    def test_raises_on_invalid_token(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_raises_on_expired_token(self):
        # Create a token that is already expired
        payload = {
            "sub": str(uuid.uuid4()),
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        with pytest.raises(JWTError):
            decode_token(token)


class TestVerifyAccessToken:
    """Tests for verify_access_token."""

    def test_accepts_access_token(self):
        token = create_access_token(uuid.uuid4(), "a@b.com")
        payload = verify_access_token(token)
        assert payload["type"] == "access"

    def test_rejects_refresh_token(self):
        token = create_refresh_token(uuid.uuid4(), "a@b.com")
        with pytest.raises(JWTError):
            verify_access_token(token)


class TestVerifyRefreshToken:
    """Tests for verify_refresh_token."""

    def test_accepts_refresh_token(self):
        token = create_refresh_token(uuid.uuid4(), "a@b.com")
        payload = verify_refresh_token(token)
        assert payload["type"] == "refresh"

    def test_rejects_access_token(self):
        token = create_access_token(uuid.uuid4(), "a@b.com")
        with pytest.raises(JWTError):
            verify_refresh_token(token)
