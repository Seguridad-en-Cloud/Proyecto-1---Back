"""Rate limiting middleware.

When the API runs behind a load balancer (Cloud Run + GLB, AWS ALB, …) every
request reaches us with the LB's address as ``request.client.host``, which
would cause the limiter to throttle every user as if they were the same IP.

We therefore extract the original client IP from ``X-Forwarded-For``, but only
when ``TRUSTED_PROXIES > 0`` so a malicious client cannot spoof the header on
direct connections.
"""
from __future__ import annotations

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config import settings


def _client_ip(request: Request) -> str:
    """Return the real client IP, honouring ``X-Forwarded-For`` when trusted."""
    if settings.trusted_proxies > 0:
        xff = request.headers.get("x-forwarded-for")
        if xff:
            # XFF is a comma-separated list: client, proxy1, proxy2, ...
            # The N-th from the right is the closest hop we trust.
            parts = [p.strip() for p in xff.split(",") if p.strip()]
            idx = max(0, len(parts) - settings.trusted_proxies)
            if parts:
                return parts[idx]
    return get_remote_address(request)


limiter = Limiter(
    key_func=_client_ip,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
)
