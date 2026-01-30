"""
Configuration module for WebSocket Forward

Handles environment variable configuration for enabling/disabling features.
"""

import os

class Config:
    """Configuration class for WebSocket Forward features"""
    
    def __init__(self):
        self._load_config()
        self._validate_config()
    
    def _load_config(self):
        """Load configuration from environment variables"""
        # Feature flags
        self.is_server = self._get_bool("FASTAPI_INROUTE_IS_SERVER", False)
        self.is_client = self._get_bool("FASTAPI_INROUTE_IS_CLIENT", False)
        
        # WebSocket configuration
        self.websocket_url = os.getenv("FASTAPI_INROUTE_SERVER_URL", "ws://localhost:8000/inroute")
        
        # Connection settings
        self.ping_interval = int(os.getenv("WEBSOCKET_PING_INTERVAL", "30"))
        self.retry_delay = int(os.getenv("WEBSOCKET_RETRY_DELAY", "5"))
        
        # Middleware settings
        self.middleware_skip_paths = self._get_list("WEBSOCKET_FORWARD_SKIP_PATHS", ["/inroute", "/health", "/metrics"])
        
        # Debug mode
        self.debug = self._get_bool("WEBSOCKET_FORWARD_DEBUG", False)
    
    def _validate_config(self):
        """Validate configuration to ensure only one mode is active"""
        if self.is_server and self.is_client:
            raise ValueError(
                "Invalid configuration: Cannot enable both server and client modes simultaneously. "
                "Set either FASTAPI_INROUTE_IS_SERVER=true or FASTAPI_INROUTE_IS_CLIENT=true, but not both."
            )
        
        if not self.is_server and not self.is_client:
            raise ValueError(
                "Invalid configuration: At least one mode must be enabled. "
                "Set either FASTAPI_INROUTE_IS_SERVER=true or FASTAPI_INROUTE_IS_CLIENT=true."
            )
    
    def _get_bool(self, key: str, default: bool) -> bool:
        """Get boolean value from environment variable"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
    
    def _get_list(self, key: str, default: list) -> list:
        """Get list value from environment variable (comma-separated)"""
        value = os.getenv(key)
        if value is None:
            return default
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def get_mode_name(self) -> str:
        """Get human-readable mode name"""
        if self.is_server:
            return "Server"
        elif self.is_client:
            return "Client"
        else:
            return "Unknown"
    
    def log_config(self):
        """Log current configuration"""
        if self.debug:
            print("\n" + "=" * 60)
            print("FastAPI InRoute Configuration")
            print("=" * 60)
            print(f"Mode: {self.get_mode_name()}")
            if self.is_client:
                print(f"WebSocket URL: {self.websocket_url}")
            if self.is_server:
                print(f"Skip Paths: {', '.join(self.middleware_skip_paths)}")
            print(f"Debug: {self.debug}")
            print("=" * 60 + "\n")


# Global configuration instance
inroute_config = Config()

# Made with Bob