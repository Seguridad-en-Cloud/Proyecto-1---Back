"""Unit tests for AuthService using mocked repositories."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.auth_service import AuthService


def _make_user(user_id=None, email="test@example.com"):
    user = MagicMock()
    user.id = user_id or uuid.uuid4()
    user.email = email
    user.password_hash = "$2b$12$hashhashhash"
    user.created_at = datetime(2025, 1, 1)
    return user


@pytest.fixture
def service():
    session = AsyncMock()
    svc = AuthService(session)
    svc.user_repo = AsyncMock()
    svc.refresh_token_repo = AsyncMock()
    return svc


# ── register ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(service):
    service.user_repo.exists_by_email = AsyncMock(return_value=False)
    user = _make_user()
    service.user_repo.create = AsyncMock(return_value=user)

    with patch("app.services.auth_service.hash_password", return_value="hashed"), \
         patch("app.services.auth_service.create_access_token", return_value="at"), \
         patch("app.services.auth_service.create_refresh_token", return_value="rt"):
        result_user, at, rt = await service.register("test@example.com", "password123")

    assert at == "at"
    assert rt == "rt"
    service.user_repo.create.assert_awaited_once()
    service.refresh_token_repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_duplicate_email(service):
    service.user_repo.exists_by_email = AsyncMock(return_value=True)
    with pytest.raises(HTTPException) as exc_info:
        await service.register("dup@example.com", "password123")
    assert exc_info.value.status_code == 409


# ── login ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(service):
    user = _make_user()
    service.user_repo.get_by_email = AsyncMock(return_value=user)

    with patch("app.services.auth_service.verify_password", return_value=True), \
         patch("app.services.auth_service.create_access_token", return_value="at"), \
         patch("app.services.auth_service.create_refresh_token", return_value="rt"):
        result_user, at, rt = await service.login("test@example.com", "password123")

    assert result_user == user
    assert at == "at"
    assert rt == "rt"


@pytest.mark.asyncio
async def test_login_user_not_found(service):
    service.user_repo.get_by_email = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc_info:
        await service.login("missing@example.com", "password123")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(service):
    user = _make_user()
    service.user_repo.get_by_email = AsyncMock(return_value=user)
    with patch("app.services.auth_service.verify_password", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await service.login("test@example.com", "wrong")
    assert exc_info.value.status_code == 401


# ── refresh ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_success(service):
    uid = uuid.uuid4()
    payload = {"sub": str(uid), "email": "test@example.com"}
    service.refresh_token_repo.is_valid = AsyncMock(return_value=True)
    service.refresh_token_repo.revoke = AsyncMock()
    service.refresh_token_repo.create = AsyncMock()

    with patch("app.services.auth_service.verify_refresh_token", return_value=payload), \
         patch("app.services.auth_service.create_access_token", return_value="new_at"), \
         patch("app.services.auth_service.create_refresh_token", return_value="new_rt"):
        new_at, new_rt = await service.refresh("old_rt")

    assert new_at == "new_at"
    assert new_rt == "new_rt"
    service.refresh_token_repo.revoke.assert_awaited_once_with("old_rt")


@pytest.mark.asyncio
async def test_refresh_invalid_token(service):
    uid = uuid.uuid4()
    payload = {"sub": str(uid), "email": "test@example.com"}
    service.refresh_token_repo.is_valid = AsyncMock(return_value=False)

    with patch("app.services.auth_service.verify_refresh_token", return_value=payload):
        with pytest.raises(HTTPException) as exc_info:
            await service.refresh("bad_rt")
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_expired_jwt(service):
    with patch("app.services.auth_service.verify_refresh_token", side_effect=Exception("expired")):
        with pytest.raises(HTTPException) as exc_info:
            await service.refresh("expired_rt")
    assert exc_info.value.status_code == 401


# ── logout ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout(service):
    uid = uuid.uuid4()
    await service.logout(uid)
    service.refresh_token_repo.revoke_all_for_user.assert_awaited_once_with(uid)
