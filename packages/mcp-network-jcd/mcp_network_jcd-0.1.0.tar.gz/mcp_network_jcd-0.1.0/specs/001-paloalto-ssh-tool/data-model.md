# Data Model: Palo Alto SSH Query Tool

**Date**: 2026-01-30
**Feature**: 001-paloalto-ssh-tool

## Overview

This feature is stateless - no persistent data storage. All entities exist only for the duration
of a single MCP tool request. Models are implemented using Pydantic for validation.

**Credentials**: Username and password are NOT passed as tool parameters. They are read from
environment variables (`PALOALTO_USERNAME`, `PALOALTO_PASSWORD`) configured in mcp.json.

## Entities

### ServerCredentials

Credentials loaded from environment variables at server startup.

| Field | Type | Source | Validation |
|-------|------|--------|------------|
| username | string | `PALOALTO_USERNAME` env var | Non-empty, required |
| password | string | `PALOALTO_PASSWORD` env var | Non-empty, required |

**Pydantic Model**:
```python
import os
from pydantic import BaseModel, Field, field_validator

class ServerCredentials(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1, repr=False)  # Never log

    @classmethod
    def from_env(cls) -> "ServerCredentials":
        username = os.environ.get("PALOALTO_USERNAME", "")
        password = os.environ.get("PALOALTO_PASSWORD", "")
        if not username or not password:
            raise ValueError("PALOALTO_USERNAME and PALOALTO_PASSWORD must be set")
        return cls(username=username, password=password)
```

### DeviceConnection

Connection parameters for a Palo Alto device (tool input parameters only).

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| host | string | Yes | - | Non-empty, valid hostname or IP |
| port | integer | No | 22 | Range: 1-65535 |
| timeout | integer | No | 30 | Range: 1-300 seconds |

**Pydantic Model**:
```python
class DeviceConnection(BaseModel):
    host: str = Field(..., min_length=1, description="Device hostname or IP address")
    port: int = Field(default=22, ge=1, le=65535, description="SSH port")
    timeout: int = Field(default=30, ge=1, le=300, description="Connection timeout in seconds")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Host cannot be empty or whitespace")
        return v.strip()
```

### QueryRequest

User request containing connection info and commands (MCP tool input).

| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| host | string | Yes | - | Non-empty |
| port | integer | No | 22 | Range: 1-65535 |
| commands | list[string] | Yes | - | 1-10 non-empty commands |
| timeout | integer | No | 30 | Range: 1-300 seconds |

**Pydantic Model**:
```python
class QueryRequest(BaseModel):
    host: str = Field(..., min_length=1)
    port: int = Field(default=22, ge=1, le=65535)
    commands: list[str] = Field(..., min_length=1, max_length=10)
    timeout: int = Field(default=30, ge=1, le=300)

    @field_validator("commands")
    @classmethod
    def validate_commands(cls, v: list[str]) -> list[str]:
        validated = []
        for cmd in v:
            if not cmd.strip():
                raise ValueError("Commands cannot be empty or whitespace")
            validated.append(cmd.strip())
        return validated
```

### CommandResult

Result of executing a single command.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| command | string | Yes | The executed command |
| success | boolean | Yes | Whether command executed successfully |
| output | string | Conditional | Command output (present if any output received) |
| error | string | Conditional | Error message (if success=false) |
| duration_ms | integer | Yes | Execution time in milliseconds |

**Partial Result Handling**: If SSH connection is interrupted mid-command, the result will have
`success: false` with whatever partial `output` was received before disconnection, plus an `error`
message describing the interruption. Both `output` and `error` can be present simultaneously in
this case.

**Pydantic Model**:
```python
class CommandResult(BaseModel):
    command: str
    success: bool
    output: str | None = None
    error: str | None = None
    duration_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def check_output_or_error(self) -> "CommandResult":
        # Failed commands must have error message
        if not self.success and self.error is None:
            raise ValueError("Failed command must have error message")
        return self
```

### QueryResponse

Complete response for a query request.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| success | boolean | Yes | Overall query success |
| device | object | Yes | Device info (host, port only - no credentials) |
| results | list[CommandResult] | Conditional | Command results (if success=true) |
| error | object | Conditional | Error info (if success=false at connection level) |
| total_duration_ms | integer | Yes | Total query time |
| timestamp | string | Yes | ISO 8601 timestamp |

**Pydantic Model**:
```python
from datetime import datetime, timezone

class DeviceInfo(BaseModel):
    host: str
    port: int

class ErrorInfo(BaseModel):
    code: str  # e.g., "CONNECTION_TIMEOUT", "AUTH_FAILED"
    message: str

class QueryResponse(BaseModel):
    success: bool
    device: DeviceInfo
    results: list[CommandResult] | None = None
    error: ErrorInfo | None = None
    total_duration_ms: int = Field(ge=0)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))
```

## Error Codes

| Code | Description | HTTP-like Equivalent |
|------|-------------|---------------------|
| CONNECTION_TIMEOUT | Device unreachable | 504 Gateway Timeout |
| AUTH_FAILED | Invalid credentials | 401 Unauthorized |
| CONNECTION_REFUSED | SSH connection refused | 502 Bad Gateway |
| COMMAND_FAILED | Command execution error | 500 Internal Error |
| VALIDATION_ERROR | Invalid input parameters | 400 Bad Request |
| CONFIG_ERROR | Missing environment variables | 500 Internal Error |
| UNKNOWN_ERROR | Unexpected error | 500 Internal Error |

## Entity Relationships

```
ServerCredentials (singleton, from env vars)
     |
     v
QueryRequest (tool params: host, port, commands, timeout)
     |
     +-- DeviceConnection (host, port, timeout)
     +-- commands (1:N strings)

QueryResponse
├── DeviceInfo (1:1, host/port only)
├── CommandResult (1:N, one per command)
└── ErrorInfo (0:1, connection-level errors only)
```

## Data Flow

```
[mcp.json env vars] --> ServerCredentials (at startup)
                              |
[MCP Client] --> QueryRequest |
                    |         |
                    v         v
              [MCP Server combines]
                    |
                    v
              [netmiko SSH with credentials]
                    |
                    v
              CommandResult[]
                    |
                    v
              QueryResponse --> [MCP Client]
```

## Security Considerations

1. **Credentials in env vars**: Never passed in tool parameters, never logged
2. **ServerCredentials**: Uses `repr=False` to prevent accidental logging
3. **DeviceInfo**: Excludes credentials - only host/port exposed in responses
4. **Error messages**: Generic messages, no credential details leaked
5. **mcp.json**: Credentials configured once, not exposed per-request
