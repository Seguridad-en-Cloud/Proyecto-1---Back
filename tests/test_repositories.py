"""Unit tests for repositories with mocked AsyncSession."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.repositories.user_repo import UserRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.repositories.category_repo import CategoryRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.dish_repo import DishRepository
from app.repositories.analytics_repo import AnalyticsRepository


# ── Helper to create a mock session ──

def _mock_session():
    s = AsyncMock()
    s.commit = AsyncMock()
    s.refresh = AsyncMock()
    s.delete = AsyncMock()
    s.add = MagicMock()
    return s


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalars_result(values):
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = values
    result.scalars.return_value = scalars
    return result


def _mock_scalar_one_result(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


# ═══════════════════════════════════════════════════════
# UserRepository
# ═══════════════════════════════════════════════════════

class TestUserRepository:
    @pytest.mark.asyncio
    async def test_create(self):
        session = _mock_session()
        repo = UserRepository(session)
        await repo.create("test@example.com", "hash123")
        session.add.assert_called_once()
        session.commit.assert_awaited_once()
        session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        session = _mock_session()
        user = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(user))
        repo = UserRepository(session)
        result = await repo.get_by_id(uuid.uuid4())
        assert result == user

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = UserRepository(session)
        result = await repo.get_by_id(uuid.uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_email(self):
        session = _mock_session()
        user = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(user))
        repo = UserRepository(session)
        result = await repo.get_by_email("test@example.com")
        assert result == user

    @pytest.mark.asyncio
    async def test_exists_by_email_true(self):
        session = _mock_session()
        user = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(user))
        repo = UserRepository(session)
        assert await repo.exists_by_email("test@example.com") is True

    @pytest.mark.asyncio
    async def test_exists_by_email_false(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = UserRepository(session)
        assert await repo.exists_by_email("nobody@example.com") is False


# ═══════════════════════════════════════════════════════
# RestaurantRepository
# ═══════════════════════════════════════════════════════

class TestRestaurantRepository:
    @pytest.mark.asyncio
    async def test_create(self):
        session = _mock_session()
        repo = RestaurantRepository(session)
        result = await repo.create(
            owner_user_id=uuid.uuid4(), name="Test", slug="test"
        )
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        session = _mock_session()
        rest = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(rest))
        repo = RestaurantRepository(session)
        assert await repo.get_by_id(uuid.uuid4()) == rest

    @pytest.mark.asyncio
    async def test_get_by_owner_id(self):
        session = _mock_session()
        rest = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(rest))
        repo = RestaurantRepository(session)
        assert await repo.get_by_owner_id(uuid.uuid4()) == rest

    @pytest.mark.asyncio
    async def test_get_by_slug(self):
        session = _mock_session()
        rest = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(rest))
        repo = RestaurantRepository(session)
        assert await repo.get_by_slug("test") == rest

    @pytest.mark.asyncio
    async def test_update(self):
        session = _mock_session()
        rest = MagicMock()
        rest.name = "Old"
        repo = RestaurantRepository(session)
        await repo.update(rest, name="New")
        assert rest.name == "New"
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_delete(self):
        session = _mock_session()
        rest = MagicMock()
        repo = RestaurantRepository(session)
        await repo.delete(rest)
        session.delete.assert_awaited_once_with(rest)
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_slug_exists_true(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(MagicMock()))
        repo = RestaurantRepository(session)
        assert await repo.slug_exists("test") is True

    @pytest.mark.asyncio
    async def test_slug_exists_false(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = RestaurantRepository(session)
        assert await repo.slug_exists("nope") is False


# ═══════════════════════════════════════════════════════
# CategoryRepository
# ═══════════════════════════════════════════════════════

class TestCategoryRepository:
    @pytest.mark.asyncio
    async def test_create_no_position(self):
        session = _mock_session()
        # get_next_position needs to work
        session.execute = AsyncMock(return_value=_mock_scalar_one_result(2))
        repo = CategoryRepository(session)
        await repo.create(
            restaurant_id=uuid.uuid4(), name="Drinks"
        )
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_position(self):
        session = _mock_session()
        repo = CategoryRepository(session)
        await repo.create(
            restaurant_id=uuid.uuid4(), name="Drinks", position=5
        )
        session.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id(self):
        session = _mock_session()
        cat = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(cat))
        repo = CategoryRepository(session)
        assert await repo.get_by_id(uuid.uuid4()) == cat

    @pytest.mark.asyncio
    async def test_list_by_restaurant(self):
        session = _mock_session()
        cats = [MagicMock(), MagicMock()]
        session.execute = AsyncMock(return_value=_mock_scalars_result(cats))
        repo = CategoryRepository(session)
        items = await repo.list_by_restaurant(uuid.uuid4())
        assert len(items) == 2

    @pytest.mark.asyncio
    async def test_list_by_restaurant_active_only(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalars_result([]))
        repo = CategoryRepository(session)
        items = await repo.list_by_restaurant(uuid.uuid4(), active_only=True)
        assert len(items) == 0

    @pytest.mark.asyncio
    async def test_update(self):
        session = _mock_session()
        cat = MagicMock()
        cat.name = "Old"
        repo = CategoryRepository(session)
        updated = await repo.update(cat, name="New")
        assert cat.name == "New"

    @pytest.mark.asyncio
    async def test_delete(self):
        session = _mock_session()
        cat = MagicMock()
        repo = CategoryRepository(session)
        await repo.delete(cat)
        session.delete.assert_awaited_once_with(cat)

    @pytest.mark.asyncio
    async def test_has_active_dishes(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_one_result(3))
        repo = CategoryRepository(session)
        assert await repo.has_active_dishes(uuid.uuid4()) is True

    @pytest.mark.asyncio
    async def test_has_no_active_dishes(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_one_result(0))
        repo = CategoryRepository(session)
        assert await repo.has_active_dishes(uuid.uuid4()) is False

    @pytest.mark.asyncio
    async def test_get_next_position(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(4))
        repo = CategoryRepository(session)
        pos = await repo.get_next_position(uuid.uuid4())
        assert pos == 5

    @pytest.mark.asyncio
    async def test_get_next_position_none(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = CategoryRepository(session)
        pos = await repo.get_next_position(uuid.uuid4())
        assert pos == 0

    @pytest.mark.asyncio
    async def test_reorder_categories(self):
        session = _mock_session()
        repo = CategoryRepository(session)
        ids = [uuid.uuid4(), uuid.uuid4()]
        await repo.reorder_categories(uuid.uuid4(), ids)
        # execute called once per id + final commit
        assert session.execute.await_count == 2
        session.commit.assert_awaited_once()


# ═══════════════════════════════════════════════════════
# RefreshTokenRepository
# ═══════════════════════════════════════════════════════

class TestRefreshTokenRepository:
    def test_hash_token(self):
        h = RefreshTokenRepository.hash_token("test-token")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA256 hex digest

    @pytest.mark.asyncio
    async def test_create(self):
        session = _mock_session()
        repo = RefreshTokenRepository(session)
        await repo.create(
            user_id=uuid.uuid4(), token="abc", expires_in_days=7
        )
        session.add.assert_called_once()
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_by_token_found(self):
        session = _mock_session()
        token_obj = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(token_obj))
        repo = RefreshTokenRepository(session)
        item = await repo.get_by_token("abc")
        assert item == token_obj

    @pytest.mark.asyncio
    async def test_get_by_token_not_found(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = RefreshTokenRepository(session)
        item = await repo.get_by_token("missing")
        assert item is None

    @pytest.mark.asyncio
    async def test_is_valid_true(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.revoked_at = None
        token_obj.expires_at = datetime.utcnow() + timedelta(days=1)
        session.execute = AsyncMock(return_value=_mock_scalar_result(token_obj))
        repo = RefreshTokenRepository(session)
        assert await repo.is_valid("valid-token") is True

    @pytest.mark.asyncio
    async def test_is_valid_not_found(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = RefreshTokenRepository(session)
        assert await repo.is_valid("ghost") is False

    @pytest.mark.asyncio
    async def test_is_valid_revoked(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.revoked_at = datetime.now(timezone.utc)
        token_obj.expires_at = datetime.now(timezone.utc) + timedelta(days=1)
        session.execute = AsyncMock(return_value=_mock_scalar_result(token_obj))
        repo = RefreshTokenRepository(session)
        assert await repo.is_valid("revoked") is False

    @pytest.mark.asyncio
    async def test_is_valid_expired(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.revoked_at = None
        token_obj.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        session.execute = AsyncMock(return_value=_mock_scalar_result(token_obj))
        repo = RefreshTokenRepository(session)
        assert await repo.is_valid("expired") is False

    @pytest.mark.asyncio
    async def test_revoke(self):
        session = _mock_session()
        token_obj = MagicMock()
        token_obj.revoked_at = None
        session.execute = AsyncMock(return_value=_mock_scalar_result(token_obj))
        repo = RefreshTokenRepository(session)
        await repo.revoke("token")
        assert token_obj.revoked_at is not None
        session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_revoke_not_found(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_result(None))
        repo = RefreshTokenRepository(session)
        await repo.revoke("missing")
        session.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_revoke_all_for_user(self):
        session = _mock_session()
        t1 = MagicMock()
        t1.revoked_at = None
        t2 = MagicMock()
        t2.revoked_at = None
        session.execute = AsyncMock(return_value=_mock_scalars_result([t1, t2]))
        repo = RefreshTokenRepository(session)
        await repo.revoke_all_for_user(uuid.uuid4())
        assert t1.revoked_at is not None
        assert t2.revoked_at is not None
        session.commit.assert_awaited_once()


# ═══════════════════════════════════════════════════════
# DishRepository (key methods)
# ═══════════════════════════════════════════════════════

class TestDishRepository:
    @pytest.mark.asyncio
    async def test_get_by_id(self):
        session = _mock_session()
        dish = MagicMock()
        session.execute = AsyncMock(return_value=_mock_scalar_result(dish))
        repo = DishRepository(session)
        assert await repo.get_by_id(uuid.uuid4()) == dish

    @pytest.mark.asyncio
    async def test_update(self):
        session = _mock_session()
        dish = MagicMock()
        dish.name = "Old"
        repo = DishRepository(session)
        updated = await repo.update(dish, name="New", price="15.00")
        assert dish.name == "New"

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        session = _mock_session()
        dish = MagicMock()
        dish.deleted_at = None
        repo = DishRepository(session)
        deleted = await repo.soft_delete(dish)
        assert dish.deleted_at is not None

    @pytest.mark.asyncio
    async def test_toggle_availability(self):
        session = _mock_session()
        dish = MagicMock()
        dish.available = True
        repo = DishRepository(session)
        toggled = await repo.toggle_availability(dish)
        assert dish.available is False


# ═══════════════════════════════════════════════════════
# AnalyticsRepository (key method)
# ═══════════════════════════════════════════════════════

class TestAnalyticsRepository:
    @pytest.mark.asyncio
    async def test_get_total_scans(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_one_result(42))
        repo = AnalyticsRepository(session)
        result = await repo.get_total_scans(uuid.uuid4())
        assert result == 42

    @pytest.mark.asyncio
    async def test_get_total_scans_with_dates(self):
        session = _mock_session()
        session.execute = AsyncMock(return_value=_mock_scalar_one_result(5))
        repo = AnalyticsRepository(session)
        result = await repo.get_total_scans(
            uuid.uuid4(),
            from_date=datetime(2025, 1, 1),
            to_date=datetime(2025, 1, 31),
        )
        assert result == 5
