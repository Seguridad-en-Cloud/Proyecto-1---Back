"""Unit tests for password hashing utilities."""
from app.core.security.passwords import hash_password, verify_password


class TestHashPassword:
    """Tests for hash_password."""

    def test_returns_string(self):
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_hash_differs_from_plaintext(self):
        plain = "mypassword"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_different_calls_produce_different_hashes(self):
        """Bcrypt uses random salt, so same input → different hash."""
        h1 = hash_password("samepass")
        h2 = hash_password("samepass")
        assert h1 != h2


class TestVerifyPassword:
    """Tests for verify_password."""

    def test_correct_password_returns_true(self):
        hashed = hash_password("correct")
        assert verify_password("correct", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_empty_password(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True
        assert verify_password("notempty", hashed) is False
