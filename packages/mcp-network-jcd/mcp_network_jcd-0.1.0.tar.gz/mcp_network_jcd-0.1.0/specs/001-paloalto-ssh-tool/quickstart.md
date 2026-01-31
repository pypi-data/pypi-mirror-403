# Quickstart: Palo Alto SSH Query Tool

**Feature**: 001-paloalto-ssh-tool
**Date**: 2026-01-30

## Prerequisites

- Python 3.12+
- Access to a Palo Alto firewall with SSH enabled
- Read-only SSH credentials for the target device

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-network-jcd

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -e .
```

## Configuration

### Credentials Setup

Credentials are configured via environment variables in mcp.json (NOT passed as tool parameters):

| Variable | Description |
|----------|-------------|
| `PALOALTO_USERNAME` | SSH username for device connections |
| `PALOALTO_PASSWORD` | SSH password for device connections |

### Configuration for Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-network-jcd": {
      "command": "python",
      "args": ["-m", "mcp_network_jcd.server"],
      "cwd": "/path/to/mcp-network-jcd",
      "env": {
        "PALOALTO_USERNAME": "readonly",
        "PALOALTO_PASSWORD": "your-password-here"
      }
    }
  }
}
```

### Running Manually (Development)

```bash
export PALOALTO_USERNAME="readonly"
export PALOALTO_PASSWORD="your-password-here"
python -m mcp_network_jcd.server
```

## Using the Tool

### Via MCP Client (Claude, etc.)

Once connected, the `paloalto_query` tool is available. Credentials are automatically used from
the server configuration - you only need to specify the device and commands:

```
Query the Palo Alto firewall at 192.168.1.1 and show system info.
```

### Direct Python Usage (for testing)

```python
import os
os.environ["PALOALTO_USERNAME"] = "readonly"
os.environ["PALOALTO_PASSWORD"] = "testpass"

from mcp_network_jcd.tools.paloalto import paloalto_query

result = paloalto_query(
    host="192.168.1.1",
    commands=["show system info"]
)
print(result)
```

## Example Tool Input

```json
{
  "host": "192.168.1.1",
  "port": 22,
  "commands": ["show system info", "show interface ethernet1/1"],
  "timeout": 30
}
```

**Note**: `username` and `password` are NOT in tool input - they come from environment variables.

## Example Tool Output

### Success

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
      "output": "hostname: fw-prod-01\nip-address: 192.168.1.1\nserial: 012345678901234\nsw-version: 10.2.3\n...",
      "duration_ms": 1234
    },
    {
      "command": "show interface ethernet1/1",
      "success": true,
      "output": "Name: ethernet1/1\nLink status: up\n...",
      "duration_ms": 856
    }
  ],
  "total_duration_ms": 3456,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

### Connection Error

```json
{
  "success": false,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "error": {
    "code": "CONNECTION_TIMEOUT",
    "message": "Device unreachable: connection timed out after 30 seconds"
  },
  "total_duration_ms": 30123,
  "timestamp": "2026-01-30T12:00:30Z"
}
```

### Missing Credentials Error

```json
{
  "success": false,
  "device": {
    "host": "192.168.1.1",
    "port": 22
  },
  "error": {
    "code": "CONFIG_ERROR",
    "message": "Server configuration error: PALOALTO_USERNAME and PALOALTO_PASSWORD must be set"
  },
  "total_duration_ms": 1,
  "timestamp": "2026-01-30T12:00:00Z"
}
```

## Running Tests

```bash
# All tests (credentials mocked via fixtures)
pytest

# Unit tests only
pytest tests/unit/

# Contract tests only
pytest tests/contract/

# With coverage
pytest --cov=mcp_network_jcd --cov-report=term-missing
```

## Common PAN-OS Commands

| Command | Description |
|---------|-------------|
| `show system info` | Device hostname, serial, version |
| `show interface all` | All interface status |
| `show routing route` | Routing table |
| `show running security-policy` | Active security rules |
| `show session all` | Active sessions |
| `show high-availability state` | HA status |

## Troubleshooting

### Missing Credentials Error

- Verify `PALOALTO_USERNAME` and `PALOALTO_PASSWORD` are set in mcp.json `env` section
- For manual runs, ensure environment variables are exported before starting server

### Connection Timeout

- Verify network connectivity to the device (`ping`, `telnet <host> 22`)
- Check firewall rules allowing SSH from MCP server
- Increase timeout parameter if network is slow

### Authentication Failed

- Verify username and password in mcp.json are correct
- Check the account has SSH access enabled
- Ensure the account is not locked

### Command Output Empty

- Some commands require specific permissions
- Verify the account has read access to the requested data
