"""
HTTP Client for Prometheux/JarvisPy API.

Provides JSON-RPC communication with JarvisPy's MCP endpoint,
used by the proxy server to forward tool requests.

Copyright (C) Prometheux Limited. All rights reserved.
"""

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


class PrometheuxClient:
    """
    JSON-RPC client for JarvisPy's MCP endpoint.
    
    Sends JSON-RPC requests to ``/mcp/messages`` and returns the
    ``result`` field, raising on HTTP or RPC errors.
    """
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None
    
    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            if not self.settings.url:
                raise ValueError("Prometheux URL is required.")
            self._client = httpx.AsyncClient(
                base_url=self.settings.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    **self.settings.get_auth_headers(),
                },
                timeout=1800.0,
            )
        return self._client

    async def rpc(
        self,
        method: str,
        params: dict[str, Any],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """
        Send a JSON-RPC request to JarvisPy and return the ``result``.

        Args:
            method: JSON-RPC method (e.g. "tools/list", "tools/call").
            params: Method parameters.
            timeout: Per-request timeout override (seconds).

        Returns:
            The ``result`` field from the JSON-RPC response.

        Raises:
            AuthenticationError: On 401.
            PrometheuxError: On any other HTTP or RPC error.
        """
        client = self._get_client()

        try:
            kwargs: dict[str, Any] = {
                "json": {
                    "method": method,
                    "params": params,
                    "jsonrpc": "2.0",
                    "id": 1,
                }
            }
            if timeout is not None:
                kwargs["timeout"] = timeout

            response = await client.post("/mcp/messages", **kwargs)
        except httpx.ConnectError as e:
            raise PrometheuxError(
                f"Failed to connect to Prometheux at {self.settings.base_url}: {e}"
            )
        except httpx.TimeoutException as e:
            raise PrometheuxError(f"Request timed out: {e}")

        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your token and credentials.",
                status_code=401,
            )
        if response.status_code != 200:
            raise PrometheuxError(
                f"JarvisPy returned status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        if "error" in data:
            raise PrometheuxError(
                data["error"].get("message", "Unknown JSON-RPC error")
            )

        return data.get("result", {})

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
