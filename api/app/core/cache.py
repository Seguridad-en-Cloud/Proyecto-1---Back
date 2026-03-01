"""Simple in-memory cache for public menu data."""
import time
from typing import Any

_cache: dict[str, tuple[Any, float]] = {}

# Default TTL in seconds (5 minutes)
DEFAULT_TTL = 300


def cache_get(key: str) -> Any | None:
    """Get a value from cache if it exists and hasn't expired.

    Args:
        key: Cache key.

    Returns:
        Cached value or None if missing/expired.
    """
    entry = _cache.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.time() > expires_at:
        _cache.pop(key, None)
        return None
    return value


def cache_set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Store a value in cache with a TTL.

    Args:
        key: Cache key.
        value: Value to store.
        ttl: Time-to-live in seconds.
    """
    _cache[key] = (value, time.time() + ttl)


def cache_invalidate(key: str) -> None:
    """Remove a specific key from cache.

    Args:
        key: Cache key to remove.
    """
    _cache.pop(key, None)


def cache_invalidate_prefix(prefix: str) -> None:
    """Remove all cache entries matching a prefix.

    Args:
        prefix: Key prefix to match.
    """
    keys_to_delete = [k for k in _cache if k.startswith(prefix)]
    for k in keys_to_delete:
        _cache.pop(k, None)


def cache_clear() -> None:
    """Clear entire cache."""
    _cache.clear()
