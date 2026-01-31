# MCP Tool Contract: cisco_ios_query

**Feature**: 001-cisco-ios-query
**Date**: 2026-01-30
**Protocol**: Model Context Protocol (MCP)

## Tool Registration

```python
@mcp.tool()
def cisco_ios_query_tool(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    """Query Cisco IOS device via SSH."""
```

## Input Parameters

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| host | string | Yes | - | min_length: 1, trimmed | Device hostname or IP address |
| commands | array[string] | Yes | - | min: 1, max: 10 items, each non-empty | Cisco IOS CLI commands to execute |
| port | integer | No | 22 | min: 1, max: 65535 | SSH port |
| timeout | integer | No | 30 | min: 1, max: 300 | Connection timeout in seconds |

### Input Validation Errors

```json
{
  "success": false,
  "device": {"host": "", "port": 22},
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Host cannot be empty"
  },
  "total_duration_ms": 0,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

## Output Schema

### Success Response

```json
{
  "success": true,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "results": [
    {
      "command": "show version",
      "success": true,
      "output": "Cisco IOS Software, Version 15.1...",
      "error": null,
      "duration_ms": 245
    },
    {
      "command": "show ip interface brief",
      "success": true,
      "output": "Interface              IP-Address...",
      "error": null,
      "duration_ms": 180
    }
  ],
  "error": null,
  "total_duration_ms": 1250,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

### Error Response (Connection Level)

```json
{
  "success": false,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "results": null,
  "error": {
    "code": "AUTH_FAILED",
    "message": "Authentication failed: invalid credentials"
  },
  "total_duration_ms": 1500,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

### Partial Failure Response

```json
{
  "success": true,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "results": [
    {
      "command": "show version",
      "success": true,
      "output": "Cisco IOS Software...",
      "error": null,
      "duration_ms": 245
    },
    {
      "command": "show running-config",
      "success": false,
      "output": null,
      "error": "Connection lost during command: OSError",
      "duration_ms": 5000
    }
  ],
  "error": null,
  "total_duration_ms": 5500,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

## Error Codes

| Code | HTTP Equivalent | Trigger | Message Pattern |
|------|-----------------|---------|-----------------|
| CONFIG_ERROR | 500 | CISCO_USERNAME or CISCO_PASSWORD not set | "CISCO_USERNAME and CISCO_PASSWORD must be set: {detail}" |
| AUTH_FAILED | 401 | SSH auth failed or enable password rejected | "Authentication failed: invalid credentials" or "Enable authentication failed" |
| CONNECTION_TIMEOUT | 504 | Device unreachable within timeout | "Device unreachable: connection timed out after {timeout} seconds" |
| CONNECTION_REFUSED | 502 | SSH port closed or filtered | "SSH connection refused by device" |
| UNKNOWN_ERROR | 500 | Unexpected exception | "Unexpected error: {exception_type}" |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| CISCO_USERNAME | Yes | SSH username for Cisco device |
| CISCO_PASSWORD | Yes | SSH password for Cisco device |
| CISCO_ENABLE_PASSWORD | No | Enable mode password (if required) |

## Behavioral Contract

### Connection Flow

1. Load credentials from environment variables
2. Validate input parameters
3. Establish SSH connection using netmiko `cisco_ios` device type
4. If CISCO_ENABLE_PASSWORD is set, call `enable()` to enter privileged mode
5. Execute commands sequentially
6. Return structured response

### Timeout Behavior

- Connection timeout applies to SSH handshake
- Command timeout uses netmiko defaults (device_type specific)
- If connection drops mid-batch, return partial results

### Credential Security

- Credentials NEVER appear in tool parameters
- Credentials NEVER appear in error messages
- Credentials NEVER appear in response output

## Example Usage (Claude Desktop)

```
User: Show me the version of the Cisco switch at 192.168.1.1

Claude: I'll query the Cisco switch for you.
[Calls cisco_ios_query_tool(host="192.168.1.1", commands=["show version"])]

Result: The switch is running Cisco IOS Software, Version 15.1(4)M4...
```

## Docstring Format

```python
"""
Query a Cisco IOS device via SSH.

Executes one or more read-only commands and returns structured results.
Credentials are read from environment variables (CISCO_USERNAME, CISCO_PASSWORD,
optionally CISCO_ENABLE_PASSWORD for privileged mode).

IMPORTANT: Avoid commands that generate large outputs (several MB) as they cannot
be processed. Use filtered commands (e.g., "show ip route | include 10.0").

Args:
    host: Device hostname or IP address
    commands: List of Cisco IOS CLI commands to execute (1-10 commands)
    port: SSH port (default: 22)
    timeout: Connection timeout in seconds (default: 30)

Returns:
    dict: Structured response with command results
"""
```
