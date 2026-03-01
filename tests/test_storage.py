"""Unit tests for S3 storage client."""
import uuid
from unittest.mock import MagicMock, patch

from app.core.storage import (
    delete_file_from_s3,
    generate_object_key,
    upload_file_to_s3,
    _ensure_bucket_exists,
)


class TestGenerateObjectKey:
    """Tests for generate_object_key."""

    def test_returns_string_with_prefix(self):
        key = generate_object_key("dishes/thumbnail", "photo.jpg")
        assert key.startswith("dishes/thumbnail/")

    def test_preserves_extension(self):
        key = generate_object_key("logos", "logo.png")
        assert key.endswith(".png")

    def test_unique_per_call(self):
        k1 = generate_object_key("dishes", "photo.jpg")
        k2 = generate_object_key("dishes", "photo.jpg")
        assert k1 != k2

    def test_defaults_to_webp(self):
        key = generate_object_key("dishes", "noext")
        assert key.endswith(".webp")

    def test_key_format(self):
        key = generate_object_key("x", "test.jpg")
        parts = key.split("/")
        assert len(parts) == 2
        assert parts[0] == "x"


class TestUploadFileToS3:
    """Tests for upload_file_to_s3 with mocked client."""

    @patch("app.core.storage.get_s3_client")
    def test_calls_put_object(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        url = upload_file_to_s3(b"data", "test/key.webp", "image/webp")

        mock_client.put_object.assert_called_once()
        assert "test/key.webp" in url

    @patch("app.core.storage.get_s3_client")
    def test_returns_public_url(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        url = upload_file_to_s3(b"data", "imgs/abc.webp", "image/webp")
        assert url.endswith("imgs/abc.webp")


class TestDeleteFileFromS3:
    """Tests for delete_file_from_s3 with mocked client."""

    @patch("app.core.storage.get_s3_client")
    def test_calls_delete_object(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        delete_file_from_s3("test/key.webp")

        mock_client.delete_object.assert_called_once()


class TestEnsureBucketExists:
    """Tests for _ensure_bucket_exists."""

    def test_bucket_already_exists(self):
        mock_client = MagicMock()
        # head_bucket succeeds → bucket exists
        mock_client.head_bucket.return_value = {}
        _ensure_bucket_exists(mock_client)
        mock_client.create_bucket.assert_not_called()

    def test_creates_bucket_when_missing(self):
        from botocore.exceptions import ClientError

        mock_client = MagicMock()
        mock_client.head_bucket.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
        )
        _ensure_bucket_exists(mock_client)
        mock_client.create_bucket.assert_called_once()
        mock_client.put_bucket_policy.assert_called_once()
