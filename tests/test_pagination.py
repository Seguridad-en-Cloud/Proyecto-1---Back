"""Unit tests for pagination utility."""
from app.utils.pagination import PaginatedResponse


class TestPaginatedResponse:
    """Tests for PaginatedResponse properties."""

    def test_has_more_true(self):
        p = PaginatedResponse(items=["a", "b"], total=10, limit=2, offset=0)
        assert p.has_more is True

    def test_has_more_false(self):
        p = PaginatedResponse(items=["a"], total=3, limit=2, offset=2)
        assert p.has_more is False

    def test_page_first(self):
        p = PaginatedResponse(items=[], total=50, limit=10, offset=0)
        assert p.page == 1

    def test_page_second(self):
        p = PaginatedResponse(items=[], total=50, limit=10, offset=10)
        assert p.page == 2

    def test_page_limit_zero(self):
        p = PaginatedResponse(items=[], total=5, limit=0, offset=0)
        assert p.page == 1

    def test_total_pages(self):
        p = PaginatedResponse(items=[], total=25, limit=10, offset=0)
        assert p.total_pages == 3

    def test_total_pages_exact_division(self):
        p = PaginatedResponse(items=[], total=20, limit=10, offset=0)
        assert p.total_pages == 2

    def test_total_pages_limit_zero(self):
        p = PaginatedResponse(items=[], total=5, limit=0, offset=0)
        assert p.total_pages == 1
