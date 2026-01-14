"""
Configuration management for Prometheux MCP Server.

Handles settings from environment variables and CLI arguments.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


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
        PROMETHEUX_USERNAME: Username for authentication
        PROMETHEUX_ORGANIZATION: Organization identifier
        PROMETHEUX_DEBUG: Enable debug mode ("true" or "1")
    """
    
    url: Optional[str] = field(default=None)
    token: Optional[str] = field(default=None)
    username: Optional[str] = field(default=None)
    organization: Optional[str] = field(default=None)
    debug: bool = field(default=False)
    
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
        
        # Validate required settings
        self._validate()
    
    def _validate(self):
        """Validate that required settings are present."""
        if not self.url:
            raise ValueError(
                "Prometheux URL is required. "
                "Set via --url or PROMETHEUX_URL environment variable."
            )
    
    @property
    def base_url(self) -> str:
        """
        Get the full base URL for API requests.
        
        If username and organization are provided, automatically constructs
        the full JarvisPy path: {url}/jarvispy/{organization}/{username}
        
        Otherwise, returns the URL as-is (for backward compatibility).
        """
        if not self.url:
            return ""
        
        # If both username and organization are provided, construct the full path
        if self.username and self.organization:
            # Check if the URL already contains the jarvispy path
            if "/jarvispy/" not in self.url:
                return f"{self.url}/jarvispy/{self.organization}/{self.username}"
        
        # Return URL as-is if no username/org or path already included
        return self.url
    
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

