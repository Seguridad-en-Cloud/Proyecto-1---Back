"""Main FastAPI application."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.api.routers import (
    analytics,
    auth,
    categories,
    dishes,
    menu,
    menu_public,
    qr,
    restaurant,
    upload,
)
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

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the image-processing worker pool over the app lifetime.

    Replaces the deprecated ``@app.on_event("startup"/"shutdown")`` hooks.
    """
    from app.services.upload_service import (
        install_signal_handlers,
        shutdown_workers,
        start_workers,
    )

    from database.session import init_connector, close_connector

    await init_connector()
    await start_workers()
    install_signal_handlers()
    try:
        yield
    finally:
        await shutdown_workers()
        await close_connector()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="LiveMenu Backend API",
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan,
)

app.state.limiter = limiter

# Middlewares (Starlette applies them in reverse-add order, so this list
# reads outer-to-inner): RequestID first so every request gets a UUID even
# when CORS rejects it.
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(menu_public.router)
app.include_router(auth.router)
app.include_router(restaurant.router)
app.include_router(categories.router)
app.include_router(dishes.router)
app.include_router(analytics.router)
app.include_router(menu.router)
app.include_router(upload.router)
app.include_router(qr.router)
