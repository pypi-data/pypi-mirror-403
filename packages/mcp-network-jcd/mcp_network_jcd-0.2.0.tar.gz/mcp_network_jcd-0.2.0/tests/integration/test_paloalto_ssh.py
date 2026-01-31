"""Integration tests for Palo Alto SSH connection (T018)."""



class TestPaloAltoSSHIntegration:
    """Integration tests for SSH connection with mocked netmiko (T018)."""

    def test_ssh_connection_established(self, mock_credentials, mock_netmiko):
        """SSH connection is established via netmiko."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["success"] is True
        mock_netmiko.assert_called_once()

    def test_ssh_connection_disconnected(self, mock_credentials, mock_netmiko):
        """SSH connection is properly disconnected after query."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        connection = mock_netmiko.return_value
        connection.disconnect.assert_called_once()

    def test_send_command_called(self, mock_credentials, mock_netmiko):
        """send_command is called for each command."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        connection = mock_netmiko.return_value
        connection.send_command.assert_called_with("show system info")

    def test_command_output_captured(self, mock_credentials, mock_netmiko):
        """Command output is captured in result."""
        mock_netmiko.return_value.send_command.return_value = "hostname: test-firewall"

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["results"][0]["output"] == "hostname: test-firewall"

    def test_host_key_auto_add(self, mock_credentials, mock_netmiko):
        """SSH host key policy set to auto-add."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        call_kwargs = mock_netmiko.call_args[1]
        assert call_kwargs.get("ssh_strict") is False or "ssh_strict" not in call_kwargs
