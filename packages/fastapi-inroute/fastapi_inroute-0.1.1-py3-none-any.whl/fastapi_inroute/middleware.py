"""
WebSocket Forward Middleware

Middleware to intercept HTTP requests and forward them via WebSocket connections.
Can be conditionally enabled/disabled via environment variables.
"""

import uuid
from typing import Optional
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .manager import ConnectionManager
from .config import inroute_config


class WebSocketForwardMiddleware(BaseHTTPMiddleware):
    """Middleware to intercept and forward requests via WebSocket"""
    
    def __init__(self, app, manager: ConnectionManager, skip_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.manager = manager
        self.skip_paths = skip_paths if skip_paths is not None else inroute_config.middleware_skip_paths
    
    async def dispatch(self, request: Request, call_next):
        # Skip WebSocket upgrade requests and configured skip paths
        if request.url.path in self.skip_paths or request.headers.get("upgrade") == "websocket":
            return await call_next(request)
        
        # Check if there are active WebSocket connections
        if self.manager.has_connections():
            # Read request body
            body = await request.body()
            
            # Prepare request data to forward
            request_data = {
                "type": "http_request",
                "request_id": str(uuid.uuid4()),
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "body": body.decode() if body else None
            }
            
            # Forward request and wait for response
            response_data = await self.manager.forward_request(request_data)
            
            if response_data:
                # Return the response from WebSocket client
                return JSONResponse(
                    content=response_data.get("body"),
                    status_code=response_data.get("status_code", 200),
                    headers=response_data.get("headers", {})
                )
            else:
                # If forwarding failed, return error
                return JSONResponse(
                    content={"error": "Failed to forward request to WebSocket client"},
                    status_code=503
                )
        
        # No WebSocket connections, process normally
        return await call_next(request)

# Made with Bob
