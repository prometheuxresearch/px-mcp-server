"""
MCP Server for Prometheux.

Creates a low-level MCP server that dynamically proxies tools from JarvisPy.
Tools are discovered at runtime via ``tools/list`` and all ``tools/call``
requests are forwarded transparently — no hard-coded tool definitions needed.

JarvisPy's ``initialize`` instructions are forwarded too: they carry the same
context block the embedded Prometheux assistant has in its system prompt (how
context reaches the model, the skills index, the user's standing rules), so a
host that surfaces server instructions governs this client by the same rules.
Hosts that drop instructions can call the ``get_session_context`` tool instead.

With ``--surface gateway`` JarvisPy lists ``describe``, ``call`` and ``write``
instead of every tool, and asks the user before writes: a call it stops for
approval is put to the user through MCP elicitation and sent again with their
decision. A host without elicitation passes JarvisPy's answer to the model,
which sends the user to the approvals page in Prometheux.

Runs with stdio transport for Claude Desktop integration.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import json
import sys
from typing import Any, Optional

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.shared.exceptions import McpError

from .config import Settings
from .client import PrometheuxClient, PrometheuxError


_settings: Settings | None = None
_client: PrometheuxClient | None = None
_cached_tools: Optional[list[types.Tool]] = None

# JarvisPy marks a tool that can run for minutes with this `_meta` key, and the
# gateway's `call` and `write` list the long-running tools they run under the
# second one. Older JarvisPy builds advertise neither, hence the fallback.
_LONG_RUNNING_META_KEY = "prometheux/long_running"
_LONG_RUNNING_TOOLS_META_KEY = "prometheux/long_running_tools"
_FALLBACK_LONG_RUNNING = frozenset({"run_concept"})
_LONG_RUNNING_TIMEOUT = 1800.0
_CALL_TIMEOUT = 120.0

# A call JarvisPy stopped for the user's approval is sent again with their
# decision under these `_meta` keys (JarvisPy's app/mcp/server_confirmation.py).
META_APPROVED = "prometheux/approved"
META_ALWAYS = "prometheux/always"
META_DENIED = "prometheux/denied"
ONCE, ALWAYS, DENY = "once", "always", "deny"
_CHOICE_TITLES = {ONCE: "Allow once", ALWAYS: "Always allow", DENY: "Deny"}


def _get_client() -> PrometheuxClient:
    global _client, _settings
    if _client is None:
        if _settings is None:
            raise RuntimeError("Server not initialized. Call create_server() first.")
        _client = PrometheuxClient(_settings)
    return _client


def _to_text_content(rpc_result: dict[str, Any]) -> list[types.TextContent]:
    """Convert a ``tools/call`` RPC result into MCP TextContent objects."""
    content = rpc_result.get("content", [])
    if content and isinstance(content, list):
        return [
            types.TextContent(type="text", text=item.get("text", ""))
            for item in content
        ]
    return [types.TextContent(type="text", text=json.dumps(rpc_result, indent=2))]


def _to_tool(spec: dict[str, Any]) -> types.Tool:
    """A JarvisPy tool definition, with the title, the behavioural annotations
    (read-only, destructive) and the Prometheux `_meta` hints kept."""
    return types.Tool(
        name=spec["name"],
        title=spec.get("title"),
        description=spec.get("description", ""),
        inputSchema=spec.get("inputSchema", {"type": "object", "properties": {}}),
        annotations=spec.get("annotations"),
        _meta=spec.get("_meta"),
    )


def is_long_running(name: str, arguments: Optional[dict], tools: list[types.Tool]) -> bool:
    """Whether a call may run for minutes: the tool is marked long-running, or it
    is the gateway's `call`/`write` running a tool that is."""
    inner = (arguments or {}).get("tool")
    tool = next((t for t in tools if t.name == name), None)
    if tool is None:
        return name in _FALLBACK_LONG_RUNNING or inner in _FALLBACK_LONG_RUNNING
    meta = tool.meta or {}
    if meta.get(_LONG_RUNNING_META_KEY):
        return True
    if isinstance(inner, str) and inner in (meta.get(_LONG_RUNNING_TOOLS_META_KEY) or ()):
        return True
    return name in _FALLBACK_LONG_RUNNING


def approval_of(rpc_result: dict[str, Any]) -> Optional[dict]:
    """The approval a `tools/call` result asks for, if JarvisPy stopped the call."""
    text = "".join(item.get("text", "") for item in rpc_result.get("content") or [])
    try:
        value = json.loads(text)
    except ValueError:
        return None
    if not isinstance(value, dict) or not value.get("needs_approval"):
        return None
    approval = value.get("approval")
    return approval if isinstance(approval, dict) and approval.get("id") else None


def decision_schema(persistable: bool) -> dict:
    """The form put to the user: "Always allow" only for a tool that may be."""
    choices = [ONCE, ALWAYS, DENY] if persistable else [ONCE, DENY]
    return {
        "type": "object",
        "properties": {"decision": {
            "type": "string",
            "title": "Decision",
            "enum": choices,
            "enumNames": [_CHOICE_TITLES[c] for c in choices],
        }},
        "required": ["decision"],
    }


def decision_of(answer: types.ElicitResult, persistable: bool) -> str:
    """What the user chose; anything but an accepted, valid choice is a no."""
    if answer.action != "accept":
        return DENY
    decision = (answer.content or {}).get("decision")
    if decision == ALWAYS and not persistable:
        return DENY
    return decision if decision in (ONCE, ALWAYS, DENY) else DENY


