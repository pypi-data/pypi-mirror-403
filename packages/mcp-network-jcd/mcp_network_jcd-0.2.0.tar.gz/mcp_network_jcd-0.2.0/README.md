# MCP Network JCD

MCP server for querying network devices via SSH. Supports Palo Alto firewalls and Cisco IOS devices.

## Installation

```bash
pip install mcp-network-jcd
```

Or from source:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Set environment variables for credentials:

```bash
# Palo Alto
export PALOALTO_USERNAME="readonly_user"
export PALOALTO_PASSWORD="your_password"

# Cisco IOS
export CISCO_USERNAME="readonly_user"
export CISCO_PASSWORD="your_password"
export CISCO_ENABLE_PASSWORD="enable_secret"  # Optional
```

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-network-jcd": {
      "command": "python",
      "args": ["-m", "mcp_network_jcd.server"],
      "env": {
        "PALOALTO_USERNAME": "readonly_user",
        "PALOALTO_PASSWORD": "your_password",
        "CISCO_USERNAME": "cisco_user",
        "CISCO_PASSWORD": "cisco_password",
        "CISCO_ENABLE_PASSWORD": "enable_secret"
      }
    }
  }
}
```

## Tools

### paloalto_query

Query Palo Alto firewall via SSH.

**Input:** `host*`, `commands*` (1-10), `port` (22), `timeout` (30s)

**Output:** `{success, device, results[], total_duration_ms, timestamp}`

#### Usage Tips

Use filtered commands to avoid large outputs:

```
# Good
show routing route | match 10.14
test security-policy-match from ZONE1 to ZONE2 source IP destination IP protocol 6 destination-port 443
show interface logical
show system info

# Avoid (output too large)
show running security-policy
show session all
show routing route  # without filter
```

### cisco_ios_query

Query Cisco IOS devices via SSH.

**Input:** `host*`, `commands*` (1-10), `port` (22), `timeout` (30s)

**Output:** `{success, device, results[], total_duration_ms, timestamp}`

#### Usage Tips

Use filtered commands to avoid large outputs:

```
# Good
show version
show ip interface brief
show ip route | include 10.0
show running-config | section interface
show interfaces status

# Avoid (output too large)
show running-config  # full config
show ip route  # without filter on large routing tables
show tech-support
```

#### Enable Mode

If `CISCO_ENABLE_PASSWORD` is set, the tool automatically enters privileged EXEC mode before running commands.

## Error Codes

Both tools return structured error responses:

| Code | Description |
|------|-------------|
| `CONFIG_ERROR` | Missing credentials in environment |
| `AUTH_FAILED` | Invalid username/password or enable password |
| `CONNECTION_TIMEOUT` | Device unreachable |
| `CONNECTION_REFUSED` | SSH connection rejected |
| `UNKNOWN_ERROR` | Unexpected error |

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .
```

## License

MIT
