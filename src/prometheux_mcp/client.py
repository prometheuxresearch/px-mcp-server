"""
HTTP Client for Prometheux/JarvisPy API.

Provides a typed client for interacting with the Prometheux API,
used by MCP tools to execute operations.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import json
import httpx
from typing import Any

from .config import Settings


class PrometheuxError(Exception):
    """Base exception for Prometheux API errors."""
    
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(PrometheuxError):
    """Raised when authentication fails."""
    pass


class NotFoundError(PrometheuxError):
    """Raised when a resource is not found."""
    pass


class PrometheuxClient:
    """
    HTTP client for the Prometheux/JarvisPy API.
    
    This client provides methods for interacting with concepts,
    projects, and other Prometheux resources via the REST API.
    
    Example:
        settings = Settings(url="https://api.prometheux.ai", token="...")
        client = PrometheuxClient(settings)
        concepts = await client.list_concepts("project-123")
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the Prometheux client.
        
        Args:
            settings: Configuration settings including URL and credentials
        """
        self.settings = settings
        self._client: httpx.AsyncClient | None = None
    
    async def __aenter__(self) -> "PrometheuxClient":
        """Async context manager entry."""
        if not self.settings.url:
            raise ValueError("Prometheux URL is required. Settings must be validated before use.")
        self._client = httpx.AsyncClient(
            base_url=self.settings.url,
            headers=self._get_headers(),
            timeout=60.0,
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        headers.update(self.settings.get_auth_headers())
        return headers
    
    def _get_client(self) -> httpx.AsyncClient:
        """Get the HTTP client, creating one if needed."""
        if self._client is None:
            if not self.settings.url:
                raise ValueError("Prometheux URL is required. Settings must be validated before use.")
            self._client = httpx.AsyncClient(
                base_url=self.settings.url,
                headers=self._get_headers(),
                timeout=60.0,
            )
        return self._client
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Any:
        """
        Make an HTTP request to the Prometheux API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., "/api/v1/concepts")
            **kwargs: Additional arguments passed to httpx
            
        Returns:
            Parsed JSON response
            
        Raises:
            AuthenticationError: If authentication fails
            NotFoundError: If resource not found
            PrometheuxError: For other API errors
        """
        client = self._get_client()
        
        try:
            response = await client.request(method, path, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Check your token and credentials.",
                    status_code=401
                )
            
            if response.status_code == 404:
                raise NotFoundError(
                    f"Resource not found: {path}",
                    status_code=404
                )
            
            if response.status_code >= 400:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get("detail", error_detail)
                except (ValueError, TypeError):
                    # If response isn't valid JSON, use the raw text
                    pass
                raise PrometheuxError(
                    f"API error ({response.status_code}): {error_detail}",
                    status_code=response.status_code
                )
            
            return response.json()
            
        except httpx.ConnectError as e:
            raise PrometheuxError(
                f"Failed to connect to Prometheux server at {self.settings.url}. "
                f"Is the server running? Error: {e}"
            )
        except httpx.TimeoutException as e:
            raise PrometheuxError(f"Request timed out: {e}")
    
    # =========================================================================
    # Concept Operations
    # =========================================================================
    
    async def list_concepts(
        self,
        project_id: str,
        scope: str = "user"
    ) -> dict[str, Any]:
        """
        List all concepts in a project.
        
        Args:
            project_id: The project identifier
            scope: Scope to search ("user" or "organization")
            
        Returns:
            Dictionary containing concepts list and count
        """
        # Call the MCP endpoint which handles the concept listing
        return await self._mcp_call("list_concepts", {
            "project_id": project_id,
            "scope": scope,
        })
    
    async def run_concept(
        self,
        project_id: str,
        concept_name: str,
        params: dict[str, Any] | None = None,
        scope: str = "user",
        force_rerun: bool = True,
        persist_outputs: bool = False,
    ) -> dict[str, Any]:
        """
        Execute a concept to derive new knowledge.
        
        Args:
            project_id: The project identifier
            concept_name: Name of the concept to execute
            params: Optional parameters for the reasoning engine
            scope: Scope to search ("user" or "organization")
            force_rerun: Re-execute even if results exist
            persist_outputs: Save derived facts to database
            
        Returns:
            Execution results including derived facts
        """
        return await self._mcp_call("run_concept", {
            "project_id": project_id,
            "concept_name": concept_name,
            "params": params,
            "scope": scope,
            "force_rerun": force_rerun,
            "persist_outputs": persist_outputs,
        })
    
    # =========================================================================
    # MCP Protocol Methods
    # =========================================================================
    
    async def _mcp_call(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """
        Call an MCP tool via the HTTP endpoint.
        
        Args:
            tool_name: Name of the MCP tool to call
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        response = await self._request(
            "POST",
            "/mcp/messages",
            json={
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
                "jsonrpc": "2.0",
                "id": 1,
            }
        )
        
        # Check for JSON-RPC error
        if "error" in response:
            error = response["error"]
            raise PrometheuxError(
                f"Tool execution failed: {error.get('message', 'Unknown error')}",
                status_code=error.get("code")
            )
        
        # Extract result from JSON-RPC response
        result = response.get("result", {})
        
        # The tool result is wrapped in content array
        if "content" in result:
            content = result["content"]
            if content and isinstance(content, list):
                # Parse the JSON string from content
                text_content = content[0].get("text", "{}")
                return json.loads(text_content)
        
        return result
    
    async def mcp_initialize(self) -> dict[str, Any]:
        """
        Initialize MCP connection.
        
        Returns:
            Server capabilities and info
        """
        return await self._request(
            "POST",
            "/mcp/messages",
            json={
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "prometheux-mcp",
                        "version": "0.1.0",
                    }
                },
                "jsonrpc": "2.0",
                "id": 0,
            }
        )
    
    async def mcp_list_tools(self) -> list[dict[str, Any]]:
        """
        List available MCP tools.
        
        Returns:
            List of tool definitions
        """
        response = await self._request(
            "POST",
            "/mcp/messages",
            json={
                "method": "tools/list",
                "params": {},
                "jsonrpc": "2.0",
                "id": 1,
            }
        )
        
        result = response.get("result", {})
        return result.get("tools", [])
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

