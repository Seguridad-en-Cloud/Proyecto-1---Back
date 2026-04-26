"""Request ID middleware to add unique ID to each request."""
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process request and add request ID."""
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        
        # Store in request state for access in other parts of the app
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id
        
        return response
