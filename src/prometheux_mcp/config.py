"""
Configuration management for Prometheux MCP Server.

Handles settings from environment variables and CLI arguments.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

# Mirror JarvisPy's app/mcp/gateway.py and app/mcp/server_confirmation.py.
SURFACE_HEADER = "X-Prometheux-MCP-Surface"
SURFACE_GATEWAY = "gateway"
SURFACE_FULL = "full"
CONFIRM_HEADER = "X-Prometheux-MCP-Confirm"
CONFIRM_ON_SERVER = "server"


@dataclass
class Settings:
    """
    Configuration settings for the Prometheux MCP server.
    
    Settings can be provided via:
    - CLI arguments (highest priority)
    - Environment variables
    - Default values (lowest priority)
    
    Environment Variables:
        PROMETHEUX_URL: Base URL of the Prometheux/JarvisPy server
        PROMETHEUX_TOKEN: Authentication token
        PROMETHEUX_USERNAME: Username for API routing
        PROMETHEUX_ORGANIZATION: Organization for API routing
        PROMETHEUX_DEBUG: Enable debug mode ("true" or "1")
        PROMETHEUX_USE_POD_ROUTING: Use pod routing prefix ("false" to disable)
        PROMETHEUX_MCP_SURFACE: "gateway" for the gateway surface, "full" (default)
            for the full tool list
        PROMETHEUX_MCP_CONFIRM_ON_SERVER: Let Prometheux ask the user before writes
            on the full tool list ("true" or "1"); the gateway always does
    """
    
    url: Optional[str] = field(default=None)
    token: Optional[str] = field(default=None)
    username: Optional[str] = field(default=None)
    organization: Optional[str] = field(default=None)
    debug: bool = field(default=False)
    use_pod_routing: bool = field(default=True)
    surface: Optional[str] = field(default=None)
    confirm_on_server: bool = field(default=False)
    
    def __post_init__(self):
        """Load from environment variables if not provided."""
        # URL
        if self.url is None:
            self.url = os.environ.get("PROMETHEUX_URL")
        
        # Remove trailing slash from URL
        if self.url:
            self.url = self.url.rstrip("/")
        
        # Token
        if self.token is None:
            self.token = os.environ.get("PROMETHEUX_TOKEN")
        
        # Username
        if self.username is None:
            self.username = os.environ.get("PROMETHEUX_USERNAME")
        
        # Organization
        if self.organization is None:
            self.organization = os.environ.get("PROMETHEUX_ORGANIZATION")
        
        # Debug
        if not self.debug:
            debug_env = os.environ.get("PROMETHEUX_DEBUG", "").lower()
            self.debug = debug_env in ("true", "1", "yes")
        
        # Pod routing
        pod_routing_env = os.environ.get("PROMETHEUX_USE_POD_ROUTING", "").lower()
        if pod_routing_env in ("false", "0", "no"):
            self.use_pod_routing = False

        # Surface: absent or "full" is the full tool list
        if self.surface is None:
            self.surface = os.environ.get("PROMETHEUX_MCP_SURFACE")
        self.surface = (self.surface or "").strip().lower() or None
        if self.surface == SURFACE_FULL:
            self.surface = None

        if not self.confirm_on_server:
            confirm_env = os.environ.get("PROMETHEUX_MCP_CONFIRM_ON_SERVER", "").lower()
            self.confirm_on_server = confirm_env in ("true", "1", "yes")
        
        # Validate required settings
        self._validate()
    
    def _validate(self):
        """Validate that required settings are present."""
        if not self.url:
            raise ValueError(
                "Prometheux URL is required. "
                "Set via --url or PROMETHEUX_URL environment variable."
            )
        if not self.username:
            raise ValueError(
                "Username is required. "
                "Set via --username or PROMETHEUX_USERNAME environment variable."
            )
        if not self.organization:
            raise ValueError(
                "Organization is required. "
                "Set via --organization or PROMETHEUX_ORGANIZATION environment variable."
            )
        if self.surface not in (None, SURFACE_GATEWAY):
            raise ValueError(
                f"Unknown surface {self.surface!r}: use 'gateway' or 'full'. "
                "Set via --surface or PROMETHEUX_MCP_SURFACE environment variable."
            )
    
    @property
    def base_url(self) -> str:
        """
        Get the base URL for API requests.
        
        Builds the full path including jarvispy/{organization}/{username}
        which is required for routing through the API Gateway in production.
        """
        if not self.url or not self.organization or not self.username:
            return self.url or ""
        if not self.use_pod_routing:
            return self.url
        return f"{self.url}/jarvispy/{self.organization}/{self.username}"
    
    @property
    def mcp_endpoint(self) -> str:
        """Get the MCP messages endpoint URL."""
        return f"{self.base_url}/mcp/messages"
    
    @property
    def has_auth(self) -> bool:
        """Check if authentication credentials are provided."""
        return bool(self.token)
    
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_surface_headers(self) -> dict[str, str]:
        """Headers that pick how JarvisPy lists its tools and who confirms writes."""
        headers = {}
        if self.surface:
            headers[SURFACE_HEADER] = self.surface
        if self.confirm_on_server:
            headers[CONFIRM_HEADER] = CONFIRM_ON_SERVER
        return headers

