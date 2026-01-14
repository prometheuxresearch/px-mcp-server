"""
MCP Server for Prometheux.

Creates and runs the Model Context Protocol server that exposes
Prometheux concepts and reasoning capabilities to AI agents.

Copyright (C) Prometheux Limited. All rights reserved.
"""

import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from .config import Settings
from .client import PrometheuxClient, PrometheuxError


# Global settings and client (set when server is created)
_settings: Settings | None = None
_client: PrometheuxClient | None = None


def get_client() -> PrometheuxClient:
    """Get the Prometheux client instance."""
    global _client, _settings
    if _client is None:
        if _settings is None:
            raise RuntimeError("Server not initialized. Call create_server() first.")
        _client = PrometheuxClient(_settings)
    return _client


def create_server(settings: Settings) -> FastMCP:
    """
    Create and configure the MCP server.
    
    Args:
        settings: Configuration settings for the server
        
    Returns:
        Configured FastMCP server instance
    """
    global _settings
    _settings = settings
    
    # Create the MCP server
    mcp = FastMCP("prometheux")
    
    # Register tools
    _register_tools(mcp)
    
    return mcp


def _register_tools(mcp: FastMCP):
    """Register all MCP tools."""
    
    @mcp.tool()
    async def list_concepts(
        project_id: str,
        scope: str = "user"
    ) -> dict[str, Any]:
        """
        List all concepts available in a project.
        
        Concepts are the building blocks of knowledge in Prometheux. Each concept
        represents a predicate/relation with its schema, rules, and metadata.
        
        Args:
            project_id: The unique identifier of the project to list concepts from
            scope: The scope to search for concepts. Use "user" for personal concepts
                   or "organization" to include shared organizational concepts.
                   Defaults to "user".
        
        Returns:
            A dictionary containing:
            - concepts: List of concept objects, each with:
                - predicate_name: The name of the concept/predicate
                - fields: Dictionary mapping field names to their types
                - column_count: Number of columns/fields in the concept
                - is_input: Whether this is an input concept (no derivation rules)
                - row_count: Number of records if the concept has been populated
                - type: The type of datasource (e.g., 'postgresql', 'csv', 'api')
                - description: Human-readable description of the concept
            - count: Total number of concepts found
        """
        try:
            client = get_client()
            result = await client.list_concepts(project_id, scope)
            return result
        except PrometheuxError as e:
            return {"error": str(e), "concepts": [], "count": 0}
        except Exception as e:
            return {"error": f"Unexpected error: {e}", "concepts": [], "count": 0}
    
    @mcp.tool()
    async def run_concept(
        project_id: str,
        concept_name: str,
        params: dict[str, Any] | None = None,
        scope: str = "user",
        force_rerun: bool = True,
        persist_outputs: bool = False
    ) -> dict[str, Any]:
        """
        Execute a concept to derive new knowledge through reasoning.
        
        This runs the Vadalog reasoning engine on the specified concept,
        applying its rules to derive output facts from input data.
        
        Args:
            project_id: The unique identifier of the project containing the concept
            concept_name: The name of the concept/predicate to execute
            params: Optional dictionary of parameters to pass to the reasoning engine.
                    These can be used to filter inputs or configure execution.
            scope: The scope to search for the concept. Use "user" for personal concepts
                   or "organization" to include shared organizational concepts.
                   Defaults to "user".
            force_rerun: If True, re-execute even if results already exist.
                        If False, return cached results when available.
                        Defaults to True.
            persist_outputs: If True, save the derived facts to the database.
                            If False, return results without persisting.
                            Defaults to False.
        
        Returns:
            A dictionary containing:
            - concept_name: The executed concept name
            - message: Status message describing the execution result
            - evaluation_results: The reasoning results including:
                - resultSet: Dictionary mapping predicate names to their derived facts
                - columnNames: Dictionary mapping predicate names to their column names
            - predicates_populated: List of predicates that were populated with data
            - total_records: Total number of records derived
            - skipped_execution: True if cached results were returned (force_rerun=False)
        """
        try:
            client = get_client()
            result = await client.run_concept(
                project_id=project_id,
                concept_name=concept_name,
                params=params,
                scope=scope,
                force_rerun=force_rerun,
                persist_outputs=persist_outputs,
            )
            return result
        except PrometheuxError as e:
            return {"error": str(e), "concept_name": concept_name}
        except Exception as e:
            return {"error": f"Unexpected error: {e}", "concept_name": concept_name}


def run_server(settings: Settings):
    """
    Run the MCP server with stdio transport.
    
    This function blocks and handles MCP messages until the client disconnects.
    
    Args:
        settings: Configuration settings for the server
    """
    # Create the server
    mcp = create_server(settings)
    
    if settings.debug:
        print(f"MCP Server 'prometheux' starting...", file=sys.stderr)
        print(f"Connected to: {settings.url}", file=sys.stderr)
    
    # Run with stdio transport
    mcp.run(transport="stdio")

