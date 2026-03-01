"""Unit tests for CategoryService using mocked repositories."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate


def _make_restaurant(rid=None, owner_id=None):
    r = MagicMock()
    r.id = rid or uuid.uuid4()
    r.owner_user_id = owner_id or uuid.uuid4()
    return r


def _make_category(cid=None, restaurant_id=None):
    c = MagicMock()
    c.id = cid or uuid.uuid4()
    c.restaurant_id = restaurant_id or uuid.uuid4()
    c.name = "Drinks"
    c.description = "Beverages"
    c.position = 1
    c.active = True
    c.created_at = datetime(2025, 1, 1)
    c.updated_at = datetime(2025, 1, 1)
    return c


@pytest.fixture
def service():
    session = AsyncMock()
    svc = CategoryService(session)
    svc.repo = AsyncMock()
    svc.restaurant_repo = AsyncMock()
    return svc


# ── _verify_restaurant_ownership ──

@pytest.mark.asyncio
async def test_verify_ownership_not_found(service):
    service.restaurant_repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service._verify_restaurant_ownership(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_ownership_forbidden(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    with pytest.raises(HTTPException) as exc:
        await service._verify_restaurant_ownership(rest.id, uuid.uuid4())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_ownership_ok(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    # Should not raise
    await service._verify_restaurant_ownership(rest.id, rest.owner_user_id)


# ── list_categories ──

@pytest.mark.asyncio
async def test_list_categories_success(service):
    rest = _make_restaurant()
    cats = [_make_category(restaurant_id=rest.id)]
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.list_by_restaurant = AsyncMock(return_value=cats)

    result = await service.list_categories(rest.owner_user_id)
    assert len(result) == 1


@pytest.mark.asyncio
async def test_list_categories_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.list_categories(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_categories_active_only(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.list_by_restaurant = AsyncMock(return_value=[])

    await service.list_categories(rest.owner_user_id, active_only=True)
    service.repo.list_by_restaurant.assert_awaited_once_with(rest.id, True)


# ── create ──

@pytest.mark.asyncio
async def test_create_category_success(service):
    rest = _make_restaurant()
    cat = _make_category(restaurant_id=rest.id)
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.create = AsyncMock(return_value=cat)

    data = CategoryCreate(name="Drinks")
    result = await service.create(rest.owner_user_id, data)
    assert result == cat


@pytest.mark.asyncio
async def test_create_category_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    data = CategoryCreate(name="Drinks")
    with pytest.raises(HTTPException) as exc:
        await service.create(uuid.uuid4(), data)
    assert exc.value.status_code == 404


# ── update ──

@pytest.mark.asyncio
async def test_update_category_success(service):
    rest = _make_restaurant()
    cat = _make_category(restaurant_id=rest.id)
    service.repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    updated = _make_category(cid=cat.id, restaurant_id=rest.id)
    updated.name = "Updated"
    service.repo.update = AsyncMock(return_value=updated)

    data = CategoryUpdate(name="Updated")
    result = await service.update(cat.id, rest.owner_user_id, data)
    assert result.name == "Updated"


@pytest.mark.asyncio
async def test_update_category_not_found(service):
    service.repo.get_by_id = AsyncMock(return_value=None)
    data = CategoryUpdate(name="Updated")
    with pytest.raises(HTTPException) as exc:
        await service.update(uuid.uuid4(), uuid.uuid4(), data)
    assert exc.value.status_code == 404


# ── delete ──

@pytest.mark.asyncio
async def test_delete_category_success(service):
    rest = _make_restaurant()
    cat = _make_category(restaurant_id=rest.id)
    service.repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.has_active_dishes = AsyncMock(return_value=False)
    service.repo.delete = AsyncMock()

    await service.delete(cat.id, rest.owner_user_id)
    service.repo.delete.assert_awaited_once_with(cat)


@pytest.mark.asyncio
async def test_delete_category_not_found(service):
    service.repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.delete(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_category_has_active_dishes(service):
    rest = _make_restaurant()
    cat = _make_category(restaurant_id=rest.id)
    service.repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.has_active_dishes = AsyncMock(return_value=True)

    with pytest.raises(HTTPException) as exc:
        await service.delete(cat.id, rest.owner_user_id)
    assert exc.value.status_code == 409


# ── reorder ──

@pytest.mark.asyncio
async def test_reorder_success(service):
    rest = _make_restaurant()
    cat1 = _make_category(restaurant_id=rest.id)
    cat2 = _make_category(restaurant_id=rest.id)
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_by_id = AsyncMock(side_effect=[cat1, cat2])
    service.repo.reorder_categories = AsyncMock()

    await service.reorder(rest.owner_user_id, [cat1.id, cat2.id])
    service.repo.reorder_categories.assert_awaited_once()


@pytest.mark.asyncio
async def test_reorder_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.reorder(uuid.uuid4(), [uuid.uuid4()])
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_reorder_wrong_category(service):
    rest = _make_restaurant()
    cat = _make_category()  # different restaurant_id
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_by_id = AsyncMock(return_value=cat)

    with pytest.raises(HTTPException) as exc:
        await service.reorder(rest.owner_user_id, [cat.id])
    assert exc.value.status_code == 400
