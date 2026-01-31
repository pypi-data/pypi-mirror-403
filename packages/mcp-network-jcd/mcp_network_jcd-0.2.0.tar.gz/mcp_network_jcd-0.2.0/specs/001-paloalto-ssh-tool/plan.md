# Implementation Plan: Palo Alto SSH Query Tool

**Branch**: `001-paloalto-ssh-tool` | **Date**: 2026-01-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-paloalto-ssh-tool/spec.md`

## Summary

Build an MCP server exposing a single tool for querying Palo Alto firewalls (any PAN-OS device)
via SSH. The tool accepts connection parameters and commands, executes them using netmiko, and
returns structured JSON responses. Password-only authentication, no host key verification.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: mcp (official Python SDK with FastMCP), netmiko (SSH to network devices)
**Storage**: N/A (stateless, no persistence)
**Testing**: pytest, pytest-asyncio
**Target Platform**: Linux server (MCP server process)
**Project Type**: Single project
**Performance Goals**: Response within 30 seconds per device query
**Constraints**: Read-only operations, no credential storage/logging
**Scale/Scope**: Single device queries, batch up to 10 commands per request

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. MCP Protocol Compliance | ✅ PASS | Tool exposed via FastMCP, JSON input/output, MCP error responses |
| II. Test-First Development | ✅ PLANNED | Tests will be written before implementation per TDD cycle |
| III. Simplicity | ✅ PASS | Single tool, minimal abstractions, netmiko handles SSH complexity |

## Project Structure

### Documentation (this feature)

```text
specs/001-paloalto-ssh-tool/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schema)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── mcp_network_jcd/
│   ├── __init__.py
│   ├── server.py           # FastMCP server entry point
│   ├── tools/
│   │   ├── __init__.py
│   │   └── paloalto.py     # Palo Alto query tool implementation
│   └── models/
│       ├── __init__.py
│       └── paloalto.py     # Pydantic models for request/response

tests/
├── conftest.py             # Shared fixtures (mock devices, etc.)
├── contract/
│   └── test_paloalto_tool.py  # MCP tool contract tests
├── integration/
│   └── test_paloalto_ssh.py   # Integration tests with netmiko
└── unit/
    └── test_models.py         # Model validation tests
```

**Structure Decision**: Single project layout. MCP server with modular tool organization under
`src/mcp_network_jcd/`. Tools separated for future extensibility (other network device types).

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | - | - |
