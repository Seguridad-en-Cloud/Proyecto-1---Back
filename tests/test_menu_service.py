"""Unit tests for MenuService using mocked repositories."""
import uuid
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.menu_service import MenuService


def _make_restaurant(slug="test-slug"):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.name = "Test Restaurant"
    r.slug = slug
    r.description = "Great food"
    r.logo_url = None
    r.phone = "555-0000"
    r.address = "123 Main St"
    r.hours = {"mon": "9-17"}
    return r


def _make_dish(available=True, deleted_at=None, position=1):
    d = MagicMock()
    d.id = uuid.uuid4()
    d.name = "Burger"
    d.description = "Juicy"
    d.price = Decimal("12.00")
    d.sale_price = None
    d.image_url = None
    d.tags = ["beef"]
    d.featured = True
    d.position = position
    d.available = available
    d.deleted_at = deleted_at
    d.created_at = datetime(2025, 1, 1)
    return d


def _make_category(dishes=None, active=True, position=1):
    c = MagicMock()
    c.id = uuid.uuid4()
    c.name = "Main Course"
    c.description = "Best dishes"
    c.position = position
    c.active = active
    c.dishes = dishes or []
    c.created_at = datetime(2025, 1, 1)
    return c


@pytest.fixture
def service():
    session = AsyncMock()
    svc = MenuService(session)
    svc.repo = AsyncMock()
    return svc


@pytest.mark.asyncio
@patch("app.services.menu_service.cache_get", return_value=None)
@patch("app.services.menu_service.cache_set")
async def test_get_menu_not_found(mock_set, mock_get, service):
    service.repo.get_by_slug = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.get_menu_by_slug("missing")
    assert exc.value.status_code == 404


@pytest.mark.asyncio
@patch("app.services.menu_service.cache_get")
async def test_get_menu_from_cache(mock_get, service):
    cached = MagicMock()
    mock_get.return_value = cached
    result = await service.get_menu_by_slug("cached-slug")
    assert result == cached
    # repo should not be called when cache hit
    service.repo.get_by_slug.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.menu_service.cache_get", return_value=None)
@patch("app.services.menu_service.cache_set")
async def test_get_menu_success_with_dishes(mock_set, mock_get, service):
    rest = _make_restaurant()
    service.repo.get_by_slug = AsyncMock(return_value=rest)

    dish = _make_dish(available=True)
    category = _make_category(dishes=[dish])

    # Mock the SQLAlchemy query execution
    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [category]
    mock_result.scalars.return_value = mock_scalars
    service.session.execute = AsyncMock(return_value=mock_result)

    result = await service.get_menu_by_slug("test-slug")
    assert result.restaurant_name == "Test Restaurant"
    assert len(result.categories) == 1
    assert len(result.categories[0].dishes) == 1
    mock_set.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.menu_service.cache_get", return_value=None)
@patch("app.services.menu_service.cache_set")
async def test_get_menu_filters_unavailable_dishes(mock_set, mock_get, service):
    rest = _make_restaurant()
    service.repo.get_by_slug = AsyncMock(return_value=rest)

    available = _make_dish(available=True)
    unavailable = _make_dish(available=False)
    deleted = _make_dish(available=True, deleted_at=datetime(2025, 6, 1))

    category = _make_category(dishes=[available, unavailable, deleted])

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [category]
    mock_result.scalars.return_value = mock_scalars
    service.session.execute = AsyncMock(return_value=mock_result)

    result = await service.get_menu_by_slug("test-slug")
    # Only the available and non-deleted dish should be included
    assert len(result.categories) == 1
    assert len(result.categories[0].dishes) == 1


@pytest.mark.asyncio
@patch("app.services.menu_service.cache_get", return_value=None)
@patch("app.services.menu_service.cache_set")
async def test_get_menu_empty_categories_filtered(mock_set, mock_get, service):
    rest = _make_restaurant()
    service.repo.get_by_slug = AsyncMock(return_value=rest)

    # Category with no available dishes
    category = _make_category(dishes=[_make_dish(available=False)])

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [category]
    mock_result.scalars.return_value = mock_scalars
    service.session.execute = AsyncMock(return_value=mock_result)

    result = await service.get_menu_by_slug("test-slug")
    assert len(result.categories) == 0
