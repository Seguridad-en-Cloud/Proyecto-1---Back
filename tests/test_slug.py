"""Unit tests for slug generation utilities."""
from app.utils.slug import generate_slug, make_unique_slug


class TestGenerateSlug:
    """Tests for generate_slug."""

    def test_basic_conversion(self):
        assert generate_slug("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert generate_slug("Café & Bar!") == "caf-bar"

    def test_multiple_spaces(self):
        assert generate_slug("a   b   c") == "a-b-c"

    def test_underscores_converted(self):
        assert generate_slug("my_restaurant") == "my-restaurant"

    def test_leading_trailing_hyphens_removed(self):
        assert generate_slug(" -hello- ") == "hello"

    def test_max_length(self):
        long_name = "a" * 200
        slug = generate_slug(long_name, max_length=50)
        assert len(slug) <= 50

    def test_empty_string(self):
        assert generate_slug("") == ""

    def test_numbers_preserved(self):
        assert generate_slug("Restaurant 42") == "restaurant-42"

    def test_multiple_hyphens_collapsed(self):
        assert generate_slug("a---b---c") == "a-b-c"

    def test_periods_preserved(self):
        assert generate_slug("v1.0 release") == "v1.0-release"


class TestMakeUniqueSlug:
    """Tests for make_unique_slug."""

    def test_slug_already_unique(self):
        result = make_unique_slug("my-slug", set())
        assert result == "my-slug"

    def test_slug_not_in_set(self):
        result = make_unique_slug("my-slug", {"other-slug"})
        assert result == "my-slug"

    def test_appends_number_on_collision(self):
        result = make_unique_slug("my-slug", {"my-slug"})
        assert result == "my-slug-1"

    def test_increments_number_on_multiple_collisions(self):
        existing = {"my-slug", "my-slug-1", "my-slug-2"}
        result = make_unique_slug("my-slug", existing)
        assert result == "my-slug-3"
