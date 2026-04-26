from starlette.types import ASGIApp, Receive, Scope, Send
import uuid

class RequestIDMiddleware:
    """Middleware to add unique request ID to each request using raw ASGI."""
    
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Generate or get request ID
        headers = dict(scope.get("headers", []))
        request_id = headers.get(b"x-request-id", str(uuid.uuid4()).encode()).decode()
        
        # Add to scope for access in app
        scope["request_id"] = request_id
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["request_id"] = request_id

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-request-id", request_id.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)
