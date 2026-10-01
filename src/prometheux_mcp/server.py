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

Runs with stdio transport for Claude Desktop integration.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import json
import sys
from typing import Any, Optional

import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server

from .config import Settings
from .client import PrometheuxClient, PrometheuxError


_settings: Settings | None = None
_client: PrometheuxClient | None = None
_cached_tools: Optional[list[types.Tool]] = None


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
        global _cached_tools
        if _cached_tools is not None:
            return _cached_tools

        client = _get_client()
        result = await client.rpc("tools/list", {})

        tools: list[types.Tool] = []
        for t in result.get("tools", []):
            tools.append(types.Tool(
                name=t["name"],
                description=t.get("description", ""),
                inputSchema=t.get("inputSchema", {
                    "type": "object", "properties": {},
                }),
            ))

        _cached_tools = tools
        if settings.debug:
            print(f"Cached {len(tools)} tools from JarvisPy", file=sys.stderr)
        return tools

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None = None,
    ) -> list[types.TextContent]:
        if settings.debug:
            print(f"tools/call → {name}", file=sys.stderr)

        client = _get_client()
        call_args = arguments or {}

        timeout = 1800.0 if name == "run_concept" else 120.0

        try:
            result = await client.rpc(
                "tools/call",
                {"name": name, "arguments": call_args},
                timeout=timeout,
            )
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
