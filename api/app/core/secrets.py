"""Secret resolution layer.

Reads sensitive values from Google Secret Manager when running on GCP, and
falls back to environment variables for local/dev environments.

Selection rules:
- If ``GCP_PROJECT_ID`` is set, the loader fetches each requested name from
  Secret Manager (``projects/<id>/secrets/<name>/versions/latest``).
- Otherwise, the value is read from ``os.environ`` directly.

This indirection lets the same code run locally with a ``.env`` file and in
production with zero ``.env`` files (Entrega 2 §3.2).
"""
from __future__ import annotations

import logging
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


def _gcp_project_id() -> str | None:
    """Return the configured GCP project, or ``None`` when not on GCP."""
    return os.getenv("GCP_PROJECT_ID") or None


@lru_cache(maxsize=128)
def _fetch_from_secret_manager(secret_name: str, project_id: str) -> str | None:
    """Fetch ``secret_name`` from GCP Secret Manager.

    Cached so that repeated lookups during a single process lifetime do not
    hammer the Secret Manager API. When the secret rotates, the Cloud Run
    revision is replaced (or restarted), which invalidates this cache.
    """
    try:
        from google.cloud import secretmanager
    except ImportError:
        logger.warning(
            "google-cloud-secret-manager not installed; cannot fetch %s",
            secret_name,
        )
        return None

    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("utf-8")
    except Exception as exc:
        logger.error("Failed to read secret %s: %s", secret_name, exc)
        return None


def get_secret(name: str, default: str | None = None) -> str | None:
    """Resolve a secret by name.

    Order of precedence:
    1. If ``GCP_PROJECT_ID`` is set and Secret Manager returns a value, use it.
    2. Otherwise fall back to the environment variable named ``name``.
    3. Otherwise return ``default``.
    """
    project_id = _gcp_project_id()
    if project_id:
        value = _fetch_from_secret_manager(name, project_id)
        if value is not None:
            return value

    env_value = os.getenv(name)
    if env_value is not None:
        return env_value

    return default
