"""
FastAPI InRoute - WebSocket-based request forwarding for FastAPI applications

This package provides functionality to forward HTTP requests between FastAPI applications
via WebSocket connections, enabling local development against deployed servers.
"""

from .setup import setup_inroute
from .config import inroute_config, Config
from .manager import ConnectionManager
from .middleware import WebSocketForwardMiddleware
from .processor import RequestProcessor
from .client import WebSocketClient, create_lifespan
from .server import websocket_endpoint

__version__ = "0.1.1"

__all__ = [
    # Main setup function
    "setup_inroute",
    
    # Configuration
    "inroute_config",
    "Config",
    
    # Core components
    "ConnectionManager",
    "WebSocketForwardMiddleware",
    "RequestProcessor",
    "WebSocketClient",
    
    # Functions
    "create_lifespan",
    "websocket_endpoint",
    
    # Version
    "__version__",
]


def main() -> None:
    """CLI entry point for the package"""
    print("Hello from fastapi-inroute!")
    print(f"Version: {__version__}")
    print("\nTo use this package, import and call setup_inroute() in your FastAPI app:")
    print("\n  from fastapi import FastAPI")
    print("  from fastapi_inroute import setup_inroute")
    print("\n  app = FastAPI()")
    print("  setup_inroute(app)")
    print("\nFor more information, see the README.md file.")


# Made with Bob
