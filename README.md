# Prometheux MCP Server

[![PyPI version](https://badge.fury.io/py/prometheux-mcp.svg)](https://badge.fury.io/py/prometheux-mcp)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD%203--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that enables AI agents like Claude to interact with [Prometheux](https://prometheux.ai) ontologies and reasoning capabilities.

> **Note**: This is the **local** version, designed for Claude Desktop and other
> stdio clients. For Claude Web, use the remote MCP server.

---

## For Users

### What This Does

This package lets **Claude Desktop** work inside your Prometheux ontologies:

- Explore an ontology — its concepts, data sources, schema, and lineage
- Run concepts to derive new facts, and preview the data behind them
- Author and validate concepts of any kind: Vadalog logic, SQL, Cypher, Python,
  and the `context` and `llm` kinds that bring unstructured knowledge and model
  calls into the same lineage
- Read and write Context Layer notes, manage snapshots, and build apps
- All through natural conversation with Claude

The full set of tools comes from the backend, not from this package — see
[Available Tools](#available-tools).

### Prerequisites

- **Prometheux account** with access to a deployed instance
- **Claude Desktop** installed on your machine
- **Your authentication token** from your Prometheux account settings

### Installation

#### Option 1: Automated Install (Recommended)

The easiest way to install - download and run our installation script:

**macOS/Linux:**
```bash
curl -sSL https://raw.githubusercontent.com/prometheuxresearch/px-mcp-server/main/install.sh -o install.sh
chmod +x install.sh
./install.sh
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/prometheuxresearch/px-mcp-server/main/install.ps1" -OutFile "install.ps1"
.\install.ps1
```

The script will:
- ✅ Install `pipx` (if not already installed)
- ✅ Install `prometheux-mcp` package
- ✅ Prompt for your credentials (URL, token, username, organization)
- ✅ Automatically configure Claude Desktop
- ✅ Create backups of existing configuration

Then just restart Claude Desktop and you're ready!

#### Option 2: Manual Install Using pipx

If you prefer manual installation, use pipx to install the package in an isolated environment:

**macOS:**
```bash
brew install pipx
pipx ensurepath
pipx install prometheux-mcp
```

**Windows:**
```bash
pip install pipx
pipx ensurepath
pipx install prometheux-mcp
```

**Linux:**
```bash
pip install pipx
pipx ensurepath
pipx install prometheux-mcp
```

### Configuration

> **Note**: If you used the automated installation script (Option 1), configuration was done automatically. Skip to the "Using Prometheux with Claude" section below.

**For manual installations (Option 2):**

1. **Get your credentials** from your Prometheux account settings:
   - Server URL (e.g., `https://api.prometheux.ai`)
   - Authentication token
   - Username
   - Organization

2. **Configure Claude Desktop** by editing the config file:

   **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
   **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

   **Configuration Example:**
   ```json
   {
     "mcpServers": {
       "prometheux": {
         "command": "/Users/YOUR_USERNAME/.local/bin/prometheux-mcp",
         "args": ["--url", "https://api.prometheux.ai"],
         "env": {
           "PROMETHEUX_TOKEN": "your_token_here",
           "PROMETHEUX_USERNAME": "your_username",
           "PROMETHEUX_ORGANIZATION": "your_org"
         }
       }
     }
   }
   ```
   
   > **Finding Your Path:** Run this in your terminal to find the full path:
   > - **macOS/Linux:** `which prometheux-mcp`
   > - **Windows:** `where prometheux-mcp` (in PowerShell or Command Prompt)
   >
   > **Common paths after pipx install:**
   > - **macOS:** `/Users/YOUR_USERNAME/.local/bin/prometheux-mcp`
   > - **Windows:** `C:\\Users\\YOUR_USERNAME\\.local\\bin\\prometheux-mcp.exe` (use double backslashes in JSON)
   > - **Linux:** `/home/YOUR_USERNAME/.local/bin/prometheux-mcp`
   
   > **Note:** Username and organization are required for API routing through the gateway.
   
   > **Custom URLs:** For on-premise deployments or custom URLs, replace `https://api.prometheux.ai` with your own server URL.

3. **Restart Claude Desktop** (quit completely with Cmd+Q, then reopen)

### Usage

Once configured, just chat with Claude:

> "What concepts are available in ontology customer-analytics?"

> "Run the churn_prediction concept in ontology customer-analytics"

> "Show me the high_value_customers from ontology sales-data with min_value of 1000"

> "Write a concept that flags suppliers whose disputes are rising, and validate it before saving"

### Available Tools

This server forwards requests to your Prometheux instance, which owns the tool
catalog — so `tools/list` is the only authoritative answer to "what tools exist",
and new tools appear without a release here. Ask Claude *"what tools do you
have?"* to see the current set.

Every tool carries MCP annotations (`readOnlyHint` / `destructiveHint` /
`idempotentHint` / `openWorldHint`) so clients can warn before anything writes.
They fall into four classes:

**Read-only** — reads existing state, no side effects: `list_ontologies`,
`list_concepts`, `get_concept`, `list_data_sources`, `preview_data_source`,
`get_ontology_schema`, `list_apps`, `list_context_notes`.

**Read-only via an external or LLM service** — derives an answer but persists
nothing: `search_vadalog_docs`, `validate_concept`, `extract_concepts_from_document`.

**Write** — creates or updates state: `run_concept`, `create_concept`,
`create_ontology`, `create_ontology_snapshot`, `save_app`, `save_context_note`.

**Destructive** — overwrites or removes state: `update_concept`,
`save_ontology_schema`, `restore_snapshot`, `delete_concept`, `delete_app`,
`delete_context_note`.

> **Note:** Concept bodies are written to the `definition` parameter, whatever the
> kind — Vadalog rules, a SQL or Cypher query, a Python body, or an LLM prompt
> template. `context` concepts have no body and are configured through
> `concept_config` instead. See
> [Context and LLM concepts](https://docs.prometheux.ai/platform/context-and-llm-concepts).

### Troubleshooting

**"command not found" or "Server disconnected" errors:**

*macOS:*
1. Find the full path: `which prometheux-mcp`
2. Use that full path in your config (usually `/Users/YOUR_USERNAME/.local/bin/prometheux-mcp`)
3. If still having issues, try pipx: `pipx install prometheux-mcp`
4. Restart Claude Desktop completely (Cmd+Q, then reopen)

*Windows:*
1. Find the full path: `where prometheux-mcp` (in PowerShell or Command Prompt)
2. Use that full path in your config with double backslashes (e.g., `C:\\Users\\YOUR_USERNAME\\.local\\bin\\prometheux-mcp.exe`)
3. Restart Claude Desktop

**"Connection refused" error:**
Check that your Prometheux server URL is correct and reachable. The gateway routes
on your organization and username, and `/mcp/info` requires your token, so test
with all three:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.prometheux.ai/jarvispy/YOUR_ORG/YOUR_USERNAME/mcp/info
```

**"Authentication failed" error:**
Verify your token is correct in the config. Generate a new token from your Prometheux account settings if needed.

**Check logs:**
- **macOS:** `~/Library/Logs/Claude/mcp-server-prometheux.log`
- **Windows:** `%APPDATA%\Claude\logs\mcp-server-prometheux.log`

---

## Tool Reference

Spelled out below are the two tools you are most likely to reach for first. For
the rest, call `tools/list` — as [Available Tools](#available-tools) explains, the
backend owns the catalog, so anything written here about the others would go stale
the moment the backend adds one. Full signatures live in the
[MCP documentation](https://docs.prometheux.ai/integrations/mcp/overview).

### `list_concepts`

Lists all concepts available in an ontology.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ontology_id` | string | Yes | — | Ontology identifier |
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

Executes a concept and returns the facts it derives. Works for every concept
kind — Vadalog logic, SQL, Cypher, Python, `context` and `llm` — since the kind
determines how the concept is evaluated, not how it is called.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `ontology_id` | string | Yes | — | Ontology identifier |
| `concept_name` | string | Yes | — | Concept to execute |
| `params` | object | No | `{}` | Parameters for reasoning |
| `scope` | string | No | `"user"` | `"user"` or `"organization"` |
| `force_rerun` | boolean | No | `true` | Re-execute even if cached |
| `persist_outputs` | boolean | No | `true` | Save results to database |

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

## For Maintainers

### Releasing a New Version

Merging a version bump into `main` publishes to PyPI — see
`.github/workflows/publish.yml`. Nothing is built from a laptop, so what customers
install is always a commit that was reviewed.

```bash
# 1. Bump the version. This is the only place it lives: setup.py stamps it into
#    the package metadata, and prometheux_mcp.__version__ reads it back out.
echo "0.1.13" > version.txt

# 2. Open a PR with that change and merge it. That is the whole release.
```

The guard job compares `version.txt` against the tags that already exist, so a
merge that does not bump the version is a no-op. A merge that does bump it runs the
tests, builds, publishes, attests the artifacts, tags the commit `v0.1.13`, and
opens a GitHub Release with the SBOM and checksums attached. A version already on
PyPI fails the upload rather than being skipped quietly.

Do not push a `v*` tag by hand. Nothing listens for tags: the tag is written after
a successful upload as the record of what shipped, and it is what the guard reads
to decide whether the next merge is a release.

> **One-time PyPI setup.** The workflow authenticates with [trusted
> publishing](https://docs.pypi.org/trusted-publishers/) rather than a stored API
> token, so it must be registered once on PyPI: project `prometheux-mcp` →
> Publishing → add a GitHub publisher with owner `prometheuxresearch`, repository
> `px-mcp-server`, workflow `publish.yml`, environment `pypi`.
>
> The environment name is not optional. A trusted publisher is bound to the
> workflow filename rather than to any branch, so without it a branch carrying a
> modified `publish.yml` can mint a real publishing token. Naming `pypi` on both
> sides — and restricting that environment to `main` under Settings →
> Environments → `pypi` → deployment branch policy — is what ties a release to a
> reviewed commit. The environment has to exist before the workflow runs, or the
> publish job fails with `Missing environment 'pypi'`.

> **Pin the MCP SDK deliberately.** `install_requires` caps `mcp` below 2.0,
> because the 2.x SDK removed the low-level decorators this server is built on.
> An uncapped release resolves to 2.x on a user's fresh install and fails on
> import — silently, since it breaks on their machine and not ours. Lift the cap
> only together with a port to the 2.x server API.

Users get the new version when they run the installation script or
`pipx install prometheux-mcp`.

---

## Access to Prometheux Backend

A Prometheux instance is required to use this server — it holds your ontologies and
answers every tool call. To request access:

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
- **Documentation**: https://docs.prometheux.ai/integrations/mcp/local
- **Issues**: [GitHub Issues](https://github.com/prometheuxresearch/px-mcp-server/issues)

## Related Projects

- [Prometheux Chain](https://pypi.org/project/prometheux-chain/) — Python SDK for Prometheux
- [Vadalog Extension](https://pypi.org/project/vadalog-extension/) — JupyterLab extension for Vadalog
- [Vadalog Jupyter Kernel](https://pypi.org/project/vadalog-jupyter-kernel/) — Jupyter kernel for Vadalog