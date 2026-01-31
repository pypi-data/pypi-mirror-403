# Data Model: Cisco IOS Query Tool

**Feature**: 001-cisco-ios-query
**Date**: 2026-01-30

## Entity Overview

```
┌─────────────────────┐     ┌─────────────────────┐
│  CiscoCredentials   │     │    QueryRequest     │
│  (from env vars)    │     │  (tool parameters)  │
└─────────────────────┘     └─────────────────────┘
         │                           │
         └───────────┬───────────────┘
                     ▼
         ┌─────────────────────┐
         │   cisco_ios_query   │
         │      (tool)         │
         └─────────────────────┘
                     │
                     ▼
         ┌─────────────────────┐
         │   QueryResponse     │
         │   (reused model)    │
         └─────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌───────────┐ ┌───────────┐ ┌───────────┐
│DeviceInfo │ │CommandResult│ │ ErrorInfo │
│ (reused)  │ │  (reused)  │ │ (reused)  │
└───────────┘ └───────────┘ └───────────┘
```

## New Entity: CiscoCredentials

**Purpose**: Load and validate Cisco device credentials from environment variables.

**Location**: `src/mcp_network_jcd/models/cisco.py`

### Fields

| Field | Type | Required | Source | Validation |
|-------|------|----------|--------|------------|
| username | str | Yes | CISCO_USERNAME env var | min_length=1 |
| password | str | Yes | CISCO_PASSWORD env var | min_length=1, repr=False |
| enable_password | str \| None | No | CISCO_ENABLE_PASSWORD env var | min_length=1 if provided, repr=False |

### Class Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| from_env | `() -> CiscoCredentials` | Load from environment; raises ValueError if required vars missing |

### Pydantic Model Definition

```python
class CiscoCredentials(BaseModel):
    """Credentials loaded from environment variables for Cisco devices."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1, repr=False)
    enable_password: str | None = Field(default=None, repr=False)

    @field_validator("enable_password")
    @classmethod
    def validate_enable_password(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            return None  # Treat empty string as None
        return v.strip() if v else None

    @classmethod
    def from_env(cls) -> "CiscoCredentials":
        username = os.environ.get("CISCO_USERNAME", "")
        password = os.environ.get("CISCO_PASSWORD", "")
        enable_password = os.environ.get("CISCO_ENABLE_PASSWORD")

        if not username:
            raise ValueError("CISCO_USERNAME must be set")
        if not password:
            raise ValueError("CISCO_PASSWORD must be set")

        return cls(
            username=username,
            password=password,
            enable_password=enable_password if enable_password else None,
        )
```

## Reused Entities (from paloalto.py)

These models are reused without modification to ensure consistent response format.

### DeviceInfo

| Field | Type | Description |
|-------|------|-------------|
| host | str | Device hostname or IP |
| port | int | SSH port |

### CommandResult

| Field | Type | Description |
|-------|------|-------------|
| command | str | Executed command string |
| success | bool | Whether command succeeded |
| output | str \| None | Command output (on success) |
| error | str \| None | Error message (on failure) |
| duration_ms | int | Execution time in milliseconds |

**Validation**: Failed commands (success=False) must have error message.

### ErrorInfo

| Field | Type | Description |
|-------|------|-------------|
| code | str | Error code (CONFIG_ERROR, AUTH_FAILED, etc.) |
| message | str | Human-readable error description |

### QueryResponse

| Field | Type | Description |
|-------|------|-------------|
| success | bool | Overall query success |
| device | DeviceInfo | Target device info |
| results | list[CommandResult] \| None | Command results (on success) |
| error | ErrorInfo \| None | Error info (on failure) |
| total_duration_ms | int | Total query time in milliseconds |
| timestamp | str | ISO 8601 timestamp |

## Validation Rules Summary

### Input Validation (QueryRequest equivalent)

| Parameter | Rule |
|-----------|------|
| host | Non-empty string, whitespace trimmed |
| port | Integer 1-65535, default 22 |
| timeout | Integer 1-300, default 30 |
| commands | List of 1-10 non-empty strings |

### Credential Validation

| Env Var | Rule |
|---------|------|
| CISCO_USERNAME | Required, non-empty |
| CISCO_PASSWORD | Required, non-empty |
| CISCO_ENABLE_PASSWORD | Optional, treated as None if empty |

## State Transitions

```
Query Lifecycle:
┌─────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐
│ Receive │───►│   Validate  │───►│   Connect   │───►│ Execute  │
│ Request │    │   Inputs    │    │    SSH      │    │ Commands │
└─────────┘    └─────────────┘    └─────────────┘    └──────────┘
                     │                   │                  │
                     ▼                   ▼                  ▼
               [Validation Error]  [Connection Error]  [Partial/Full Results]
                     │                   │                  │
                     └───────────────────┴──────────────────┘
                                         │
                                         ▼
                              ┌─────────────────────┐
                              │   Return Response   │
                              │   (QueryResponse)   │
                              └─────────────────────┘
```

## Import Strategy

To reuse models from paloalto.py in cisco.py:

```python
# In tools/cisco.py
from mcp_network_jcd.models.paloalto import (
    CommandResult,
    DeviceInfo,
    ErrorInfo,
    QueryResponse,
)
from mcp_network_jcd.models.cisco import CiscoCredentials
```

This maintains a single source of truth for shared response models.
