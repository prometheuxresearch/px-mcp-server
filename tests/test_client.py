"""Tests for the Prometheux HTTP client."""

import pytest
import httpx
from pytest_httpx import HTTPXMock

from prometheux_mcp.config import Settings
from prometheux_mcp.client import (
    PrometheuxClient,
    PrometheuxError,
    AuthenticationError,
    NotFoundError,
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
    async def test_list_concepts_success(self, client, httpx_mock: HTTPXMock):
        """Test successful concept listing."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": '{"concepts": [{"predicate_name": "test"}], "count": 1}'
                        }
                    ]
                },
                "id": 1
            }
        )
        
        result = await client.list_concepts("project-123")
        
        assert result["count"] == 1
        assert result["concepts"][0]["predicate_name"] == "test"
    
    @pytest.mark.asyncio
    async def test_run_concept_success(self, client, httpx_mock: HTTPXMock):
        """Test successful concept execution."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": '{"concept_name": "test", "total_records": 10}'
                        }
                    ]
                },
                "id": 1
            }
        )
        
        result = await client.run_concept("project-123", "test")
        
        assert result["concept_name"] == "test"
        assert result["total_records"] == 10
    
    @pytest.mark.asyncio
    async def test_authentication_error(self, client, httpx_mock: HTTPXMock):
        """Test authentication error handling."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            status_code=401,
        )
        
        with pytest.raises(AuthenticationError):
            await client.list_concepts("project-123")
    
    @pytest.mark.asyncio
    async def test_not_found_error(self, client, httpx_mock: HTTPXMock):
        """Test not found error handling."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            status_code=404,
        )
        
        with pytest.raises(NotFoundError):
            await client.list_concepts("project-123")
    
    @pytest.mark.asyncio
    async def test_mcp_list_tools(self, client, httpx_mock: HTTPXMock):
        """Test listing MCP tools."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {"name": "list_concepts", "description": "List concepts"},
                        {"name": "run_concept", "description": "Run concept"},
                    ]
                },
                "id": 1
            }
        )
        
        tools = await client.mcp_list_tools()
        
        assert len(tools) == 2
        assert tools[0]["name"] == "list_concepts"
        assert tools[1]["name"] == "run_concept"
    
    @pytest.mark.asyncio
    async def test_context_manager(self, settings, httpx_mock: HTTPXMock):
        """Test async context manager."""
        httpx_mock.add_response(
            url="https://api.prometheux.ai/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "result": {
                    "content": [{"type": "text", "text": '{"concepts": [], "count": 0}'}]
                },
                "id": 1
            }
        )
        
        async with PrometheuxClient(settings) as client:
            result = await client.list_concepts("project-123")
            assert result["count"] == 0

