"""
WebSocket Client

Client-side WebSocket connection handler for receiving and processing forwarded requests.
Can be conditionally enabled/disabled via environment variables.
"""

import asyncio
import json
import os
from typing import Optional
from contextlib import asynccontextmanager

import websockets
from fastapi import FastAPI

from .processor import RequestProcessor
from .config import inroute_config


class WebSocketClient:
    """WebSocket client for connecting to server and processing forwarded requests"""
    
    def __init__(self, processor: RequestProcessor):
        self.processor = processor
        self.websocket_task: Optional[asyncio.Task] = None
    
    async def connect_to_server(self, websocket_url: str):
        """Connect to deployed server and handle forwarded requests"""
        retry_delay = inroute_config.retry_delay
        max_retries = None  # Infinite retries
        retry_count = 0
        
        while True:
            try:
                print(f"Connecting to {websocket_url}...")
                
                async with websockets.connect(websocket_url) as websocket:
                    print("✓ Connected! Waiting for requests...")
                    retry_count = 0  # Reset retry count on successful connection
            
                    # Send periodic pings to keep connection alive
                    async def send_pings():
                        while True:
                            try:
                                await websocket.send(json.dumps({"type": "ping"}))
                                await asyncio.sleep(inroute_config.ping_interval)
                            except Exception as e:
                                print(f"Ping error: {e}")
                                break
                    
                    # Start ping task
                    ping_task = asyncio.create_task(send_pings())
                    
                    try:
                        async for message in websocket:
                            data = json.loads(message)
                            message_type = data.get("type")
                            
                            if message_type == "http_request":
                                # Process the forwarded HTTP request
                                request_id = data.get("request_id")
                                print(f"\nReceived request {request_id}")
                                
                                # Process request locally
                                response_data = await self.processor.process_http_request(data)
                                
                                # Send response back
                                response_message = {
                                    "type": "http_response",
                                    "request_id": request_id,
                                    "status_code": response_data["status_code"],
                                    "body": response_data["body"],
                                    "headers": response_data["headers"]
                                }
                                
                                await websocket.send(json.dumps(response_message))
                                print(f"Sent response for {request_id}")
                            
                            elif message_type == "pong":
                                # Keep-alive response
                                pass
                            
                            else:
                                print(f"Unknown message type: {message_type}")
                    
                    except websockets.exceptions.ConnectionClosed:
                        print("Connection closed")
                    finally:
                        ping_task.cancel()
            
            except asyncio.CancelledError:
                print("WebSocket client task cancelled")
                break
            except Exception as e:
                retry_count += 1
                print(f"Connection error: {e}")
                print(f"Retrying in {retry_delay} seconds... (attempt {retry_count})")
                await asyncio.sleep(retry_delay)
    
    async def start(self, websocket_url: str):
        """Start the WebSocket client as a background task"""
        self.websocket_task = asyncio.create_task(self.connect_to_server(websocket_url))
    
    async def stop(self):
        """Stop the WebSocket client"""
        if self.websocket_task and not self.websocket_task.done():
            self.websocket_task.cancel()
            try:
                await self.websocket_task
            except asyncio.CancelledError:
                pass


def create_lifespan(websocket_url: Optional[str] = None, processor: Optional[RequestProcessor] = None):
    """
    Create a lifespan context manager for FastAPI that starts WebSocket client on startup
    
    The client will only start if WEBSOCKET_FORWARD_ENABLE_CLIENT is set to true.
    
    Args:
        websocket_url: WebSocket URL to connect to (defaults to FASTAPI_INROUTE_SERVER_URL env var or ws://localhost:8000/inroute)
        processor: RequestProcessor instance (required if client is enabled)
    
    Returns:
        Async context manager for FastAPI lifespan
    """
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager to start WebSocket client on startup"""
        client = None
        
        # Only start client if enabled
        if inroute_config.is_client:
            if processor is None:
                raise ValueError("processor is required when WEBSOCKET_FORWARD_ENABLE_CLIENT is true")
            
            # Get WebSocket URL from parameter, environment, or use default
            url = websocket_url or inroute_config.websocket_url
            
            print("=" * 60)
            print("FastAPI WebSocket Client - Background Mode")
            print("=" * 60)
            print(f"Server URL: {url}")
            print("=" * 60)
            print("\nStarting WebSocket client in background...")
            
            # Create and start WebSocket client
            client = WebSocketClient(processor)
            await client.start(url)
        else:
            if inroute_config.debug:
                print("WebSocket client disabled (WEBSOCKET_FORWARD_ENABLE_CLIENT=false)")
        
        yield  # Server is running
        
        # Cleanup on shutdown
        if client is not None:
            print("\nShutting down WebSocket client...")
            await client.stop()
    
    return lifespan

# Made with Bob
