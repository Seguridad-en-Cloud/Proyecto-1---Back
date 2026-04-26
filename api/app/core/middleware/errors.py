"""Error handling middleware for uniform error responses."""
from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with uniform format."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "message": exc.detail if isinstance(exc.detail, str) else "An error occurred",
            "request_id": request_id,
        },
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with uniform format."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "validation_error",
            "message": "Request validation failed",
            "errors": exc.errors(),
            "request_id": request_id,
        },
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Handle rate limit exceeded errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "request_id": request_id,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    
    # Log the error (in production, use proper logging)
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "internal_server_error",
            "message": "An internal server error occurred",
            "request_id": request_id,
        },
    )
