"""Tests for dish endpoints."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def category_created(client: AsyncClient, auth_headers: dict[str, str]):
    """Create restaurant and category before tests."""
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )
    
    response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Main Dishes"},
    )
    
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_dish(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test creating a dish."""
    response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Burger",
            "description": "Delicious burger",
            "price": "12.99",
            "available": True,
            "featured": False,
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Burger"
    assert float(data["price"]) == 12.99


@pytest.mark.asyncio
async def test_list_dishes(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test listing dishes."""
    # Create dishes
    await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Dish 1",
            "price": "10.00",
        },
    )
    
    # List dishes
    response = await client.get(
        "/api/v1/admin/dishes",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_dish(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test getting a single dish."""
    # Create dish
    create_response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Test Dish",
            "price": "15.00",
        },
    )
    dish_id = create_response.json()["id"]
    
    # Get dish
    response = await client.get(
        f"/api/v1/admin/dishes/{dish_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Dish"


@pytest.mark.asyncio
async def test_update_dish(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test updating a dish."""
    # Create dish
    create_response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Original",
            "price": "10.00",
        },
    )
    dish_id = create_response.json()["id"]
    
    # Update dish
    response = await client.put(
        f"/api/v1/admin/dishes/{dish_id}",
        headers=auth_headers,
        json={"name": "Updated", "price": "12.00"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_dish(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test soft deleting a dish."""
    # Create dish
    create_response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "To Delete",
            "price": "10.00",
        },
    )
    dish_id = create_response.json()["id"]
    
    # Delete dish
    response = await client.delete(
        f"/api/v1/admin/dishes/{dish_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["deleted_at"] is not None


@pytest.mark.asyncio
async def test_toggle_availability(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test toggling dish availability."""
    # Create dish
    create_response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Test",
            "price": "10.00",
            "available": True,
        },
    )
    dish_id = create_response.json()["id"]
    
    # Toggle availability
    response = await client.patch(
        f"/api/v1/admin/dishes/{dish_id}/availability",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["available"] is False
