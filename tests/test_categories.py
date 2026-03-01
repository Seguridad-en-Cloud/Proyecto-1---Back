"""Tests for category endpoints."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def restaurant_created(client: AsyncClient, auth_headers: dict[str, str]):
    """Create a restaurant before tests."""
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )


@pytest.mark.asyncio
async def test_create_category(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test creating a category."""
    response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={
            "name": "Appetizers",
            "description": "Starter dishes",
            "active": True,
        },
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Appetizers"
    assert data["position"] == 0


@pytest.mark.asyncio
async def test_list_categories(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test listing categories."""
    # Create categories
    await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Category 1"},
    )
    await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Category 2"},
    )
    
    # List categories
    response = await client.get(
        "/api/v1/admin/categories",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_category(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test updating a category."""
    # Create category
    create_response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Original"},
    )
    category_id = create_response.json()["id"]
    
    # Update category
    response = await client.put(
        f"/api/v1/admin/categories/{category_id}",
        headers=auth_headers,
        json={"name": "Updated"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"


@pytest.mark.asyncio
async def test_delete_category(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test deleting a category."""
    # Create category
    create_response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "To Delete"},
    )
    category_id = create_response.json()["id"]
    
    # Delete category
    response = await client.delete(
        f"/api/v1/admin/categories/{category_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_reorder_categories(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test reordering categories."""
    # Create categories
    cat1_response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Category 1"},
    )
    cat2_response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Category 2"},
    )
    
    cat1_id = cat1_response.json()["id"]
    cat2_id = cat2_response.json()["id"]
    
    # Reorder
    response = await client.patch(
        "/api/v1/admin/categories/reorder",
        headers=auth_headers,
        json={"ordered_ids": [cat2_id, cat1_id]},
    )
    
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_create_category_no_restaurant(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test creating a category without a restaurant returns 404."""
    response = await client.post(
        "/api/v1/admin/categories",
        headers=auth_headers,
        json={"name": "Orphan Category"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_nonexistent_category(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test updating a category that does not exist."""
    import uuid

    fake_id = str(uuid.uuid4())
    response = await client.put(
        f"/api/v1/admin/categories/{fake_id}",
        headers=auth_headers,
        json={"name": "Ghost"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_category(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test deleting a category that does not exist."""
    import uuid

    fake_id = str(uuid.uuid4())
    response = await client.delete(
        f"/api/v1/admin/categories/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_categories_empty(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test listing categories when none exist."""
    response = await client.get(
        "/api/v1/admin/categories",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []
