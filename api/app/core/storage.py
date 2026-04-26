"""Object storage abstraction.

Two backends:

* :class:`S3Storage`  – boto3 against S3 / MinIO. Used for local dev.
* :class:`GCSStorage` – Google Cloud Storage. Used in production.

The backend is selected by ``settings.storage_backend``.

Public URLs are normalized so that the frontend can derive the object key by
stripping the bucket-prefix returned in :pyfunc:`StorageBackend.public_prefix`.
The frontend uses that prefix to compute the key for delete operations.
"""
from __future__ import annotations

import logging
import uuid
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Common interface for the object-storage backends."""

    @abstractmethod
    def upload(self, file_bytes: bytes, key: str, content_type: str) -> str:
        """Upload bytes and return the object's public URL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete an object by its key."""

    @abstractmethod
    def public_prefix(self) -> str:
        """Return the URL prefix that comes before the object key.

        For S3/MinIO this is e.g. ``http://localhost:9000/livemenu``; for GCS
        it is ``https://storage.googleapis.com/<bucket>`` (or the configured
        custom domain). Used by the frontend to extract object keys.
        """


# ── S3 / MinIO ────────────────────────────────────────────────────────────


class S3Storage(StorageBackend):
    """boto3-based backend. Targets MinIO in local dev or AWS S3."""

    def __init__(self) -> None:
        import boto3
        from botocore.config import Config

        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        from botocore.exceptions import ClientError
        try:
            self._client.head_bucket(Bucket=settings.s3_bucket)
        except ClientError:
            import json
            self._client.create_bucket(Bucket=settings.s3_bucket)
            policy = {
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{settings.s3_bucket}/*",
                }],
            }
            self._client.put_bucket_policy(
                Bucket=settings.s3_bucket, Policy=json.dumps(policy)
            )
            logger.info("Created S3 bucket %s", settings.s3_bucket)

    def upload(self, file_bytes: bytes, key: str, content_type: str) -> str:
        self._client.put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=file_bytes,
            ContentType=content_type,
        )
        return f"{self.public_prefix()}/{key}"

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=settings.s3_bucket, Key=key)

    def public_prefix(self) -> str:
        return settings.s3_public_url.rstrip("/")


# ── Google Cloud Storage ──────────────────────────────────────────────────


class GCSStorage(StorageBackend):
    """google-cloud-storage backend with versioned, IAM-controlled bucket.

    The bucket is expected to be pre-provisioned by Terraform with:
      * uniform_bucket_level_access = true
      * versioning enabled
      * CMEK or Google-managed encryption at rest
      * IAM granting ``roles/storage.objectAdmin`` only to the backend SA
      * (optional) ``allUsers`` with ``roles/storage.objectViewer`` if the
        bucket is meant to serve images publicly via CDN.
    """

    def __init__(self) -> None:
        from google.cloud import storage  # type: ignore

        if not settings.gcs_bucket:
            raise RuntimeError(
                "STORAGE_BACKEND=gcs but GCS_BUCKET is not configured"
            )

        self._client = storage.Client(project=settings.gcp_project_id)
        self._bucket = self._client.bucket(settings.gcs_bucket)

    def upload(self, file_bytes: bytes, key: str, content_type: str) -> str:
        blob = self._bucket.blob(key)
        # cache_control is sent on upload only; objects keep this metadata.
        blob.cache_control = "public, max-age=86400"
        blob.upload_from_string(file_bytes, content_type=content_type)
        return f"{self.public_prefix()}/{key}"

    def delete(self, key: str) -> None:
        try:
            self._bucket.blob(key).delete()
        except Exception as exc:
            # Object may already have been removed; let callers decide.
            logger.warning("GCS delete failed for %s: %s", key, exc)
            raise

    def public_prefix(self) -> str:
        if settings.gcs_public_url:
            return settings.gcs_public_url.rstrip("/")
        return f"https://storage.googleapis.com/{settings.gcs_bucket}"


# ── Factory ───────────────────────────────────────────────────────────────


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the singleton backend selected by configuration."""
    global _backend
    if _backend is None:
        if settings.storage_backend == "gcs":
            _backend = GCSStorage()
        else:
            _backend = S3Storage()
        logger.info(
            "Initialised storage backend: %s", settings.storage_backend
        )
    return _backend


# ── Helpers (preserve previous public API) ────────────────────────────────


def upload_file_to_s3(file_bytes: bytes, key: str, content_type: str) -> str:
    """Upload bytes; returned URL points at the active storage backend.

    Function name is kept for backwards compatibility with the worker pool;
    it now delegates to the configured backend (S3 *or* GCS).
    """
    return get_storage().upload(file_bytes, key, content_type)


def delete_file_from_s3(key: str) -> None:
    """Delete an object by key on the active storage backend."""
    get_storage().delete(key)


def get_public_prefix() -> str:
    """Return the URL prefix that precedes the object key."""
    return get_storage().public_prefix()


def generate_object_key(prefix: str, filename: str) -> str:
    """Generate a unique object key, e.g. ``dishes/abc123.webp``."""
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "webp"
    unique = uuid.uuid4().hex[:12]
    return f"{prefix}/{unique}.{ext}"
