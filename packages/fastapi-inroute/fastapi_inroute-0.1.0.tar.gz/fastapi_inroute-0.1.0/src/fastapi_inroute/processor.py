"""
Request Processor

Handles processing of HTTP requests forwarded via WebSocket.
"""

import json
from fastapi.testclient import TestClient


class RequestProcessor:
    """Processes HTTP requests using a FastAPI TestClient"""
    
    def __init__(self, client: TestClient):
        self.client = client
    
    async def process_http_request(self, request_data: dict) -> dict:
        """Process HTTP request locally and return response"""
        method = request_data["method"]
        path = request_data["path"]
        query_params = request_data.get("query_params", {})
        headers = request_data.get("headers", {})
        body = request_data.get("body")
        
        # Build URL with query parameters
        url = path
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            url = f"{path}?{query_string}"
        
        print(f"Processing {method} {url}")
        
        # Process request using TestClient
        try:
            if method == "GET":
                response = self.client.get(url, headers=headers)
            elif method == "POST":
                response = self.client.post(url, json=json.loads(body) if body else None, headers=headers)
            elif method == "PUT":
                response = self.client.put(url, json=json.loads(body) if body else None, headers=headers)
            elif method == "DELETE":
                response = self.client.delete(url, headers=headers)
            elif method == "PATCH":
                response = self.client.patch(url, json=json.loads(body) if body else None, headers=headers)
            else:
                return {
                    "status_code": 405,
                    "body": {"error": f"Method {method} not supported"},
                    "headers": {}
                }
            
            return {
                "status_code": response.status_code,
                "body": response.json() if response.content else None,
                "headers": dict(response.headers)
            }
        except Exception as e:
            print(f"Error processing request: {e}")
            return {
                "status_code": 500,
                "body": {"error": str(e)},
                "headers": {}
            }

# Made with Bob
