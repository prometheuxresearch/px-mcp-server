"""Tests for the Prometheux HTTP client."""

import pytest
from pytest_httpx import HTTPXMock

from prometheux_mcp.config import Settings
from prometheux_mcp.client import (
    PrometheuxClient,
    PrometheuxError,
    AuthenticationError,
)


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        url="https://api.prometheux.ai",
        token="test_token",
        username="test_user",
        organization="test_org",
    )


@pytest.fixture
def client(settings):
    """Create test client."""
    return PrometheuxClient(settings)


class TestPrometheuxClient:
    """Tests for the PrometheuxClient class."""

    @pytest.mark.asyncio
    async def test_rpc_tools_list(self, client, httpx_mock: HTTPXMock):
        """Test tools/list RPC call."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {"name": "list_concepts", "description": "List concepts"},
                        {"name": "run_concept", "description": "Run concept"},
                    ]
                },
                "id": 1,
            },
        )

        result = await client.rpc("tools/list", {})

        assert len(result["tools"]) == 2
        assert result["tools"][0]["name"] == "list_concepts"

    @pytest.mark.asyncio
    async def test_rpc_tools_call(self, client, httpx_mock: HTTPXMock):
        """Test tools/call RPC call."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {"type": "text", "text": '{"concepts": [], "count": 0}'}
                    ]
                },
                "id": 1,
            },
        )

        result = await client.rpc(
            "tools/call",
            {"name": "list_concepts", "arguments": {"ontology_id": "p1"}},
        )

        assert "content" in result
        assert result["content"][0]["type"] == "text"

    @pytest.mark.asyncio
    async def test_authentication_error(self, client, httpx_mock: HTTPXMock):
        """Test authentication error handling."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages",
            status_code=401,
        )

        with pytest.raises(AuthenticationError):
            await client.rpc("tools/list", {})

    @pytest.mark.asyncio
    async def test_rpc_error_response(self, client, httpx_mock: HTTPXMock):
        """Test JSON-RPC error handling."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "Tool not found"},
                "id": 1,
            },
        )

        with pytest.raises(PrometheuxError, match="Tool not found"):
            await client.rpc("tools/call", {"name": "bad_tool", "arguments": {}})

    @pytest.mark.asyncio
    async def test_http_error(self, client, httpx_mock: HTTPXMock):
        """Test non-200 HTTP response handling."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages",
            status_code=500,
            text="Internal Server Error",
        )

        with pytest.raises(PrometheuxError, match="status 500"):
            await client.rpc("tools/list", {})
