"""
WebSocket Connection Manager

Manages active WebSocket connections and handles request/response forwarding.
"""

import asyncio
import uuid
from typing import Dict, Optional

from fastapi import WebSocket, WebSocketException, status


class ConnectionManager:
    """Manages WebSocket connections and request/response routing"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.pending_responses: Dict[str, asyncio.Future] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a new WebSocket connection
        
        Raises:
            WebSocketException: If a connection already exists
        """
        # Check if there's already an active connection
        if self.active_connections:
            # Reject the connection with an error
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Only one connection allowed at a time")
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION, reason="Only one connection allowed at a time")
        
        await websocket.accept()
        self.active_connections[client_id] = websocket
        print(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            print(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    def has_connections(self) -> bool:
        """Check if there are any active connections"""
        return len(self.active_connections) > 0
    
    async def forward_request(self, request_data: dict) -> Optional[dict]:
        """Forward request to first available WebSocket connection and wait for response"""
        if not self.active_connections:
            return None
        
        # Get first available connection
        client_id = next(iter(self.active_connections))
        websocket = self.active_connections[client_id]
        
        # Create a future for the response
        request_id = request_data["request_id"]
        future = asyncio.Future()
        self.pending_responses[request_id] = future
        
        try:
            # Send request to WebSocket client
            await websocket.send_json(request_data)
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=30.0)
            return response
        except asyncio.TimeoutError:
            print(f"Request {request_id} timed out")
            return None
        except Exception as e:
            print(f"Error forwarding request: {e}")
            return None
        finally:
            # Clean up
            if request_id in self.pending_responses:
                del self.pending_responses[request_id]
    
    def set_response(self, request_id: str, response_data: dict):
        """Set response for a pending request"""
        if request_id in self.pending_responses:
            future = self.pending_responses[request_id]
            if not future.done():
                future.set_result(response_data)

# Made with Bob
