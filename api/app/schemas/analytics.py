"""Analytics schemas."""
from pydantic import BaseModel


class ScansByPeriod(BaseModel):
    """Scans grouped by time period."""
    
    period: str
    count: int


class ScansByHour(BaseModel):
    """Scans grouped by hour of day."""
    
    hour: int
    count: int


class TopUserAgent(BaseModel):
    """Top user agent by scan count."""
    
    user_agent: str
    count: int


class AnalyticsResponse(BaseModel):
    """Analytics dashboard response."""
    
    total_scans: int
    scans_by_period: list[ScansByPeriod]
    scans_by_hour: list[ScansByHour]
    top_user_agents: list[TopUserAgent]
