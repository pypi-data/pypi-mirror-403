# Quickstart: Cisco IOS Query Tool Implementation

**Feature**: 001-cisco-ios-query
**Date**: 2026-01-30

## TL;DR

Add `cisco_ios_query` tool following the existing `paloalto_query` pattern:
1. Create `models/cisco.py` with `CiscoCredentials`
2. Create `tools/cisco.py` with `cisco_ios_query()`
3. Register tool in `server.py`

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `src/mcp_network_jcd/models/cisco.py` | CiscoCredentials model |
| `src/mcp_network_jcd/tools/cisco.py` | cisco_ios_query function |
| `tests/unit/test_cisco_models.py` | Credential validation tests |
| `tests/contract/test_cisco_tool.py` | Tool contract tests |
| `tests/integration/test_cisco_ssh.py` | netmiko mock tests |

### Modified Files

| File | Change |
|------|--------|
| `src/mcp_network_jcd/server.py` | Import and register cisco_ios_query_tool |

## Implementation Order (TDD)

### Step 1: CiscoCredentials Model

**Test First** (`tests/unit/test_cisco_models.py`):
```python
def test_credentials_from_env_success(monkeypatch):
    monkeypatch.setenv("CISCO_USERNAME", "admin")
    monkeypatch.setenv("CISCO_PASSWORD", "secret")
    creds = CiscoCredentials.from_env()
    assert creds.username == "admin"

def test_credentials_missing_username_raises(monkeypatch):
    monkeypatch.delenv("CISCO_USERNAME", raising=False)
    with pytest.raises(ValueError, match="CISCO_USERNAME"):
        CiscoCredentials.from_env()

def test_enable_password_optional(monkeypatch):
    monkeypatch.setenv("CISCO_USERNAME", "admin")
    monkeypatch.setenv("CISCO_PASSWORD", "secret")
    # No CISCO_ENABLE_PASSWORD set
    creds = CiscoCredentials.from_env()
    assert creds.enable_password is None
```

**Then Implement** (`src/mcp_network_jcd/models/cisco.py`):
```python
class CiscoCredentials(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1, repr=False)
    enable_password: str | None = Field(default=None, repr=False)

    @classmethod
    def from_env(cls) -> "CiscoCredentials":
        # Load from CISCO_* env vars
```

### Step 2: Tool Contract Tests

**Test First** (`tests/contract/test_cisco_tool.py`):
```python
def test_returns_success_response_structure(mock_ssh):
    result = cisco_ios_query("host", ["show version"])
    assert "success" in result
    assert "device" in result
    assert "results" in result
    assert "total_duration_ms" in result

def test_config_error_on_missing_credentials(monkeypatch):
    monkeypatch.delenv("CISCO_USERNAME", raising=False)
    result = cisco_ios_query("host", ["show version"])
    assert result["success"] is False
    assert result["error"]["code"] == "CONFIG_ERROR"
```

### Step 3: Tool Implementation

**Implement** (`src/mcp_network_jcd/tools/cisco.py`):
```python
def cisco_ios_query(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    # Follow paloalto.py pattern
    # Use device_type="cisco_ios"
    # Handle enable password if set
```

### Step 4: Integration Tests

**Test** (`tests/integration/test_cisco_ssh.py`):
```python
def test_enable_mode_called_when_password_set(mock_netmiko, monkeypatch):
    monkeypatch.setenv("CISCO_ENABLE_PASSWORD", "enablesecret")
    cisco_ios_query("host", ["show running-config"])
    mock_netmiko.return_value.enable.assert_called_once()

def test_enable_mode_not_called_when_no_password(mock_netmiko, monkeypatch):
    monkeypatch.delenv("CISCO_ENABLE_PASSWORD", raising=False)
    cisco_ios_query("host", ["show version"])
    mock_netmiko.return_value.enable.assert_not_called()
```

### Step 5: Server Registration

**Modify** (`src/mcp_network_jcd/server.py`):
```python
from mcp_network_jcd.tools.cisco import cisco_ios_query

@mcp.tool()
def cisco_ios_query_tool(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    """Query Cisco IOS device via SSH. Creds from env: CISCO_USERNAME, CISCO_PASSWORD, CISCO_ENABLE_PASSWORD (optional)..."""
    return cisco_ios_query(host=host, commands=commands, port=port, timeout=timeout)
```

## Key Differences from Palo Alto Tool

| Aspect | Palo Alto | Cisco |
|--------|-----------|-------|
| Device type | `paloalto_panos` | `cisco_ios` |
| Env vars | `PALOALTO_*` | `CISCO_*` |
| Enable password | N/A | Optional `CISCO_ENABLE_PASSWORD` |
| Enable mode | Not needed | Call `connection.enable()` if password set |

## Verification Commands

```bash
# Run all tests
pytest

# Run only Cisco tests
pytest tests/ -k cisco

# Lint check
ruff check src/mcp_network_jcd/models/cisco.py src/mcp_network_jcd/tools/cisco.py
```

## Environment Setup for Testing

```bash
export CISCO_USERNAME="testuser"
export CISCO_PASSWORD="testpass"
export CISCO_ENABLE_PASSWORD="enablepass"  # Optional
```
