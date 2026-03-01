"""Unit tests for DishService using mocked repositories."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.dish_service import DishService
from app.schemas.dish import DishCreate, DishUpdate


def _make_restaurant(rid=None, owner_id=None):
    r = MagicMock()
    r.id = rid or uuid.uuid4()
    r.owner_user_id = owner_id or uuid.uuid4()
    return r


def _make_category(cid=None, restaurant_id=None):
    c = MagicMock()
    c.id = cid or uuid.uuid4()
    c.restaurant_id = restaurant_id or uuid.uuid4()
    return c


def _make_dish(did=None, category_id=None):
    d = MagicMock()
    d.id = did or uuid.uuid4()
    d.category_id = category_id or uuid.uuid4()
    d.name = "Pizza"
    d.description = "Margherita"
    d.price = Decimal("10.00")
    d.sale_price = None
    d.image_url = None
    d.available = True
    d.featured = False
    d.tags = ["italian"]
    d.position = 1
    d.created_at = datetime(2025, 1, 1)
    d.updated_at = datetime(2025, 1, 1)
    d.deleted_at = None
    return d


@pytest.fixture
def service():
    session = AsyncMock()
    svc = DishService(session)
    svc.repo = AsyncMock()
    svc.category_repo = AsyncMock()
    svc.restaurant_repo = AsyncMock()
    return svc


# ── _verify_category_ownership ──

@pytest.mark.asyncio
async def test_verify_category_not_found(service):
    service.category_repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service._verify_category_ownership(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_verify_category_forbidden(service):
    cat = _make_category()
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    rest = _make_restaurant(rid=cat.restaurant_id)
    rest.owner_user_id = uuid.uuid4()
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    with pytest.raises(HTTPException) as exc:
        await service._verify_category_ownership(cat.id, uuid.uuid4())
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_verify_category_restaurant_not_found(service):
    cat = _make_category()
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service._verify_category_ownership(cat.id, uuid.uuid4())
    assert exc.value.status_code == 403


# ── list_dishes ──

@pytest.mark.asyncio
async def test_list_dishes_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)

    dish = _make_dish()
    service.repo.list_dishes = AsyncMock(return_value=([dish], 1))

    result = await service.list_dishes(owner_id)
    assert result.total == 1
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_list_dishes_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.list_dishes(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_dishes_with_category_filter(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.list_dishes = AsyncMock(return_value=([], 0))

    result = await service.list_dishes(owner_id, category_id=cat.id)
    assert result.total == 0


# ── get_dish ──

@pytest.mark.asyncio
async def test_get_dish_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat.id)

    service.repo.get_by_id = AsyncMock(return_value=dish)
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)

    result = await service.get_dish(dish.id, owner_id)
    assert result == dish


@pytest.mark.asyncio
async def test_get_dish_not_found(service):
    service.repo.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.get_dish(uuid.uuid4(), uuid.uuid4())
    assert exc.value.status_code == 404


# ── create ──

@pytest.mark.asyncio
async def test_create_dish_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat.id)

    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.create = AsyncMock(return_value=dish)

    data = DishCreate(category_id=cat.id, name="Pizza", price=Decimal("10.00"))
    result = await service.create(owner_id, data)
    assert result == dish


# ── update ──

@pytest.mark.asyncio
async def test_update_dish_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat.id)

    service.repo.get_by_id = AsyncMock(return_value=dish)
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.update = AsyncMock(return_value=dish)

    data = DishUpdate(name="Updated Pizza")
    result = await service.update(dish.id, owner_id, data)
    assert result == dish


@pytest.mark.asyncio
async def test_update_dish_change_category(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat1 = _make_category(restaurant_id=rest.id)
    cat2 = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat1.id)

    service.repo.get_by_id = AsyncMock(return_value=dish)
    service.category_repo.get_by_id = AsyncMock(side_effect=[cat1, cat2])
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.update = AsyncMock(return_value=dish)

    data = DishUpdate(category_id=cat2.id)
    result = await service.update(dish.id, owner_id, data)
    assert result == dish


# ── delete ──

@pytest.mark.asyncio
async def test_delete_dish_success(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat.id)

    service.repo.get_by_id = AsyncMock(return_value=dish)
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    service.repo.soft_delete = AsyncMock(return_value=dish)

    result = await service.delete(dish.id, owner_id)
    assert result == dish


# ── toggle_availability ──

@pytest.mark.asyncio
async def test_toggle_availability(service):
    owner_id = uuid.uuid4()
    rest = _make_restaurant(owner_id=owner_id)
    cat = _make_category(restaurant_id=rest.id)
    dish = _make_dish(category_id=cat.id)

    service.repo.get_by_id = AsyncMock(return_value=dish)
    service.category_repo.get_by_id = AsyncMock(return_value=cat)
    service.restaurant_repo.get_by_id = AsyncMock(return_value=rest)
    toggled = _make_dish(category_id=cat.id)
    toggled.available = False
    service.repo.toggle_availability = AsyncMock(return_value=toggled)

    result = await service.toggle_availability(dish.id, owner_id)
    assert result.available is False
