# syntax=docker/dockerfile:1.7
# ─────────────────────────────────────────────────────────────────────────
# Multi-stage build for the LiveMenu API.
# Stage 1 ("builder") compiles wheels for native deps (Pillow, asyncpg).
# Stage 2 ("runtime") runs as a non-root user with the smallest possible
# attack surface (no compilers, no apt cache, no shell scripting).
# ─────────────────────────────────────────────────────────────────────────

ARG PYTHON_VERSION=3.12-slim

# ── Stage 1: builder ──────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Compilers + headers needed only at build time. They are NOT copied to the
# runtime image, keeping the final image small and reducing CVE surface.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libjpeg-dev \
        zlib1g-dev \
        libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml requirements.txt ./

RUN pip install --upgrade pip && \
    pip wheel --wheel-dir=/wheels -r requirements.txt

# ── Stage 2: runtime ──────────────────────────────────────────────────────
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/api \
    PORT=8000

# curl is only used by the HEALTHCHECK; libjpeg/libwebp are runtime libs for
# Pillow. No compilers in the runtime image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libjpeg62-turbo \
        libwebp7 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 app \
    && useradd  --system --uid 1001 --gid app --home /app --shell /usr/sbin/nologin app

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*.whl && rm -rf /wheels

COPY --chown=app:app api/      ./api/
COPY --chown=app:app database/ ./database/
COPY --chown=app:app alembic.ini ./

USER app

EXPOSE 8000

# In-container health probe; Cloud Run also probes the ``/api/v1/auth/health``
# endpoint independently via its load-balancer.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS "http://localhost:${PORT}/api/v1/auth/health" || exit 1

# Migrations are NOT run on every startup. Reason: alembic uses a synchronous
# engine that doesn't know about the Cloud SQL Connector, so it would hang on
# cold start and Cloud Run would kill the container before it binds the port.
# Migrations are applied out-of-band (one-off Cloud Run job, manual gcloud
# run jobs execute, or a release-time CI step). See docs/GUIA-DESPLIEGUE.md.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
