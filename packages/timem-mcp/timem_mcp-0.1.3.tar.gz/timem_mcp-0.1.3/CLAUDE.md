# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TiMEM MCP Server is a Model Context Protocol (MCP) server that provides memory management tools for TiMEM Engine. The project is built using FastMCP framework and communicates with MCP clients like Claude Desktop via stdio transport.

## Common Commands

### Development
```bash
# Install in development mode
pip install -e .

# Run directly (using Python module)
python -m timem_mcp

# Run using uvx (recommended)
uvx timem-mcp

# Debug with MCP Inspector (local)
npx @modelcontextprotocol/inspector uvx --from <your-local-path> timem-mcp -e TiMEM_API_HOST=http://localhost:8000 -e TiMEM_API_KEY=<your-api-key>
```

### Build and Publish
```bash
# Build package
python -m build

# Check package
twine check dist/*
```

### Configuration Requirements
The following environment variables are required to run the service:
- `TiMEM_API_KEY`: TiMEM Engine API Key
- `TiMEM_USER_ID`: User ID (optional)

Optional configuration:
- `TiMEM_API_HOST`: API endpoint (defaults to `https://api.timem.cloud`)

## Code Architecture

```
timem_mcp/
├── __init__.py      # Exports main entry point and version
├── __main__.py      # Entry: validate config → start MCP server (stdio)
├── server.py        # MCP core: FastMCP instance + 3 tool definitions
├── client.py        # HTTP client: async calls to TiMEM Engine API
└── config.py        # Config management: env var reading (supports TiMEM_*/TIMEM_* prefixes)
```

### Execution Flow
1. `__main__.py:main()` → validate env vars → call `mcp.run(transport="stdio")`
2. `server.py` uses FastMCP decorators to register tool functions
3. Tool functions call TiMEM Engine API via `client.py:call_api()`
4. API paths retrieved from `config.py:Config` constants: `MEMORY_CREATE_PATH` / `MEMORY_QUERY_PATH`
5. Configuration retrieved from `config.py` getters: `get_api_key()` / `get_user_id()` / `get_base_url()`

### MCP Tools
| Tool | Purpose | API Endpoint |
|------|---------|--------------|
| `create_memory` | Create memories from conversation history | POST `/api/v1/memory/` |
| `search_memories` | Search stored memories | GET `/api/v1/memory/query` |
| `ready` | Health check | - |

## Key Design Points

- **Environment variable prefix priority**: `TiMEM_*` > `TIMEM_*` (implemented in `config.py:Config._get_env`)
- **API authentication**: Via `X-API-Key` request header (`client.py:call_api`)
- **Response format handling**: `create_memory` wraps list responses as `{"status": "success", "memories": [...], "count": n}` (`server.py:70-72`)
- **Transport mode**: MCP standard requires `stdio` transport, not HTTP

## Notes

- Project uses `pyproject.toml` for dependency management, not `requirements.txt`
- `timem_mcp_service.py` in root directory is a legacy file; use code in `timem_mcp/` package
- PyPI package name is `timem-mcp`, but Python import name is `timem_mcp` (follows Python convention)
