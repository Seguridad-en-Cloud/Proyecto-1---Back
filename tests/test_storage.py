"""Unit tests for the object-storage abstraction.

The storage module now exposes a ``StorageBackend`` interface with two
implementations (``S3Storage`` for MinIO/S3, ``GCSStorage`` for Google Cloud
Storage). Module-level helpers (``upload_file_to_s3``, ``delete_file_from_s3``)
are kept for backwards compatibility and now delegate to the active backend.
"""
from unittest.mock import MagicMock, patch

import app.core.storage as storage_module
from app.core.storage import (
    delete_file_from_s3,
    generate_object_key,
    get_public_prefix,
    upload_file_to_s3,
)


class TestGenerateObjectKey:
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


class TestModuleHelpers:
    """Module-level helpers should delegate to the active backend."""

    def setup_method(self):
        # Reset the singleton between tests so each test installs its own mock.
        storage_module._backend = None

    def teardown_method(self):
        storage_module._backend = None

    def test_upload_delegates_to_backend(self):
        backend = MagicMock()
        backend.upload.return_value = "http://example/test/key.webp"
        with patch("app.core.storage.get_storage", return_value=backend):
            url = upload_file_to_s3(b"data", "test/key.webp", "image/webp")
        backend.upload.assert_called_once_with(b"data", "test/key.webp", "image/webp")
        assert url == "http://example/test/key.webp"

    def test_delete_delegates_to_backend(self):
        backend = MagicMock()
        with patch("app.core.storage.get_storage", return_value=backend):
            delete_file_from_s3("test/key.webp")
        backend.delete.assert_called_once_with("test/key.webp")

    def test_public_prefix_delegates(self):
        backend = MagicMock()
        backend.public_prefix.return_value = "http://cdn/livemenu"
        with patch("app.core.storage.get_storage", return_value=backend):
            assert get_public_prefix() == "http://cdn/livemenu"


class TestS3StorageEnsureBucket:
    """Verify the S3 backend creates the bucket + sets a policy on first use."""

    def test_bucket_already_exists_does_not_recreate(self):
        from app.core.storage import S3Storage

        with patch("boto3.client") as mock_boto:
            client = MagicMock()
            client.head_bucket.return_value = {}
            mock_boto.return_value = client

            S3Storage()

            client.create_bucket.assert_not_called()

    def test_creates_bucket_when_missing(self):
        from botocore.exceptions import ClientError

        from app.core.storage import S3Storage

        with patch("boto3.client") as mock_boto:
            client = MagicMock()
            client.head_bucket.side_effect = ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadBucket"
            )
            mock_boto.return_value = client

            S3Storage()

            client.create_bucket.assert_called_once()
            client.put_bucket_policy.assert_called_once()
