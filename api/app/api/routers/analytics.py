"""Analytics routes."""
from datetime import datetime

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.deps import CurrentUserId, DatabaseSession
from app.schemas.analytics import AnalyticsResponse
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/admin/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(
    user_id: CurrentUserId,
    session: DatabaseSession,
    granularity: str = Query(default="day", regex="^(day|week|month)$"),
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
):
    """Get analytics dashboard data."""
    service = AnalyticsService(session)
    return await service.get_analytics(
        owner_user_id=user_id,
        granularity=granularity,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/export")
async def export_analytics(
    user_id: CurrentUserId,
    session: DatabaseSession,
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
):
    """Export analytics data as CSV."""
    service = AnalyticsService(session)
    csv_data = await service.export_analytics(
        owner_user_id=user_id,
        from_date=from_date,
        to_date=to_date,
    )
    
    return StreamingResponse(
        iter([csv_data]),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=analytics_export.csv"
        },
    )
