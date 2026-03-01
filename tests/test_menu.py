"""Tests for public menu endpoints."""
import pytest
from httpx import AsyncClient

from app.core.cache import cache_clear


@pytest.fixture
async def menu_setup(client: AsyncClient, auth_headers: dict[str, str]):
    """Create restaurant, category, and dish for menu tests."""
    cache_clear()

    # Create restaurant
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Menu Test Restaurant", "description": "A great place"},
    )

    # Create category
    cat_resp = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Entrées", "description": "Main courses"},
    )
    cat_id = cat_resp.json()["id"]

    # Create dish
    await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": cat_id,
            "name": "Pasta Carbonara",
            "description": "Classic Italian",
            "price": "14.50",
            "available": True,
            "featured": True,
        },
    )

    return "menu-test-restaurant"  # expected slug


@pytest.mark.asyncio
async def test_menu_json_endpoint(client: AsyncClient, menu_setup: str):
    """Test GET /api/v1/menu/{slug} returns JSON menu."""
    slug = menu_setup
    response = await client.get(f"/api/v1/menu/{slug}")

    assert response.status_code == 200
    data = response.json()
    assert data["restaurant_name"] == "Menu Test Restaurant"
    assert data["restaurant_slug"] == slug
    assert len(data["categories"]) == 1
    assert data["categories"][0]["name"] == "Entrées"
    assert len(data["categories"][0]["dishes"]) == 1
    assert data["categories"][0]["dishes"][0]["name"] == "Pasta Carbonara"


@pytest.mark.asyncio
async def test_menu_html_endpoint(client: AsyncClient, menu_setup: str):
    """Test GET /m/{slug} returns HTML page."""
    slug = menu_setup
    response = await client.get(f"/m/{slug}")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Menu Test Restaurant" in response.text
    assert "Pasta Carbonara" in response.text


@pytest.mark.asyncio
async def test_menu_json_not_found(client: AsyncClient):
    """Test GET /api/v1/menu/{slug} with nonexistent slug."""
    response = await client.get("/api/v1/menu/nonexistent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_menu_html_not_found(client: AsyncClient):
    """Test GET /m/{slug} with nonexistent slug."""
    response = await client.get("/m/nonexistent-slug")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_menu_hides_unavailable_dishes(
    client: AsyncClient, auth_headers: dict[str, str], menu_setup: str
):
    """Unavailable dishes should not appear in public menu."""
    slug = menu_setup

    # Get current dishes
    dishes_resp = await client.get("/api/v1/admin/dishes", headers=auth_headers)
    dish_id = dishes_resp.json()["items"][0]["id"]

    # Toggle availability (make unavailable)
    await client.patch(
        f"/api/v1/admin/dishes/{dish_id}/availability",
        headers=auth_headers,
    )

    # Clear cache so we get fresh data
    cache_clear()

    # Check public menu
    response = await client.get(f"/api/v1/menu/{slug}")
    assert response.status_code == 200
    data = response.json()
    # Category with no available dishes should not appear
    assert len(data["categories"]) == 0


@pytest.mark.asyncio
async def test_menu_cache_works(client: AsyncClient, menu_setup: str):
    """Second request should be served from cache."""
    slug = menu_setup
    cache_clear()

    # First request — populates cache
    resp1 = await client.get(f"/api/v1/menu/{slug}")
    assert resp1.status_code == 200

    # Second request — served from cache
    resp2 = await client.get(f"/api/v1/menu/{slug}")
    assert resp2.status_code == 200
    assert resp1.json() == resp2.json()


@pytest.mark.asyncio
async def test_menu_hides_inactive_category(
    client: AsyncClient, auth_headers: dict[str, str], menu_setup: str
):
    """Inactive categories should not appear in menu."""
    slug = menu_setup
    cache_clear()

    # Get categories
    cats_resp = await client.get("/api/v1/admin/categories", headers=auth_headers)
    cat_id = cats_resp.json()[0]["id"]

    # Deactivate category
    await client.put(
        f"/api/v1/admin/categories/{cat_id}",
        headers=auth_headers,
        json={"active": False},
    )
    cache_clear()

    response = await client.get(f"/api/v1/menu/{slug}")
    assert response.status_code == 200
    assert len(response.json()["categories"]) == 0
