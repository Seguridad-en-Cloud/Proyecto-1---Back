"""Datetime utility functions."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware).
    
    Replacement for deprecated datetime.utcnow().
    """
    return datetime.now(timezone.utc)
