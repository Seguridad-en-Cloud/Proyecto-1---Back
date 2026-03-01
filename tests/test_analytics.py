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


@pytest.mark.asyncio
async def test_analytics_requires_auth(client: AsyncClient):
    """Test that analytics requires authentication."""
    response = await client.get("/api/v1/admin/analytics")
    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_analytics_no_restaurant(client: AsyncClient, auth_headers: dict[str, str]):
    """Test analytics without a restaurant returns 404."""
    response = await client.get(
        "/api/v1/admin/analytics",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_analytics_with_granularity(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test analytics with different granularity values."""
    for granularity in ("day", "week", "month"):
        response = await client.get(
            f"/api/v1/admin/analytics?granularity={granularity}",
            headers=auth_headers,
        )
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_analytics_with_date_range(
    client: AsyncClient, auth_headers: dict[str, str], restaurant_created
):
    """Test analytics with from/to date parameters."""
    response = await client.get(
        "/api/v1/admin/analytics?from=2025-01-01T00:00:00&to=2026-12-31T23:59:59",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_scans"] == 0


@pytest.mark.asyncio
async def test_export_analytics_no_restaurant(
    client: AsyncClient, auth_headers: dict[str, str]
):
    """Test export analytics without restaurant."""
    response = await client.get(
        "/api/v1/admin/analytics/export",
        headers=auth_headers,
    )
    assert response.status_code == 404
