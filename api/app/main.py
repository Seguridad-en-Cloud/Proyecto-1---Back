"""Main FastAPI application."""
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routers import analytics, auth, categories, dishes, menu, restaurant
from app.core.config import settings
from app.core.logging import configure_logging
from app.core.middleware.errors import (
    general_exception_handler,
    http_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from app.core.middleware.rate_limit import limiter
from app.core.middleware.request_id import RequestIDMiddleware

# Configure logging
configure_logging()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LiveMenu Backend API",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
)

# Add rate limiter state
app.state.limiter = limiter

# Add middlewares (order matters - applied in reverse order)
# 1. Request ID (first to add ID to all requests)
app.add_middleware(RequestIDMiddleware)

# 2. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(auth.router)
app.include_router(restaurant.router)
app.include_router(categories.router)
app.include_router(dishes.router)
app.include_router(analytics.router)
app.include_router(menu.router)


@app.on_event("startup")
async def startup_event():
    """Startup event handler."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler."""
    pass
