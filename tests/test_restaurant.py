"""Tests for restaurant endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test creating a restaurant."""
    response = await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={
            "name": "Test Restaurant",
            "description": "A test restaurant",
            "phone": "123-456-7890",
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Restaurant"
    assert data["slug"] == "test-restaurant"


@pytest.mark.asyncio
async def test_create_restaurant_duplicate(client: AsyncClient, auth_headers: dict[str, str]):
    """Test creating duplicate restaurant."""
    # Create first restaurant
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )
    
    # Try to create another
    response = await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Another Restaurant"},
    )
    
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test getting restaurant."""
    # Create restaurant
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )
    
    # Get restaurant
    response = await client.get(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Restaurant"


@pytest.mark.asyncio
async def test_update_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test updating restaurant."""
    # Create restaurant
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Original Name"},
    )
    
    # Update restaurant
    response = await client.put(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Updated Name"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["slug"] == "updated-name"


@pytest.mark.asyncio
async def test_delete_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test deleting restaurant."""
    # Create restaurant
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )
    
    # Delete restaurant
    response = await client.delete(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
    )
    
    assert response.status_code == 204
    
    # Verify it's deleted
    get_response = await client.get(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
    )
    assert get_response.status_code == 404
