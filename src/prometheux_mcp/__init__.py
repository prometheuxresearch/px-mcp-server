"""
Prometheux MCP Server

A Model Context Protocol (MCP) server that enables AI agents to interact
with Prometheux ontologies and reasoning capabilities.

Copyright (C) Prometheux Limited. All rights reserved.
"""

from importlib.metadata import PackageNotFoundError, version as _distribution_version
from pathlib import Path

try:
    __version__ = _distribution_version("prometheux-mcp")
except PackageNotFoundError:
    # Not installed, so there is no distribution metadata to read — a source
    # checkout run directly. Fall back to the file setup.py stamps into that
    # metadata at build time, so both paths report the same number. Hardcoding it
    # here instead drifts the moment someone bumps version.txt and forgets this
    # line: it sat at 0.1.0 through eleven releases.
    _version_file = Path(__file__).resolve().parents[2] / "version.txt"
    __version__ = (
        _version_file.read_text(encoding="utf-8").strip()
        if _version_file.is_file()
        else "0.0.0+unknown"
    )

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
