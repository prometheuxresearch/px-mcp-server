# Prometheux MCP Server

[![PyPI version](https://badge.fury.io/py/prometheux-mcp.svg)](https://badge.fury.io/py/prometheux-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) client that enables AI agents like Claude to interact with [Prometheux](https://prometheux.ai) knowledge graphs and reasoning capabilities.

---

## For Users

### What This Does

This package lets you use **Claude Desktop** to interact with your Prometheux projects:
- List concepts in your projects
- Run concepts to derive new knowledge
- All through natural conversation with Claude

### Prerequisites

- **Prometheux account** with access to a deployed instance
- **Claude Desktop** installed on your machine
- **Your credentials** (token, username, organization) from your Prometheux admin

### Installation

```bash
pip install prometheux-mcp
```

**macOS users:** If you encounter permission issues with Claude Desktop, use pipx instead:

```bash
brew install pipx
pipx ensurepath
pipx install prometheux-mcp
```

### Configuration

1. **Get your credentials** from your Prometheux admin or account settings:
   - Server URL (e.g., `https://api.prometheux.ai`)
   - Authentication token
   - Username
   - Organization

2. **Configure Claude Desktop** by editing the config file:

   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   ```json
   {
     "mcpServers": {
       "prometheux": {
         "command": "prometheux-mcp",
         "args": ["--url", "https://api.prometheux.ai"],
         "env": {
           "PROMETHEUX_TOKEN": "your_token",
           "PROMETHEUX_USERNAME": "your_username",
           "PROMETHEUX_ORGANIZATION": "your_organization"
         }
       }
     }
   }
   ```

   > **macOS with pipx:** Use the full path `~/.local/bin/prometheux-mcp` for the command.

3. **Restart Claude Desktop** (quit completely with Cmd+Q, then reopen)

### Usage

Once configured, just chat with Claude:

> "What concepts are available in project customer-analytics?"

> "Run the churn_prediction concept in project customer-analytics"

> "Show me the high_value_customers from project sales-data with min_value of 1000"

### Available Tools

| Tool | Description |
|------|-------------|
| `list_concepts` | Lists all concepts in a project |
| `run_concept` | Executes a concept to derive new knowledge |

### Troubleshooting

**"Server disconnected" error (macOS):**
Install with pipx and use the full path `~/.local/bin/prometheux-mcp` in your config.

**"Connection refused" error:**
Check that your Prometheux server URL is correct and accessible.

**"Authentication failed" error:**
Verify your token, username, and organization are correct.

**Check logs:**
`~/Library/Logs/Claude/mcp-server-prometheux.log`

---

## For Developers

This section is for developers who want to:
- Contribute to this package
- Test locally with a development JarvisPy instance
- Understand the architecture

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR MACHINE                                   │
│  ┌─────────────────┐         ┌─────────────────┐                        │
│  │  Claude Desktop │         │ prometheux-mcp  │                        │
│  │                 │──stdio──│  (this package) │                        │
│  │   (AI Agent)    │         │                 │                        │
│  └─────────────────┘         └────────┬────────┘                        │
└───────────────────────────────────────┼─────────────────────────────────┘
                                        │ HTTP
                                        ▼
                          ┌─────────────────────────┐
                          │     Prometheux Server   │
                          │       (JarvisPy)        │
                          │                         │
                          │   Cloud or On-Premise   │
                          └─────────────────────────┘
```

**Key points:**
- This is NOT a service you run — Claude Desktop starts it automatically
- Communication with Claude Desktop is via stdio (stdin/stdout)
- Communication with Prometheux is via HTTP
- Stateless — each Claude session starts a fresh instance

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/prometheux-ar/px-mcp-server.git
cd px-mcp-server

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

### Testing with Local JarvisPy

1. **Start JarvisPy** in development mode:
   ```bash
   cd /path/to/jarvispy
   source venv/bin/activate
   RUN_MODE=development python run.py
   ```

2. **Install your local package with pipx** (required for Claude Desktop on macOS):
   ```bash
   pipx install /path/to/px-mcp-server --force
   ```

3. **Configure Claude Desktop** to use localhost:
   ```json
   {
     "mcpServers": {
       "prometheux": {
         "command": "/Users/YOUR_USERNAME/.local/bin/prometheux-mcp",
         "args": ["--url", "http://localhost:8000", "--debug"]
       }
     }
   }
   ```

4. **Restart Claude Desktop** and test

### Why pipx for macOS?

Claude Desktop on macOS cannot access virtual environments in protected folders (like `~/Documents`) due to security restrictions. pipx installs to `~/.local/` which is accessible.

### Running Tests

```bash
pytest
```

### Code Quality

```bash
ruff check src/    # Linting
mypy src/          # Type checking
```

### Project Structure

```
src/prometheux_mcp/
├── __init__.py      # Package exports
├── __main__.py      # CLI entry point (Click-based)
├── config.py        # Configuration management
├── client.py        # HTTP client for Prometheux API
├── server.py        # MCP server and tool definitions
└── tools/           # Reserved for future tool modules
```

### Building for PyPI

```bash
python -m build
twine upload dist/*
```

---

## Tool Reference

### `list_concepts`

Lists all concepts available in a project.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string | Yes | — | Project identifier |
| `scope` | string | No | `"user"` | `"user"` or `"organization"` |

**Example response:**
```json
{
  "concepts": [
    {
      "predicate_name": "customer",
      "fields": {"id": "string", "name": "string"},
      "column_count": 2,
      "is_input": true,
      "row_count": 1000,
      "type": "postgresql",
      "description": "Customer records"
    }
  ],
  "count": 1
}
```

### `run_concept`

Executes a concept to derive new knowledge through Vadalog reasoning.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_id` | string | Yes | — | Project identifier |
| `concept_name` | string | Yes | — | Concept to execute |
| `params` | object | No | `{}` | Parameters for reasoning |
| `scope` | string | No | `"user"` | `"user"` or `"organization"` |
| `force_rerun` | boolean | No | `true` | Re-execute even if cached |
| `persist_outputs` | boolean | No | `false` | Save results to database |

**Example response:**
```json
{
  "concept_name": "high_value_customers",
  "message": "Concept executed successfully",
  "evaluation_results": {
    "resultSet": {
      "high_value_customers": [["Alice", 5000], ["Bob", 3000]]
    },
    "columnNames": {
      "high_value_customers": ["name", "total_value"]
    }
  },
  "predicates_populated": ["high_value_customers"],
  "total_records": 2
}
```

---

## Related Projects

- [Prometheux](https://prometheux.ai) — Knowledge graph and reasoning platform
- [JarvisPy](https://github.com/prometheux-ar/jarvispy) — Prometheux backend (server-side MCP endpoints)
- [Model Context Protocol](https://modelcontextprotocol.io) — Open standard for AI tool integration

## License

MIT License — Copyright (C) Prometheux Limited.

## Support

- **Documentation**: [docs.prometheux.ai](https://docs.prometheux.ai)
- **Issues**: [GitHub Issues](https://github.com/prometheux-ar/px-mcp-server/issues)
- **Email**: support@prometheux.ai
