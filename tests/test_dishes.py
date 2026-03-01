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


@pytest.mark.asyncio
async def test_create_dish_no_category(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test creating a dish without a valid restaurant."""
    import uuid

    response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": str(uuid.uuid4()),
            "name": "Orphan Dish",
            "price": "10.00",
        },
    )
    assert response.status_code in (404, 403)


@pytest.mark.asyncio
async def test_get_nonexistent_dish(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test getting a dish that does not exist."""
    import uuid

    fake_id = str(uuid.uuid4())
    response = await client.get(
        f"/api/v1/admin/dishes/{fake_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_dishes_with_filter(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test filtering dishes by availability."""
    # Create available dish
    await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Available Dish",
            "price": "10.00",
            "available": True,
        },
    )
    # Create unavailable dish
    await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Unavailable Dish",
            "price": "10.00",
            "available": False,
        },
    )

    response = await client.get(
        "/api/v1/admin/dishes?available=true",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["available"] is True


@pytest.mark.asyncio
async def test_create_dish_with_all_fields(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test creating a dish with all optional fields."""
    response = await client.post(
        "/api/v1/admin/dishes",
        headers=auth_headers,
        json={
            "category_id": category_created,
            "name": "Full Dish",
            "description": "A complete dish entry",
            "price": "25.99",
            "sale_price": "19.99",
            "available": True,
            "featured": True,
            "tags": ["spicy", "vegan"],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["featured"] is True
    assert "spicy" in data["tags"]
    assert float(data["sale_price"]) == 19.99


@pytest.mark.asyncio
async def test_list_dishes_pagination(
    client: AsyncClient, auth_headers: dict[str, str], category_created
):
    """Test dish listing pagination."""
    # Create 3 dishes
    for i in range(3):
        await client.post(
            "/api/v1/admin/dishes",
            headers=auth_headers,
            json={
                "category_id": category_created,
                "name": f"Dish {i}",
                "price": "10.00",
            },
        )

    response = await client.get(
        "/api/v1/admin/dishes?limit=2&offset=0",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0
