"""Unit tests for API dependencies (deps.py)."""
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.deps import get_current_user_id
from app.core.config import settings


def _make_credentials(token: str):
    cred = MagicMock()
    cred.credentials = token
    return cred


def _make_valid_token(user_id: uuid.UUID | None = None) -> str:
    uid = user_id or uuid.uuid4()
    payload = {
        "sub": str(uid),
        "email": "test@example.com",
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@pytest.mark.asyncio
async def test_get_current_user_id_valid_token():
    uid = uuid.uuid4()
    token = _make_valid_token(uid)
    cred = _make_credentials(token)
    result = await get_current_user_id(cred)
    assert result == uid


@pytest.mark.asyncio
async def test_get_current_user_id_invalid_token():
    cred = _make_credentials("totally.invalid.token")
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(cred)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_id_expired_token():
    import time
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "type": "access",
        "exp": int(time.time()) - 3600,  # expired 1 hour ago
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    cred = _make_credentials(token)
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(cred)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_id_wrong_secret():
    payload = {
        "sub": str(uuid.uuid4()),
        "email": "test@example.com",
        "type": "access",
    }
    token = jwt.encode(payload, "wrong-secret", algorithm=settings.jwt_algorithm)
    cred = _make_credentials(token)
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(cred)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_id_bad_uuid():
    payload = {
        "sub": "not-a-uuid",
        "email": "test@example.com",
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    cred = _make_credentials(token)
    with pytest.raises(HTTPException) as exc:
        await get_current_user_id(cred)
    assert exc.value.status_code == 401
