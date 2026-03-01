"""Unit tests for Pydantic schemas."""
import uuid
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas.auth import RegisterRequest, LoginRequest, RefreshRequest, TokenResponse, AuthResponse, UserResponse
from app.schemas.restaurant import RestaurantCreate, RestaurantUpdate, RestaurantResponse
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryReorderRequest, CategoryResponse
from app.schemas.dish import DishCreate, DishUpdate, DishResponse
from app.schemas.menu import MenuResponse, MenuCategoryResponse, MenuDishResponse
from app.schemas.upload import UploadResponse, DeleteResponse
from app.schemas.analytics import AnalyticsResponse, ScansByPeriod, ScansByHour, TopUserAgent


# ── Auth Schemas ──

class TestRegisterRequest:
    def test_valid(self):
        r = RegisterRequest(email="test@example.com", password="password1")
        assert r.email == "test@example.com"

    def test_short_password(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="short1")

    def test_password_no_letter(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="12345678")

    def test_password_no_number(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="test@example.com", password="abcdefgh")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            RegisterRequest(email="not-an-email", password="password1")


class TestLoginRequest:
    def test_valid(self):
        r = LoginRequest(email="test@example.com", password="password1")
        assert r.password == "password1"

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            LoginRequest()


class TestRefreshRequest:
    def test_valid(self):
        r = RefreshRequest(refresh_token="some-token")
        assert r.refresh_token == "some-token"


class TestTokenResponse:
    def test_valid(self):
        r = TokenResponse(access_token="at", refresh_token="rt")
        assert r.token_type == "bearer"


class TestUserResponse:
    def test_valid(self):
        r = UserResponse(id=uuid.uuid4(), email="test@example.com", created_at="2025-01-01")
        assert r.email == "test@example.com"


# ── Restaurant Schemas ──

class TestRestaurantCreate:
    def test_valid(self):
        r = RestaurantCreate(name="Test Restaurant")
        assert r.name == "Test Restaurant"
        assert r.description is None

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="")

    def test_name_too_long(self):
        with pytest.raises(ValidationError):
            RestaurantCreate(name="x" * 101)

    def test_with_all_fields(self):
        r = RestaurantCreate(
            name="Test", description="Desc", logo_url="http://img.png",
            phone="555", address="123 Main", hours={"mon": "9-5"}
        )
        assert r.hours == {"mon": "9-5"}


class TestRestaurantUpdate:
    def test_partial_update(self):
        r = RestaurantUpdate(description="New desc")
        assert r.name is None
        assert r.description == "New desc"


# ── Category Schemas ──

class TestCategoryCreate:
    def test_valid(self):
        c = CategoryCreate(name="Drinks")
        assert c.active is True

    def test_empty_name(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="")


class TestCategoryUpdate:
    def test_partial(self):
        c = CategoryUpdate(active=False)
        assert c.name is None
        assert c.active is False


class TestCategoryReorder:
    def test_valid(self):
        ids = [uuid.uuid4(), uuid.uuid4()]
        r = CategoryReorderRequest(ordered_ids=ids)
        assert len(r.ordered_ids) == 2

    def test_empty_list(self):
        with pytest.raises(ValidationError):
            CategoryReorderRequest(ordered_ids=[])


# ── Dish Schemas ──

class TestDishCreate:
    def test_valid(self):
        d = DishCreate(category_id=uuid.uuid4(), name="Pizza", price=Decimal("10.00"))
        assert d.available is True
        assert d.featured is False

    def test_negative_price(self):
        with pytest.raises(ValidationError):
            DishCreate(category_id=uuid.uuid4(), name="Pizza", price=Decimal("-1.00"))

    def test_zero_price(self):
        with pytest.raises(ValidationError):
            DishCreate(category_id=uuid.uuid4(), name="Pizza", price=Decimal("0.00"))


class TestDishUpdate:
    def test_partial(self):
        d = DishUpdate(name="Updated")
        assert d.price is None
        assert d.name == "Updated"


# ── Menu Schemas ──

class TestMenuResponse:
    def test_valid(self):
        dish = MenuDishResponse(
            id=uuid.uuid4(), name="Burger", description=None,
            price=Decimal("12.00"), sale_price=None, image_url=None,
            tags=None, featured=False, position=1,
        )
        cat = MenuCategoryResponse(
            id=uuid.uuid4(), name="Main", description=None,
            position=1, dishes=[dish],
        )
        m = MenuResponse(
            restaurant_id=uuid.uuid4(), restaurant_name="Test",
            restaurant_slug="test", description=None, logo_url=None,
            phone=None, address=None, hours=None, categories=[cat],
        )
        assert m.restaurant_name == "Test"
        assert len(m.categories) == 1


# ── Upload Schemas ──

class TestUploadResponse:
    def test_valid(self):
        r = UploadResponse(
            thumbnail="http://s3/t.webp",
            medium="http://s3/m.webp",
            large="http://s3/l.webp",
        )
        assert r.thumbnail.startswith("http")


class TestDeleteResponse:
    def test_valid(self):
        r = DeleteResponse(detail="deleted")
        assert r.detail == "deleted"


# ── Analytics Schemas ──

class TestAnalyticsResponse:
    def test_valid(self):
        r = AnalyticsResponse(
            total_scans=100,
            scans_by_period=[ScansByPeriod(period="2025-01-01", count=50)],
            scans_by_hour=[ScansByHour(hour=12, count=30)],
            top_user_agents=[TopUserAgent(user_agent="Chrome", count=80)],
        )
        assert r.total_scans == 100
