"""
WebSocket Server Endpoint

Provides the WebSocket endpoint handler for the server side.
"""

import uuid
from fastapi import WebSocket, WebSocketDisconnect

from .manager import ConnectionManager


async def websocket_endpoint(websocket: WebSocket, manager: ConnectionManager):
    """
    WebSocket endpoint handler for receiving client connections
    
    Args:
        websocket: The WebSocket connection
        manager: ConnectionManager instance to handle the connection
    """
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from WebSocket client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "http_response":
                # This is a response to a forwarded request
                request_id = data.get("request_id")
                response_data = {
                    "status_code": data.get("status_code", 200),
                    "body": data.get("body"),
                    "headers": data.get("headers", {})
                }
                manager.set_response(request_id, response_data)
            
            elif message_type == "ping":
                # Keep-alive ping
                await websocket.send_json({"type": "pong"})
            
            else:
                # Unknown message type
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# Made with Bob
