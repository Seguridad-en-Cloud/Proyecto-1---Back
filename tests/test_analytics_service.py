"""Unit tests for AnalyticsService using mocked repositories."""
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.analytics_service import AnalyticsService


def _make_restaurant(owner_id=None):
    r = MagicMock()
    r.id = uuid.uuid4()
    r.owner_user_id = owner_id or uuid.uuid4()
    return r


@pytest.fixture
def service():
    session = AsyncMock()
    svc = AnalyticsService(session)
    svc.repo = AsyncMock()
    svc.restaurant_repo = AsyncMock()
    return svc


# ── get_analytics ──

@pytest.mark.asyncio
async def test_get_analytics_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.get_analytics(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_get_analytics_success(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_total_scans = AsyncMock(return_value=42)
    service.repo.get_scans_by_period = AsyncMock(return_value=[
        {"period": datetime(2025, 1, 1), "count": 10},
        {"period": datetime(2025, 1, 2), "count": 32},
    ])
    service.repo.get_scans_by_hour = AsyncMock(return_value=[
        {"hour": 12, "count": 15},
        {"hour": 18, "count": 27},
    ])
    service.repo.get_top_user_agents = AsyncMock(return_value=[
        {"user_agent": "Chrome", "count": 30},
    ])

    result = await service.get_analytics(rest.owner_user_id, granularity="day")
    assert result.total_scans == 42
    assert len(result.scans_by_period) == 2
    assert len(result.scans_by_hour) == 2
    assert len(result.top_user_agents) == 1


@pytest.mark.asyncio
async def test_get_analytics_invalid_granularity_defaults_to_day(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_total_scans = AsyncMock(return_value=0)
    service.repo.get_scans_by_period = AsyncMock(return_value=[])
    service.repo.get_scans_by_hour = AsyncMock(return_value=[])
    service.repo.get_top_user_agents = AsyncMock(return_value=[])

    result = await service.get_analytics(rest.owner_user_id, granularity="invalid")
    assert result.total_scans == 0


@pytest.mark.asyncio
async def test_get_analytics_with_date_range(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    service.repo.get_total_scans = AsyncMock(return_value=5)
    service.repo.get_scans_by_period = AsyncMock(return_value=[])
    service.repo.get_scans_by_hour = AsyncMock(return_value=[])
    service.repo.get_top_user_agents = AsyncMock(return_value=[])

    from_dt = datetime(2025, 1, 1)
    to_dt = datetime(2025, 1, 31)
    result = await service.get_analytics(rest.owner_user_id, from_date=from_dt, to_date=to_dt)
    service.repo.get_total_scans.assert_awaited_once_with(rest.id, from_dt, to_dt)


# ── export_analytics ──

@pytest.mark.asyncio
async def test_export_analytics_no_restaurant(service):
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await service.export_analytics(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_export_analytics_success(service):
    rest = _make_restaurant()
    service.restaurant_repo.get_by_owner_id = AsyncMock(return_value=rest)
    # Return list of mock scan events
    event = MagicMock()
    event.scanned_at = datetime(2025, 1, 1, 12, 0)
    event.user_agent = "Chrome"
    event.ip_hash = "abc123"
    event.referrer = "https://google.com"
    service.repo.get_scan_events_for_export = AsyncMock(return_value=[event])

    result = await service.export_analytics(rest.owner_user_id)
    assert isinstance(result, str)
    assert "timestamp" in result  # CSV header