def decision_meta(approval_id: str, decision: str) -> dict:
    """The `_meta` that carries the user's decision back to JarvisPy."""
    if decision == DENY:
        return {META_DENIED: approval_id}
    if decision == ALWAYS:
        return {META_APPROVED: approval_id, META_ALWAYS: True}
    return {META_APPROVED: approval_id}


async def _tools() -> list[types.Tool]:
    """JarvisPy's tool list, fetched once per process: stdio serves one user."""
    global _cached_tools
    if _cached_tools is None:
        result = await _get_client().rpc("tools/list", {})
        _cached_tools = [_to_tool(t) for t in result.get("tools", [])]
    return _cached_tools


async def _routing_tools() -> list[types.Tool]:
    """The tool list to route a call by, or none if it cannot be read: the call
    then gets the fallback timeout and reports its own failure."""
    try:
        return await _tools()
    except PrometheuxError:
        return []


def _can_elicit(server: Server) -> bool:
    client_params = server.request_context.session.client_params
    return bool(client_params and client_params.capabilities.elicitation is not None)


async def _ask_and_rerun(
    server: Server,
    params: dict[str, Any],
    approval: dict,
    stopped: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    """Put a call JarvisPy stopped for approval to the user, and send it again
    with their decision. A host without elicitation, one that fails to ask, and
    a question dismissed without a choice (``cancel``, which is also what a
    headless host answers) get JarvisPy's result as is: the request stays open,
    and the result tells the model where the user approves it."""
    if not _can_elicit(server):
        return stopped
    persistable = bool(approval.get("persistable"))
    ctx = server.request_context
    try:
        answer = await ctx.session.elicit(
            str(approval.get("question") or "Allow this Prometheux action?"),
            decision_schema(persistable),
            related_request_id=ctx.request_id,
        )
    except McpError:
        return stopped
    if _settings and _settings.debug:
        print(f"elicitation ← {answer.action}", file=sys.stderr)
    if answer.action == "cancel":
        return stopped
    decided = {**params, "_meta": decision_meta(approval["id"], decision_of(answer, persistable))}
    return await _get_client().rpc("tools/call", decided, timeout=timeout)


def create_server(settings: Settings) -> Server:
    """
    Create and configure the MCP server.

    Returns a ``mcp.server.lowlevel.Server`` that proxies all tool
    traffic to JarvisPy.
    """
    global _settings
    _settings = settings

    server = Server("prometheux")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        tools = await _tools()
        if settings.debug:
            print(f"Listing {len(tools)} tools from JarvisPy", file=sys.stderr)
        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None = None,
    ) -> list[types.TextContent]:
        if settings.debug:
            print(f"tools/call → {name}", file=sys.stderr)

        params = {"name": name, "arguments": arguments or {}}
        long_running = is_long_running(name, arguments, await _routing_tools())
        timeout = _LONG_RUNNING_TIMEOUT if long_running else _CALL_TIMEOUT

        try:
            result = await _get_client().rpc("tools/call", params, timeout=timeout)
            approval = approval_of(result)
            if approval is not None:
                result = await _ask_and_rerun(server, params, approval, result, timeout)
        except PrometheuxError as exc:
            if settings.debug:
                print(f"tools/call ← {name} FAILED: {exc}", file=sys.stderr)
            return [types.TextContent(
                type="text",
                text=json.dumps({"error": str(exc)}),
            )]

        content = _to_text_content(result)
        if settings.debug:
            print(
                f"tools/call ← {name} succeeded ({len(content)} content items)",
                file=sys.stderr,
            )
        return content

    return server


# JarvisPy renders the instructions per caller (the user's rules are fetched
# from the database), so a slow backend must not stall the host's handshake:
# past this budget the client starts without instructions and the model can
# still fetch the block through get_session_context.
_INSTRUCTIONS_TIMEOUT = 10.0


async def fetch_instructions(settings: Settings) -> Optional[str]:
    """Ask JarvisPy for its ``initialize`` instructions; None if unavailable."""
    try:
        result = await _get_client().rpc(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "prometheux-mcp", "version": _package_version()},
            },
            timeout=_INSTRUCTIONS_TIMEOUT,
        )
    except PrometheuxError as exc:
        if settings.debug:
            print(f"initialize ← no instructions: {exc}", file=sys.stderr)
        return None
    instructions = result.get("instructions")
    if settings.debug:
        print(
            f"initialize ← {len(instructions or '')} chars of instructions",
            file=sys.stderr,
        )
    return instructions or None


def _package_version() -> str:
    try:
        from . import __version__
        return __version__
    except Exception:  # pragma: no cover — import cycle or missing metadata
        return "unknown"


async def _run_stdio(server: Server, settings: Settings):
    """Run the server with stdio transport."""
    # The host's own initialize request waits in the pipe while this runs; the
    # low-level Server reads ``instructions`` when it builds the handshake reply.
    server.instructions = await fetch_instructions(settings)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream,
            server.create_initialization_options(),
        )


def run_server(settings: Settings):
    """
    Run the MCP server with stdio transport.

    This function blocks and handles MCP messages until the client disconnects.
    """
    import asyncio

    server = create_server(settings)

    if settings.debug:
        print(f"MCP Server 'prometheux' starting...", file=sys.stderr)
        print(f"Connected to: {settings.base_url}", file=sys.stderr)

    asyncio.run(_run_stdio(server, settings))
