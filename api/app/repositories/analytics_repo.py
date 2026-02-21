"""Analytics repository for database operations."""
import uuid
from datetime import datetime

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_event import ScanEvent


class AnalyticsRepository:
    """Repository for Analytics database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_total_scans(
        self, 
        restaurant_id: uuid.UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> int:
        """Get total number of scans for a restaurant."""
        query = select(func.count(ScanEvent.id)).where(
            ScanEvent.restaurant_id == restaurant_id
        )
        
        if from_date:
            query = query.where(ScanEvent.timestamp >= from_date)
        if to_date:
            query = query.where(ScanEvent.timestamp <= to_date)
        
        result = await self.session.execute(query)
        return result.scalar_one()
    
    async def get_scans_by_period(
        self,
        restaurant_id: uuid.UUID,
        granularity: str = "day",
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict]:
        """Get scans grouped by time period (day, week, month)."""
        # Base query
        query = select(
            func.date_trunc(granularity, ScanEvent.timestamp).label("period"),
            func.count(ScanEvent.id).label("count"),
        ).where(ScanEvent.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(ScanEvent.timestamp >= from_date)
        if to_date:
            query = query.where(ScanEvent.timestamp <= to_date)
        
        query = query.group_by("period").order_by("period")
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [{"period": row.period, "count": row.count} for row in rows]
    
    async def get_scans_by_hour(
        self,
        restaurant_id: uuid.UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict]:
        """Get scans grouped by hour of day (0-23)."""
        query = select(
            extract("hour", ScanEvent.timestamp).label("hour"),
            func.count(ScanEvent.id).label("count"),
        ).where(ScanEvent.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(ScanEvent.timestamp >= from_date)
        if to_date:
            query = query.where(ScanEvent.timestamp <= to_date)
        
        query = query.group_by("hour").order_by("hour")
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [{"hour": int(row.hour), "count": row.count} for row in rows]
    
    async def get_top_user_agents(
        self,
        restaurant_id: uuid.UUID,
        limit: int = 5,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[dict]:
        """Get top user agents by scan count."""
        query = select(
            ScanEvent.user_agent,
            func.count(ScanEvent.id).label("count"),
        ).where(ScanEvent.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(ScanEvent.timestamp >= from_date)
        if to_date:
            query = query.where(ScanEvent.timestamp <= to_date)
        
        query = query.group_by(ScanEvent.user_agent)
        query = query.order_by(func.count(ScanEvent.id).desc())
        query = query.limit(limit)
        
        result = await self.session.execute(query)
        rows = result.all()
        
        return [{"user_agent": row.user_agent, "count": row.count} for row in rows]
    
    async def get_scan_events_for_export(
        self,
        restaurant_id: uuid.UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> list[ScanEvent]:
        """Get all scan events for CSV export."""
        query = select(ScanEvent).where(ScanEvent.restaurant_id == restaurant_id)
        
        if from_date:
            query = query.where(ScanEvent.timestamp >= from_date)
        if to_date:
            query = query.where(ScanEvent.timestamp <= to_date)
        
        query = query.order_by(ScanEvent.timestamp.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
