"""
Setup Functions for FastAPI InRoute Package

Provides a unified function to configure the app based on environment settings.
"""

from typing import Optional
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from .config import inroute_config
from .manager import ConnectionManager
from .middleware import WebSocketForwardMiddleware
from .server import websocket_endpoint
from .processor import RequestProcessor
from .client import create_lifespan


def setup_inroute(app: FastAPI) -> None:
    """
    Configure FastAPI app with InRoute functionality based on config settings.
    
    This function automatically sets up the app based on environment variables:
    - FASTAPI_INROUTE_IS_SERVER: Enable server mode (middleware + WebSocket endpoint)
    - FASTAPI_INROUTE_IS_CLIENT: Enable client mode (WebSocket client connection)
    
    The function attaches necessary components to the app object without returning anything.
    
    Args:
        app: FastAPI application instance to configure
    
    Example:
        ```python
        from fastapi import FastAPI
        from fastapi_inroute import setup_inroute
        
        app = FastAPI()
        
        # Add your routes
        @app.get("/")
        def read_root():
            return {"Hello": "World"}
        
        # Setup InRoute based on environment config
        setup_inroute(app)
        ```
    
    Environment Variables:
        - FASTAPI_INROUTE_IS_SERVER: Enable server mode (default: True)
        - FASTAPI_INROUTE_IS_CLIENT: Enable client mode (default: False)
        - FASTAPI_INROUTE_SERVER_URL: WebSocket URL for client mode (default: ws://localhost:8000/inroute)
        - WEBSOCKET_FORWARD_SKIP_PATHS: Comma-separated paths to skip (default: /inroute,/health,/metrics)
        - WEBSOCKET_FORWARD_DEBUG: Enable debug logging (default: False)
    """
    # Log configuration if debug is enabled
    inroute_config.log_config()
    
    # Setup server mode components
    if inroute_config.is_server:
        # Create connection manager
        manager = ConnectionManager()
        
        # Add middleware with skip paths
        skip_paths = inroute_config.middleware_skip_paths
        app.add_middleware(
            WebSocketForwardMiddleware,
            manager=manager,
            skip_paths=skip_paths
        )
        
        # Store manager in app state for access in routes
        app.state.manager = manager
        
        # Add WebSocket endpoint
        @app.websocket("/inroute")
        async def ws_endpoint(websocket: WebSocket):
            """WebSocket endpoint for client connections"""
            await websocket_endpoint(websocket, manager)
        
        # Add connections monitoring endpoint
        @app.get("/connections")
        def get_active_connections():
            """Get information about active WebSocket connections"""
            return {
                "active_connections": len(manager.active_connections),
                "client_ids": list(manager.active_connections.keys()),
                "has_connections": manager.has_connections()
            }
    
    # Setup client mode components
    if inroute_config.is_client:
        # Create test client for processing requests
        test_client = TestClient(app)
        
        # Create processor
        processor = RequestProcessor(test_client)
        
        # Store processor in app state
        app.state.processor = processor
        
        # Create and set lifespan
        lifespan = create_lifespan(websocket_url=inroute_config.websocket_url, processor=processor)
        app.router.lifespan_context = lifespan


# Made with Bob