"""
Prometheux MCP Server

A Model Context Protocol (MCP) server that enables AI agents to interact
with Prometheux knowledge graphs and reasoning capabilities.

Copyright (C) Prometheux Limited. All rights reserved.
"""

__version__ = "0.1.0"
__author__ = "Prometheux Limited"

from .server import create_server, run_server
from .client import PrometheuxClient
from .config import Settings

__all__ = [
    "__version__",
    "create_server",
    "run_server",
    "PrometheuxClient",
    "Settings",
]

