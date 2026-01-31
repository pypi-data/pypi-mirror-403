# MCP Network JCD

MCP server for querying network devices. Currently supports Palo Alto firewalls via SSH.

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Set environment variables for credentials:

```bash
export PALOALTO_USERNAME="readonly_user"
export PALOALTO_PASSWORD="your_password"
```

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-network-jcd": {
      "command": "python",
      "args": ["-m", "mcp_network_jcd.server"],
      "cwd": "/path/to/mcp-network-jcd",
      "env": {
        "PALOALTO_USERNAME": "readonly_user",
        "PALOALTO_PASSWORD": "your_password"
      }
    }
  }
}
```

## Tool: paloalto_query

Query Palo Alto firewall via SSH.

**Input:** `host*`, `commands*` (1-10), `port` (22), `timeout` (30s)

**Output:** `{success, device, results[], total_duration_ms, timestamp}`

### Usage Tips

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

## Development

```bash
# Run tests
pytest

# Lint
ruff check .
```
