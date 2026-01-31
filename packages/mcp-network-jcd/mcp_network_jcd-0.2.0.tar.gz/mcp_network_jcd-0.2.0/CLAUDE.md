# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MCP server for querying Palo Alto firewalls via SSH. Uses FastMCP (official Python SDK) with netmiko for SSH connections. Read-only tool for Claude Desktop integration.

## Commands

```bash
# Install (development mode)
pip install -e ".[dev]"

# Run tests
pytest

# Run single test file
pytest tests/unit/test_models.py

# Run single test
pytest tests/unit/test_models.py::TestQueryRequest::test_valid_request

# Lint
ruff check .

# Fix lint issues
ruff check . --fix
```

## Architecture

```
src/mcp_network_jcd/
├── server.py          # FastMCP entry point, registers tools
├── models/
│   └── paloalto.py    # Pydantic models (QueryRequest, QueryResponse, CommandResult)
└── tools/
    └── paloalto.py    # paloalto_query() - SSH connection and command execution
```

**Data Flow**: `server.py` → `tools/paloalto.py` → netmiko SSH → PAN-OS device

**Credentials**: Loaded from environment variables `PALOALTO_USERNAME` and `PALOALTO_PASSWORD` via `ServerCredentials.from_env()` in models. Never passed as tool parameters.

## Test Organization

- `tests/unit/` - Pydantic model validation
- `tests/contract/` - Tool API contracts, error codes, partial failure handling
- `tests/integration/` - netmiko SSH mocking

## Key Patterns

- **Error Codes**: CONFIG_ERROR, AUTH_FAILED, CONNECTION_TIMEOUT, CONNECTION_REFUSED, UNKNOWN_ERROR
- **Partial Failure**: If SSH drops mid-batch, returns partial results (success=True with failed commands)
- **Validation Limits**: 1-10 commands per request, port 1-65535, timeout 1-300s

## Active Technologies
- Python 3.12 + FastMCP (mcp>=1.0.0), netmiko>=4.0.0, pydantic>=2.0.0 (001-cisco-ios-query)
- N/A (stateless tool) (001-cisco-ios-query)

## Recent Changes
- 001-cisco-ios-query: Added Python 3.12 + FastMCP (mcp>=1.0.0), netmiko>=4.0.0, pydantic>=2.0.0
