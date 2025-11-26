"""
Prometheux MCP Server - CLI Entry Point

Runs the MCP server with stdio transport for integration with
Claude Desktop and other MCP clients.

Usage:
    prometheux-mcp --url https://your-jarvispy-instance.com
    
    # Or with environment variables:
    export PROMETHEUX_URL=https://your-jarvispy-instance.com
    export PROMETHEUX_TOKEN=your_token
    prometheux-mcp

Copyright (C) Prometheux Limited. All rights reserved.
"""

import sys
import click

from .server import run_server
from .config import Settings


@click.command()
@click.option(
    "--url",
    envvar="PROMETHEUX_URL",
    help="Prometheux/JarvisPy server URL (e.g., https://api.prometheux.ai)",
)
@click.option(
    "--token",
    envvar="PROMETHEUX_TOKEN",
    help="Authentication token",
)
@click.option(
    "--username",
    envvar="PROMETHEUX_USERNAME",
    help="Username for authentication",
)
@click.option(
    "--organization",
    envvar="PROMETHEUX_ORGANIZATION", 
    help="Organization identifier",
)
@click.option(
    "--debug",
    is_flag=True,
    envvar="PROMETHEUX_DEBUG",
    help="Enable debug logging",
)
@click.version_option()
def main(
    url: str | None,
    token: str | None,
    username: str | None,
    organization: str | None,
    debug: bool,
):
    """
    Prometheux MCP Server - Connect AI agents to Prometheux knowledge graphs.
    
    This server implements the Model Context Protocol (MCP) to expose
    Prometheux concepts and reasoning capabilities to AI agents like Claude.
    
    \b
    Example usage with Claude Desktop:
    
    1. Add to claude_desktop_config.json:
       {
         "mcpServers": {
           "prometheux": {
             "command": "prometheux-mcp",
             "args": ["--url", "https://your-server.com"],
             "env": {
               "PROMETHEUX_TOKEN": "your_token",
               "PROMETHEUX_USERNAME": "your_username",
               "PROMETHEUX_ORGANIZATION": "your_org"
             }
           }
         }
       }
    
    2. Restart Claude Desktop
    
    3. Ask Claude to list or run concepts in your projects
    """
    try:
        # Build settings from CLI args and environment
        settings = Settings(
            url=url,
            token=token,
            username=username,
            organization=organization,
            debug=debug,
        )
        
        if debug:
            print(f"Starting Prometheux MCP Server...", file=sys.stderr)
            print(f"  URL: {settings.url}", file=sys.stderr)
            print(f"  Username: {settings.username}", file=sys.stderr)
            print(f"  Organization: {settings.organization}", file=sys.stderr)
        
        # Run the MCP server
        run_server(settings)
        
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        if debug:
            print("Server stopped by user", file=sys.stderr)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        if debug:
            import traceback
            traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

