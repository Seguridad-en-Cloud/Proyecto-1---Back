"""Analytics service with business logic."""
import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.restaurant_repo import RestaurantRepository
from app.schemas.analytics import AnalyticsResponse, ScansByHour, ScansByPeriod, TopUserAgent
from app.utils.csv_export import export_to_csv, scan_events_to_csv_data


class AnalyticsService:
    """Service for analytics operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = AnalyticsRepository(session)
        self.restaurant_repo = RestaurantRepository(session)
    
    async def get_analytics(
        self,
        owner_user_id: uuid.UUID,
        granularity: str = "day",
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> AnalyticsResponse:
        """Get analytics dashboard data.
        
        Args:
            owner_user_id: Owner's user ID
            granularity: Time granularity (day, week, month)
            from_date: Start date filter
            to_date: End date filter
            
        Returns:
            Analytics response with dashboard data
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        # Validate granularity
        if granularity not in ("day", "week", "month"):
            granularity = "day"
        
        # Get total scans
        total_scans = await self.repo.get_total_scans(
            restaurant.id, from_date, to_date
        )
        
        # Get scans by period
        scans_by_period_data = await self.repo.get_scans_by_period(
            restaurant.id, granularity, from_date, to_date
        )
        scans_by_period = [
            ScansByPeriod(
                period=item["period"].isoformat() if item["period"] else "",
                count=item["count"]
            )
            for item in scans_by_period_data
        ]
        
        # Get scans by hour
        scans_by_hour_data = await self.repo.get_scans_by_hour(
            restaurant.id, from_date, to_date
        )
        scans_by_hour = [
            ScansByHour(hour=item["hour"], count=item["count"])
            for item in scans_by_hour_data
        ]
        
        # Get top user agents
        top_user_agents_data = await self.repo.get_top_user_agents(
            restaurant.id, limit=5, from_date=from_date, to_date=to_date
        )
        top_user_agents = [
            TopUserAgent(user_agent=item["user_agent"], count=item["count"])
            for item in top_user_agents_data
        ]
        
        return AnalyticsResponse(
            total_scans=total_scans,
            scans_by_period=scans_by_period,
            scans_by_hour=scans_by_hour,
            top_user_agents=top_user_agents,
        )
    
    async def export_analytics(
        self,
        owner_user_id: uuid.UUID,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
    ) -> str:
        """Export analytics data as CSV.
        
        Args:
            owner_user_id: Owner's user ID
            from_date: Start date filter
            to_date: End date filter
            
        Returns:
            CSV formatted string
            
        Raises:
            HTTPException: If restaurant not found
        """
        restaurant = await self.restaurant_repo.get_by_owner_id(owner_user_id)
        
        if not restaurant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Restaurant not found",
            )
        
        # Get scan events
        scan_events = await self.repo.get_scan_events_for_export(
            restaurant.id, from_date, to_date
        )
        
        # Convert to CSV data
        csv_data = scan_events_to_csv_data(scan_events)
        
        # Export to CSV
        columns = ["timestamp", "user_agent", "ip_hash", "referrer"]
        return export_to_csv(csv_data, columns)
