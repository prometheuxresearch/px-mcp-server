"""The gateway surface, the server's approvals and the long-running timeout."""

import json
from types import SimpleNamespace

import mcp.types as types
import pytest
from mcp.server.lowlevel.server import request_ctx
from pytest_httpx import HTTPXMock

from prometheux_mcp import server as server_module
from prometheux_mcp.config import Settings

MESSAGES = "https://api.prometheux.ai/jarvispy/test_org/test_user/mcp/messages"

WRITE = {
    "name": "write",
    "title": "Write",
    "description": "Run a tool that changes something.",
    "inputSchema": {"type": "object"},
    "annotations": {"destructiveHint": True},
    "_meta": {"prometheux/long_running_tools": ["copy_ontology", "run_concept"]},
}
COPY = {
    "name": "copy_ontology",
    "inputSchema": {"type": "object"},
    "_meta": {"prometheux/long_running": True},
}
LIST = {"name": "list_concepts", "inputSchema": {"type": "object"},
        "annotations": {"readOnlyHint": True}}

STOPPED = {"content": [{"type": "text", "text": json.dumps({
    "success": False,
    "needs_approval": True,
    "approval": {"id": "ap-1", "tool": "create_concept", "persistable": True,
                 "question": "Prometheux: allow create concept?"},
    "message": "Nothing was done: ask the user to approve it in Prometheux.",
})}]}
DONE = {"content": [{"type": "text", "text": '{"success": true}'}]}


def settings(**overrides) -> Settings:
    return Settings(url="https://api.prometheux.ai", token="test_token",
                    username="test_user", organization="test_org", **overrides)


class FakeClient:
    """JarvisPy: lists `tools`, and answers calls from `answers` in turn."""

    def __init__(self, tools=(WRITE, COPY, LIST), answers=(DONE,)):
        self.tools = list(tools)
        self.answers = list(answers)
        self.calls: list[tuple[dict, float | None]] = []

    async def rpc(self, method, params, timeout=None):
        if method == "tools/list":
            return {"tools": self.tools}
        self.calls.append((params, timeout))
        return self.answers.pop(0) if self.answers else DONE


class FakeSession:
    def __init__(self, elicitation=True, action="accept", decision="once"):
        capabilities = SimpleNamespace(elicitation=object() if elicitation else None)
        self.client_params = SimpleNamespace(capabilities=capabilities)
        self.answer = types.ElicitResult(action=action, content={"decision": decision})
        self.asked: list[tuple[str, dict]] = []

    async def elicit(self, message, requested_schema, related_request_id=None):
        self.asked.append((message, requested_schema))
        return self.answer


@pytest.fixture(autouse=True)
def fresh_state():
    server_module._client = None
    server_module._cached_tools = None
    yield
    server_module._client = None
    server_module._cached_tools = None


async def call(client: FakeClient, session: FakeSession, name: str, arguments: dict) -> str:
    server_module._client = client
    server = server_module.create_server(settings())
    token = request_ctx.set(SimpleNamespace(
        request_id=7, session=session, meta=None, lifespan_context=None, request=None,
    ))
    try:
        handler = server.request_handlers[types.CallToolRequest]
        result = await handler(types.CallToolRequest(
            method="tools/call",
            params=types.CallToolRequestParams(name=name, arguments=arguments),
        ))
    finally:
        request_ctx.reset(token)
    return result.root.content[0].text


class TestSettings:
    def test_full_list_by_default_sends_no_surface_header(self):
        assert settings().get_surface_headers() == {}

    def test_gateway_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("PROMETHEUX_MCP_SURFACE", "Gateway")
        assert settings().get_surface_headers() == {"X-Prometheux-MCP-Surface": "gateway"}

    def test_full_is_the_same_as_unset(self):
        assert settings(surface="full").surface is None

    def test_an_unknown_surface_is_refused(self):
        with pytest.raises(ValueError, match="Unknown surface"):
            settings(surface="code")

    def test_confirm_on_server_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("PROMETHEUX_MCP_CONFIRM_ON_SERVER", "true")
        assert settings().get_surface_headers() == {"X-Prometheux-MCP-Confirm": "server"}

    @pytest.mark.asyncio
    async def test_every_request_carries_the_headers(self, httpx_mock: HTTPXMock):
        httpx_mock.add_response(url=MESSAGES, json={"jsonrpc": "2.0", "id": 1, "result": {}})
        server_module._settings = settings(surface="gateway")
        await server_module.fetch_instructions(server_module._settings)
        sent = httpx_mock.get_requests()[0]
        assert sent.headers["X-Prometheux-MCP-Surface"] == "gateway"


