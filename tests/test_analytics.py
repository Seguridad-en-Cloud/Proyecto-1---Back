"""Tests for analytics endpoints."""
import pytest
from httpx import AsyncClient


@pytest.fixture
async def restaurant_created(client: AsyncClient, auth_headers: dict[str, str]):
    """Create restaurant before tests."""
    await client.post(
        "/api/v1/admin/restaurant",
        headers=auth_headers,
        json={"name": "Test Restaurant"},
    )


@pytest.mark.asyncio
async def test_get_analytics(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test getting analytics dashboard."""
    response = await client.get(
        "/api/v1/admin/analytics",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "total_scans" in data
    assert "scans_by_period" in data
    assert "scans_by_hour" in data
    assert "top_user_agents" in data
    assert data["total_scans"] == 0  # No scans yet


@pytest.mark.asyncio
async def test_export_analytics(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test exporting analytics as CSV."""
    response = await client.get(
        "/api/v1/admin/analytics/export",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    
    # Should have CSV headers even with no data
    content = response.text
    assert "timestamp" in content
    assert "user_agent" in content
