"""S3/MinIO storage client."""
import logging
import uuid

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Lazy-initialized client
_s3_client = None


def get_s3_client():
    """Get or create the S3 client (lazy singleton)."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        _ensure_bucket_exists(_s3_client)
    return _s3_client


def _ensure_bucket_exists(client) -> None:
    """Create the bucket if it doesn't exist and set public-read policy."""
    try:
        client.head_bucket(Bucket=settings.s3_bucket)
    except ClientError:
        client.create_bucket(Bucket=settings.s3_bucket)
        # Set bucket policy so objects are publicly readable
        import json

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{settings.s3_bucket}/*",
                }
            ],
        }
        client.put_bucket_policy(
            Bucket=settings.s3_bucket,
            Policy=json.dumps(policy),
        )
        logger.info("Created S3 bucket: %s", settings.s3_bucket)


def upload_file_to_s3(file_bytes: bytes, key: str, content_type: str) -> str:
    """Upload a file to S3 and return its public URL.

    Args:
        file_bytes: Raw file content.
        key: Object key (path) in the bucket.
        content_type: MIME type.

    Returns:
        Public URL of the uploaded object.
    """
    client = get_s3_client()
    client.put_object(
        Bucket=settings.s3_bucket,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"{settings.s3_public_url}/{key}"


def delete_file_from_s3(key: str) -> None:
    """Delete a file from S3.

    Args:
        key: Object key to delete.
    """
    client = get_s3_client()
    client.delete_object(Bucket=settings.s3_bucket, Key=key)


def generate_object_key(prefix: str, filename: str) -> str:
    """Generate a unique object key.

    Args:
        prefix: Folder prefix (e.g. 'logos', 'dishes').
        filename: Original filename.

    Returns:
        Unique key like 'dishes/abc123-original.webp'
    """
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "webp"
    unique = uuid.uuid4().hex[:12]
    return f"{prefix}/{unique}.{ext}"