class TestToolList:
    @pytest.mark.asyncio
    async def test_title_annotations_and_meta_reach_the_host(self):
        server_module._client = FakeClient()
        tools = {t.name: t for t in await server_module._tools()}
        assert tools["write"].title == "Write"
        assert tools["write"].annotations.destructiveHint is True
        assert tools["list_concepts"].annotations.readOnlyHint is True
        assert tools["copy_ontology"].meta == {"prometheux/long_running": True}


class TestLongRunning:
    def test_a_tool_marked_long_running(self):
        tools = [server_module._to_tool(t) for t in (WRITE, COPY, LIST)]
        assert server_module.is_long_running("copy_ontology", {}, tools) is True
        assert server_module.is_long_running("list_concepts", {}, tools) is False

    def test_the_gateway_running_a_long_running_tool(self):
        tools = [server_module._to_tool(t) for t in (WRITE, COPY, LIST)]
        assert server_module.is_long_running("write", {"tool": "run_concept"}, tools) is True
        assert server_module.is_long_running("write", {"tool": "create_concept"}, tools) is False

    def test_run_concept_without_a_list(self):
        assert server_module.is_long_running("run_concept", {}, []) is True
        assert server_module.is_long_running("write", {"tool": "run_concept"}, []) is True
        assert server_module.is_long_running("list_concepts", {}, []) is False

    @pytest.mark.asyncio
    async def test_a_long_running_call_gets_the_long_timeout(self):
        client = FakeClient()
        await call(client, FakeSession(), "write", {"tool": "run_concept", "arguments": {}})
        await call(client, FakeSession(), "write", {"tool": "create_concept", "arguments": {}})
        assert [timeout for _, timeout in client.calls] == [1800.0, 120.0]


class TestApproval:
    @pytest.mark.asyncio
    async def test_the_user_is_asked_and_the_call_sent_again(self):
        client = FakeClient(answers=[STOPPED, DONE])
        session = FakeSession(decision="always")
        text = await call(client, session, "write", {"tool": "create_concept", "arguments": {}})

        assert text == '{"success": true}'
        message, schema = session.asked[0]
        assert message == "Prometheux: allow create concept?"
        assert schema["properties"]["decision"]["enum"] == ["once", "always", "deny"]
        rerun, _ = client.calls[1]
        assert rerun["_meta"] == {"prometheux/approved": "ap-1", "prometheux/always": True}
        assert rerun["arguments"] == {"tool": "create_concept", "arguments": {}}

    @pytest.mark.asyncio
    async def test_a_declined_question_is_a_denial(self):
        client = FakeClient(answers=[STOPPED, DONE])
        await call(client, FakeSession(action="decline"), "write", {"tool": "create_concept"})
        assert client.calls[1][0]["_meta"] == {"prometheux/denied": "ap-1"}

    @pytest.mark.asyncio
    async def test_a_dismissed_question_leaves_the_request_open(self):
        client = FakeClient(answers=[STOPPED, DONE])
        text = await call(client, FakeSession(action="cancel"), "write", {"tool": "create_concept"})
        assert "approve it in Prometheux" in text
        assert len(client.calls) == 1

    @pytest.mark.asyncio
    async def test_always_is_refused_for_a_call_that_may_not_be_always_allowed(self):
        stopped = json.loads(STOPPED["content"][0]["text"])
        stopped["approval"]["persistable"] = False
        client = FakeClient(answers=[{"content": [{"type": "text", "text": json.dumps(stopped)}]}, DONE])
        session = FakeSession(decision="always")
        await call(client, session, "write", {"tool": "create_concept"})
        assert session.asked[0][1]["properties"]["decision"]["enum"] == ["once", "deny"]
        assert client.calls[1][0]["_meta"] == {"prometheux/denied": "ap-1"}

    @pytest.mark.asyncio
    async def test_a_host_without_elicitation_passes_the_message_to_the_model(self):
        client = FakeClient(answers=[STOPPED])
        text = await call(client, FakeSession(elicitation=False), "write", {"tool": "create_concept"})
        assert "approve it in Prometheux" in text
        assert len(client.calls) == 1

    @pytest.mark.asyncio
    async def test_an_ordinary_result_is_not_an_approval(self):
        client = FakeClient(answers=[DONE])
        session = FakeSession()
        assert await call(client, session, "list_concepts", {}) == '{"success": true}'
        assert session.asked == []
