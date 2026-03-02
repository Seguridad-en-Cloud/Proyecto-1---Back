# ── Stage 1: build deps in a throwaway layer ──────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Only system libs needed to compile wheels (gcc, image libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libjpeg62-turbo-dev zlib1g-dev libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install into a virtual-env so we can copy it cleanly
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ── Stage 2: lean runtime image ───────────────────────────────────
FROM python:3.12-slim

# Only runtime libs — no gcc, no dev headers
RUN apt-get update && apt-get install -y --no-install-recommends \
        libjpeg62-turbo libwebp7 curl tini \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy only what the app needs
COPY api/    ./api/
COPY database/ ./database/
COPY alembic.ini ./

# Non-root user for security
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/auth/health || exit 1

# tini handles PID 1 / zombie reaping; graceful shutdown
ENTRYPOINT ["tini", "--"]
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1"]
