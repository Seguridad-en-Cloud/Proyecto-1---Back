"""Unit tests for in-memory cache."""
import time

from app.core.cache import (
    cache_clear,
    cache_get,
    cache_invalidate,
    cache_invalidate_prefix,
    cache_set,
)


class TestCacheGetSet:
    """Tests for cache_get and cache_set."""

    def setup_method(self):
        cache_clear()

    def test_set_and_get(self):
        cache_set("key1", "value1")
        assert cache_get("key1") == "value1"

    def test_get_missing_key(self):
        assert cache_get("nonexistent") is None

    def test_stores_complex_objects(self):
        data = {"name": "test", "items": [1, 2, 3]}
        cache_set("complex", data)
        assert cache_get("complex") == data

    def test_expired_entry_returns_none(self):
        cache_set("short", "val", ttl=0)
        time.sleep(0.01)
        assert cache_get("short") is None

    def test_custom_ttl(self):
        cache_set("long", "val", ttl=3600)
        assert cache_get("long") == "val"


class TestCacheInvalidate:
    """Tests for cache_invalidate."""

    def setup_method(self):
        cache_clear()

    def test_invalidate_existing_key(self):
        cache_set("k1", "v1")
        cache_invalidate("k1")
        assert cache_get("k1") is None

    def test_invalidate_nonexistent_key_no_error(self):
        cache_invalidate("nope")  # Should not raise


class TestCacheInvalidatePrefix:
    """Tests for cache_invalidate_prefix."""

    def setup_method(self):
        cache_clear()

    def test_invalidates_matching_keys(self):
        cache_set("menu:slug1", "a")
        cache_set("menu:slug2", "b")
        cache_set("other:key", "c")
        cache_invalidate_prefix("menu:")
        assert cache_get("menu:slug1") is None
        assert cache_get("menu:slug2") is None
        assert cache_get("other:key") == "c"

    def test_no_match_does_nothing(self):
        cache_set("abc", "val")
        cache_invalidate_prefix("xyz:")
        assert cache_get("abc") == "val"


class TestCacheClear:
    """Tests for cache_clear."""

    def test_clears_all_entries(self):
        cache_set("a", 1)
        cache_set("b", 2)
        cache_clear()
        assert cache_get("a") is None
        assert cache_get("b") is None
