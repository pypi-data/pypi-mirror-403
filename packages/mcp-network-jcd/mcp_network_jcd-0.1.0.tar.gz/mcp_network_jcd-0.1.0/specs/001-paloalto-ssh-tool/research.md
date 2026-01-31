# Research: Palo Alto SSH Query Tool

**Date**: 2026-01-30
**Feature**: 001-paloalto-ssh-tool

## Technology Decisions

### 1. SSH Library: netmiko

**Decision**: Use netmiko for SSH connections to Palo Alto devices.

**Rationale**:
- Native support for Palo Alto PAN-OS via `device_type="paloalto_panos"`
- Handles PAN-OS CLI quirks (prompt patterns, command responses)
- Built-in exception classes for timeout and authentication errors
- Widely used in network automation, well-maintained

**Alternatives Considered**:
- **paramiko**: Lower-level SSH library. Requires manual handling of PAN-OS interactive shell
  behavior. More code, more bugs. Rejected.
- **pan-python**: Palo Alto's official library. Uses XML API, not CLI/SSH. Different use case
  (API-based automation). Rejected for this requirement.

**Key netmiko Parameters**:
```python
{
    "device_type": "paloalto_panos",
    "host": "<ip_or_hostname>",
    "port": 22,  # default
    "username": "<user>",
    "password": "<password>",
    "timeout": 30,  # connection timeout
    "session_timeout": 60,  # read timeout
}
```

**Host Key Verification** (FR-010): Set via `AutoAddPolicy()` or disable with netmiko's
default behavior. Use `set_missing_host_key_policy(paramiko.AutoAddPolicy())` internally.

### 2. MCP Server Framework: FastMCP (official SDK)

**Decision**: Use `mcp.server.fastmcp.FastMCP` from the official MCP Python SDK.

**Rationale**:
- Official implementation, incorporated into MCP SDK in 2024
- Decorator-based tool definition (`@mcp.tool()`)
- Handles protocol compliance, serialization, error responses
- Supports both stdio and HTTP transports

**Alternatives Considered**:
- **Custom MCP implementation**: Unnecessary complexity. Violates Simplicity principle.
- **Third-party MCP libraries**: Less maintained than official SDK. Rejected.

**FastMCP Pattern**:
```python
import os
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("MCP Network JCD")

# Credentials from environment variables (configured in mcp.json)
USERNAME = os.environ["PALOALTO_USERNAME"]
PASSWORD = os.environ["PALOALTO_PASSWORD"]

@mcp.tool()
def paloalto_query(host: str, commands: list[str], port: int = 22, timeout: int = 30) -> dict:
    """Query a Palo Alto firewall via SSH. Credentials from env vars."""
    # Use USERNAME, PASSWORD from module scope
    return {"results": [...]}
```

### 3. Credential Management

**Decision**: Credentials via environment variables, NOT tool parameters.

**Rationale**:
- Security: Credentials not exposed in MCP tool calls or logs
- Simplicity: Single configuration point in mcp.json
- Standard pattern: MCP servers commonly use env vars for secrets

**Environment Variables**:
| Variable | Description |
|----------|-------------|
| `PALOALTO_USERNAME` | SSH username for all device connections |
| `PALOALTO_PASSWORD` | SSH password for all device connections |

**mcp.json Configuration**:
```json
{
  "mcpServers": {
    "mcp-network-jcd": {
      "command": "python",
      "args": ["-m", "mcp_network_jcd.server"],
      "env": {
        "PALOALTO_USERNAME": "readonly",
        "PALOALTO_PASSWORD": "secret"
      }
    }
  }
}
```

### 3. Error Handling Strategy

**Decision**: Map netmiko exceptions to MCP error responses with user-friendly messages.

**Exception Mapping**:

| netmiko Exception | MCP Error Message | User Action |
|-------------------|-------------------|-------------|
| `NetMikoTimeoutException` | "Device unreachable: connection timed out" | Check network connectivity |
| `NetMikoAuthenticationException` | "Authentication failed: invalid credentials" | Verify username/password |
| `SSHException` | "SSH connection refused" | Check device SSH config |
| Generic `Exception` | "Unexpected error during query" | Contact support |

**Credential Security**: Never include credentials in error messages or logs.

### 4. Response Structure

**Decision**: Return structured JSON with command results and metadata.

**Response Format**:
```json
{
  "success": true,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "results": [
    {
      "command": "show system info",
      "success": true,
      "output": "hostname: fw01\nserial: 0123456789\n...",
      "duration_ms": 1234
    }
  ],
  "total_duration_ms": 2345,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

**Error Response Format**:
```json
{
  "success": false,
  "error": {
    "code": "CONNECTION_TIMEOUT",
    "message": "Device unreachable: connection timed out after 30 seconds"
  },
  "device": {
    "host": "192.168.1.1",
    "port": 22
  }
}
```

### 5. Testing Strategy

**Decision**: Three-tier testing aligned with constitution requirements.

| Test Type | Scope | Mock Strategy |
|-----------|-------|---------------|
| Unit | Model validation, error mapping | No mocks needed |
| Contract | MCP tool interface | Mock netmiko `ConnectHandler` |
| Integration | Full SSH flow | Real device OR mock SSH server |

**Contract Test Pattern**:
```python
@pytest.fixture
def mock_connect_handler(mocker):
    mock = mocker.patch("netmiko.ConnectHandler")
    mock.return_value.send_command.return_value = "hostname: test-fw"
    return mock

@pytest.fixture
def mock_credentials(monkeypatch):
    monkeypatch.setenv("PALOALTO_USERNAME", "testuser")
    monkeypatch.setenv("PALOALTO_PASSWORD", "testpass")

def test_paloalto_query_returns_structured_response(mock_connect_handler, mock_credentials):
    result = paloalto_query(host="1.1.1.1", commands=["show system info"])
    assert result["success"] is True
    assert len(result["results"]) == 1
```

## Dependencies

### Python Packages

```text
# requirements.txt
mcp>=1.0.0           # Official MCP Python SDK (includes FastMCP)
netmiko>=4.0.0       # SSH to network devices
pydantic>=2.0.0      # Data validation (may be included with mcp)

# Development
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-mock>=3.12.0
```

### PAN-OS CLI Commands Reference

Common read-only commands for testing:
- `show system info` - Device info (hostname, serial, version)
- `show interface all` - Interface status
- `show routing route` - Routing table
- `show running security-policy` - Security rules
- `show session all` - Active sessions

## Open Questions (Resolved)

| Question | Resolution |
|----------|------------|
| SSH host key verification | Skip verification (FR-010) |
| Authentication method | Password only (Clarification) |
| Device scope | Any PAN-OS device (Clarification) |
