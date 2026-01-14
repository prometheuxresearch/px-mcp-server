# Prometheux MCP Server

[![PyPI version](https://badge.fury.io/py/prometheux-mcp.svg)](https://badge.fury.io/py/prometheux-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

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

**Option 1: Using pipx (Recommended for Claude Desktop)**

```bash
# Install pipx if you don't have it
brew install pipx
pipx ensurepath

# Install prometheux-mcp
pipx install prometheux-mcp
```

This installs the package in an isolated environment and makes the `prometheux-mcp` command available globally.

**Option 2: Using pip**

```bash
pip install prometheux-mcp
```

> **Note for macOS users:** Claude Desktop may have permission issues accessing pip-installed packages in certain directories. If you encounter "Server disconnected" errors, use pipx instead.

### Configuration

1. **Get your credentials** from your Prometheux admin or account settings:
   - Server URL (e.g., `https://api.prometheux.ai`)
   - Authentication token
   - Username
   - Organization

2. **Configure Claude Desktop** by editing the config file:

   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   **If installed with pipx (recommended):**
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
   
   > **Note:** The full JarvisPy path (`/jarvispy/{organization}/{username}`) is automatically constructed from your username and organization. No need to include it in the URL!

   **If pipx isn't in PATH, use the full path:**
   ```json
   {
     "mcpServers": {
       "prometheux": {
         "command": "/Users/YOUR_USERNAME/.local/bin/prometheux-mcp",
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
   
   > Replace `YOUR_USERNAME` with your actual macOS username, or find the path with: `which prometheux-mcp`
   
   **For custom deployments with full URL:**
   
   If you need to specify the complete JarvisPy path (e.g., for custom routing), you can include it in the URL:
   ```json
   "args": ["--url", "https://api.prometheux.ai/jarvispy/myorg/myuser"]
   ```
   In this case, the organization and username from `env` are still used for authentication, but the URL is used as-is.

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
1. Uninstall: `pip uninstall prometheux-mcp`
2. Install with pipx: `pipx install prometheux-mcp`
3. Update your config with either `"command": "prometheux-mcp"` or the full path from `which prometheux-mcp`
4. Restart Claude Desktop completely (Cmd+Q, then reopen)

**"Connection refused" error:**
Check that your Prometheux server URL is correct and accessible. Test with: `curl [YOUR_URL]/mcp/info`

**"Authentication failed" error:**
Verify your token, username, and organization are correct in the config.

**"command not found" error:**
If using pipx, ensure it's in your PATH: `pipx ensurepath` then restart your terminal or Claude Desktop.

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
git clone https://github.com/prometheuxresearch/px-mcp-server.git
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

## Access to Prometheux Backend

The Prometheux backend is required to use this MCP client. To request access:

- 📧 **Email**: davben@prometheux.co.uk, teodoro.baldazzi@prometheux.co.uk, or support@prometheux.co.uk
- 🌐 **Website**: https://www.prometheux.ai

## License

BSD 3-Clause License — see [LICENSE](LICENSE) file for details.

## About Prometheux

Prometheux is an **ontology native data engine** that processes data anywhere it lives. Define ontologies once and unlock knowledge that spans databases, warehouses, and platforms—built on the Vadalog reasoning engine.

**Key capabilities:**
- **Connect**: Query across Snowflake, Databricks, Neo4j, SQL, CSV, and more without ETL or vendor lock-in
- **Think**: Replace 100+ lines of PySpark/SQL with simple declarative logic. Power graph analytics without GraphDBs
- **Explain**: Full lineage & traceability with deterministic, repeatable results. Ground AI in structured, explainable context

Exponentially faster and simpler than traditional approaches. Learn more at [prometheux.ai](https://prometheux.ai/).

## Support

For issues, questions, or access requests:

- **Homepage**: https://www.prometheux.ai
- **PyPI**: https://pypi.org/project/prometheux-mcp/
- **Email**: davben@prometheux.co.uk, teodoro.baldazzi@prometheux.co.uk, or support@prometheux.co.uk
- **Documentation**: https://docs.prometheux.ai/mcp
- **Issues**: [GitHub Issues](https://github.com/prometheuxresearch/px-mcp-server/issues)

## Related Projects

- [Prometheux Chain](https://pypi.org/project/prometheux-chain/) — Python SDK for Prometheux
- [Vadalog Extension](https://pypi.org/project/vadalog-extension/) — JupyterLab extension for Vadalog
- [Vadalog Jupyter Kernel](https://pypi.org/project/vadalog-jupyter-kernel/) — Jupyter kernel for Vadalog