"""The stdio proxy forwards JarvisPy's initialize instructions to the host."""

import pytest
from pytest_httpx import HTTPXMock

from prometheux_mcp import server as server_module
from prometheux_mcp.config import Settings


@pytest.fixture
def settings():
    return Settings(
        url="https://api.prometheux.ai",
        token="test_token",
        username="test_user",
        organization="test_org",
    )


@pytest.fixture(autouse=True)
def fresh_client():
    server_module._client = None
    yield
    server_module._client = None


MESSAGES = "https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages"


@pytest.mark.asyncio
async def test_initialize_instructions_reach_the_server(settings, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=MESSAGES,
        json={"jsonrpc": "2.0", "id": 1, "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "prometheux", "version": "1.0.0"},
            "instructions": "## Context protocol\nRules travel here.",
        }},
    )
    server = server_module.create_server(settings)
    server.instructions = await server_module.fetch_instructions(settings)
    assert server.create_initialization_options().instructions == (
        "## Context protocol\nRules travel here."
    )
    sent = httpx_mock.get_requests()[0]
    assert sent.url == MESSAGES
    assert b'"method": "initialize"' in sent.content or b'"method":"initialize"' in sent.content


@pytest.mark.asyncio
async def test_backend_failure_means_no_instructions_not_a_crash(settings, httpx_mock: HTTPXMock):
    httpx_mock.add_response(url=MESSAGES, status_code=503, text="down")
    assert await server_module.fetch_instructions(settings) is None


@pytest.mark.asyncio
async def test_empty_instructions_are_omitted(settings, httpx_mock: HTTPXMock):
    httpx_mock.add_response(
        url=MESSAGES,
        json={"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2024-11-05"}},
    )
    assert await server_module.fetch_instructions(settings) is None
