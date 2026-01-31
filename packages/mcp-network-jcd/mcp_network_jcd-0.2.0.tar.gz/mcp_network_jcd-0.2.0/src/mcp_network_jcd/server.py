"""FastMCP server for MCP Network JCD."""

from mcp.server.fastmcp import FastMCP

from mcp_network_jcd.tools.cisco import cisco_ios_query
from mcp_network_jcd.tools.paloalto import paloalto_query

mcp = FastMCP("MCP Network JCD")


@mcp.tool()
def paloalto_query_tool(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    """Query Palo Alto firewall via SSH. Creds from env: PALOALTO_USERNAME, PALOALTO_PASSWORD. Input: host*, commands* (1-10), port (22), timeout (30s). Output: {success, device, results[], total_duration_ms, timestamp}. IMPORTANT: Avoid large outputs (MB). Use filtered commands: "show routing route | match 10.14", "test security-policy-match from ZONE to ZONE source IP destination IP protocol 6 destination-port 443", "show interface logical". Avoid unfiltered: "show running security-policy", "show session all"."""
    return paloalto_query(host=host, commands=commands, port=port, timeout=timeout)


@mcp.tool()
def cisco_ios_query_tool(
    host: str,
    commands: list[str],
    port: int = 22,
    timeout: int = 30,
) -> dict:
    """Query Cisco IOS device via SSH. Creds from env: CISCO_USERNAME, CISCO_PASSWORD, CISCO_ENABLE_PASSWORD (optional). Input: host*, commands* (1-10), port (22), timeout (30s). Output: {success, device, results[], total_duration_ms, timestamp}. IMPORTANT: Avoid large outputs (MB). Use filtered commands: "show ip route | include 10.0", "show running-config | section interface". Avoid unfiltered: "show running-config", "show ip route"."""
    return cisco_ios_query(host=host, commands=commands, port=port, timeout=timeout)


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
