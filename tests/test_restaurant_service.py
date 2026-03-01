"""Unit tests for RestaurantService using mocked repositories."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.restaurant_service import RestaurantService
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def _make_restaurant(rid=None, owner_id=None, name="My Restaurant", slug="my-restaurant"):
    r = MagicMock()
    r.id = rid or uuid.uuid4()
    r.owner_user_id = owner_id or uuid.uuid4()
    r.name = name
    r.slug = slug
    r.description = "desc"
    r.logo_url = None
    r.phone = None
    r.address = None
    r.hours = None
    r.created_at = datetime(2025, 1, 1)
    r.updated_at = datetime(2025, 1, 1)
    return r


@pytest.fixture
def service():
    session = AsyncMock()
    svc = RestaurantService(session)
    svc.repo = AsyncMock()
    return svc


# ── get_by_owner ──────────────────────────────────

@pytest.mark.asyncio
async def test_get_by_owner_found(service):
    rest = _make_restaurant()
    service.repo.get_by_owner_id = AsyncMock(return_value=rest)
    result = await service.get_by_owner(rest.owner_user_id)
    assert result == rest


@pytest.mark.asyncio
async def test_get_by_owner_not_found(service):
    service.repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.get_by_owner(uuid.uuid4())
    assert exc.value.status_code == 404


# ── create ──────────────────────────────────

@pytest.mark.asyncio
async def test_create_success(service):
    owner_id = uuid.uuid4()
    service.repo.get_by_owner_id = AsyncMock(return_value=None)
    service.repo.get_by_slug = AsyncMock(return_value=None)
    new_rest = _make_restaurant(owner_id=owner_id)
    service.repo.create = AsyncMock(return_value=new_rest)

    data = RestaurantCreate(name="My Restaurant")
    result = await service.create(owner_id, data)
    assert result == new_rest
    service.repo.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_already_has_restaurant(service):
    owner_id = uuid.uuid4()
    service.repo.get_by_owner_id = AsyncMock(return_value=_make_restaurant(owner_id=owner_id))
    data = RestaurantCreate(name="New")
    with pytest.raises(HTTPException) as exc:
        await service.create(owner_id, data)
    assert exc.value.status_code == 409


# ── update ──────────────────────────────────

@pytest.mark.asyncio
async def test_update_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    service.repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.update = AsyncMock(return_value=rest)

    data = RestaurantUpdate(description="Updated desc")
    result = await service.update(owner_id, data)
    assert result == rest
    service.repo.update.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_with_name_regenerates_slug(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    service.repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_by_slug = AsyncMock(return_value=None)
    service.repo.update = AsyncMock(return_value=rest)

    data = RestaurantUpdate(name="New Name")
    await service.update(owner_id, data)
    # verify slug was passed to update
    call_kwargs = service.repo.update.call_args
    assert "slug" in call_kwargs.kwargs or any("slug" in str(a) for a in call_kwargs.args)


@pytest.mark.asyncio
async def test_update_not_found(service):
    service.repo.get_by_owner_id = AsyncMock(return_value=None)
    data = RestaurantUpdate(description="x")
    with pytest.raises(HTTPException) as exc:
        await service.update(uuid.uuid4(), data)
    assert exc.value.status_code == 404


# ── delete ──────────────────────────────────

@pytest.mark.asyncio
async def test_delete_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    service.repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.delete = AsyncMock()
    await service.delete(owner_id)
    service.repo.delete.assert_awaited_once_with(rest)


@pytest.mark.asyncio
async def test_delete_not_found(service):
    service.repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.delete(uuid.uuid4())
    assert exc.value.status_code == 404


# ── _ensure_unique_slug ──────────────────────────────────

@pytest.mark.asyncio
async def test_ensure_unique_slug_available(service):
    service.repo.get_by_slug = AsyncMock(return_value=None)
    result = await service._ensure_unique_slug("my-slug")
    assert result == "my-slug"


@pytest.mark.asyncio
async def test_ensure_unique_slug_with_collision(service):
    existing = _make_restaurant(slug="my-slug")
    service.repo.get_by_slug = AsyncMock(side_effect=[existing, None])
    result = await service._ensure_unique_slug("my-slug")
    assert result == "my-slug-1"


@pytest.mark.asyncio
async def test_ensure_unique_slug_exclude_self(service):
    rest = _make_restaurant(slug="my-slug")
    service.repo.get_by_slug = AsyncMock(return_value=rest)
    result = await service._ensure_unique_slug("my-slug", exclude_id=rest.id)
    assert result == "my-slug"
