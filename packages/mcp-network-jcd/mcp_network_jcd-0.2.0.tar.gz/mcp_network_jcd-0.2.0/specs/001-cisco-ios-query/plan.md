# Implementation Plan: Cisco IOS Query Tool

**Branch**: `001-cisco-ios-query` | **Date**: 2026-01-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-cisco-ios-query/spec.md`

## Summary

Add a `cisco_ios_query` MCP tool to query Cisco IOS/IOS-XE devices via SSH. The tool mirrors the existing `paloalto_query` tool pattern: accepts host, commands (1-10), port, and timeout parameters; loads credentials from environment variables (CISCO_USERNAME, CISCO_PASSWORD, optional CISCO_ENABLE_PASSWORD); returns structured JSON responses with command results and timing. Uses netmiko with `cisco_ios` device type for SSH connectivity.

## Technical Context

**Language/Version**: Python 3.12
**Primary Dependencies**: FastMCP (mcp>=1.0.0), netmiko>=4.0.0, pydantic>=2.0.0
**Storage**: N/A (stateless tool)
**Testing**: pytest with pytest-mock for SSH mocking
**Target Platform**: Linux server (MCP server for Claude Desktop)
**Project Type**: Single project (extends existing MCP server)
**Performance Goals**: Command execution within configured timeout (default 30s)
**Constraints**: 1-10 commands per request, timeout 1-300s, port 1-65535
**Scale/Scope**: Single device queries, read-only commands

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. MCP Protocol Compliance ✅

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Structured input via MCP tool parameters | ✅ Pass | Tool accepts host, commands, port, timeout as typed parameters |
| Structured JSON output | ✅ Pass | Returns QueryResponse model serialized to dict |
| Errors through MCP error responses | ✅ Pass | Error codes (AUTH_FAILED, CONNECTION_TIMEOUT, etc.) in structured response |
| Independently callable (no external state) | ✅ Pass | Each call is stateless; credentials from env vars |

### II. Test-First Development (NON-NEGOTIABLE) ✅

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Tests written before implementation | ✅ Planned | TDD workflow in tasks will enforce red-green-refactor |
| Unit tests for data transformations | ✅ Planned | Model validation tests (CiscoCredentials, QueryRequest) |
| Contract tests for MCP tool | ✅ Planned | Tool parameter validation, response structure |
| Integration tests for SSH | ✅ Planned | netmiko mock tests for connection/command flows |

### III. Simplicity ✅

| Requirement | Status | Evidence |
|-------------|--------|----------|
| No speculative features | ✅ Pass | Only implementing spec requirements |
| Prefer composition | ✅ Pass | Reusing existing response models (QueryResponse, CommandResult) |
| Avoid premature abstraction | ✅ Pass | Cisco-specific module, not generic "network device" abstraction |
| YAGNI compliance | ✅ Pass | No config mode, no NX-OS/IOS-XR support (out of scope) |

**Pre-Design Gate: PASS**

## Project Structure

### Documentation (this feature)

```text
specs/001-cisco-ios-query/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/mcp_network_jcd/
├── __init__.py
├── server.py            # FastMCP entry point (add cisco_ios_query_tool)
├── models/
│   ├── __init__.py
│   ├── paloalto.py      # Existing Palo Alto models
│   └── cisco.py         # NEW: CiscoCredentials model
└── tools/
    ├── __init__.py
    ├── paloalto.py      # Existing Palo Alto tool
    └── cisco.py         # NEW: cisco_ios_query function

tests/
├── conftest.py
├── unit/
│   ├── __init__.py
│   ├── test_models.py           # Existing + NEW: Cisco model tests
│   └── test_cisco_models.py     # NEW: CiscoCredentials validation
├── contract/
│   ├── __init__.py
│   ├── test_paloalto_tool.py    # Existing
│   └── test_cisco_tool.py       # NEW: cisco_ios_query contract tests
└── integration/
    ├── __init__.py
    ├── test_paloalto_ssh.py     # Existing
    └── test_cisco_ssh.py        # NEW: netmiko mock tests for Cisco
```

**Structure Decision**: Extends existing single-project structure. New Cisco module in `models/cisco.py` and `tools/cisco.py` following established patterns. Reuses shared models (QueryResponse, CommandResult, DeviceInfo, ErrorInfo) from paloalto.py where applicable.

## Complexity Tracking

> No constitution violations. Design follows existing patterns with minimal additions.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Separate cisco.py module | Yes | Cisco-specific credentials (enable password) and device_type differ from Palo Alto |
| Reuse QueryResponse model | Yes | Same response structure; no need for Cisco-specific response model |
| Separate CiscoCredentials | Yes | Different env vars (CISCO_*) and optional enable_password field |

## Post-Design Constitution Re-Check

*Performed after Phase 1 design completion.*

### I. MCP Protocol Compliance ✅ (Confirmed)

- Tool contract in `contracts/cisco_ios_query.md` defines structured input/output
- Response schema matches existing paloalto_query pattern
- Error codes documented with clear triggers

### II. Test-First Development ✅ (Ready)

- `quickstart.md` provides TDD implementation order
- Test examples provided for each phase (unit → contract → integration)
- Red-green-refactor workflow documented

### III. Simplicity ✅ (Confirmed)

- Data model reuses 4 existing models (QueryResponse, CommandResult, DeviceInfo, ErrorInfo)
- Only 1 new model required (CiscoCredentials)
- No unnecessary abstractions introduced
- Implementation follows existing patterns exactly

**Post-Design Gate: PASS**

## Generated Artifacts

| Artifact | Status | Path |
|----------|--------|------|
| research.md | ✅ Complete | [research.md](research.md) |
| data-model.md | ✅ Complete | [data-model.md](data-model.md) |
| contracts/ | ✅ Complete | [contracts/cisco_ios_query.md](contracts/cisco_ios_query.md) |
| quickstart.md | ✅ Complete | [quickstart.md](quickstart.md) |
| tasks.md | ✅ Complete | [tasks.md](tasks.md) |
