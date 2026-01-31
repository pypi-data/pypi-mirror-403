"""Integration tests for Cisco IOS SSH connection."""


class TestCiscoSSHIntegration:
    """Integration tests for Cisco SSH connection with mocked netmiko (US1)."""

    def test_single_command_execution(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T019: Single command is executed via SSH."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is True
        connection = mock_cisco_netmiko.return_value
        connection.send_command.assert_called_with("show version")

    def test_command_output_returned_unmodified(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T020: Command output is returned unmodified."""
        mock_cisco_netmiko.return_value.send_command.return_value = (
            "Cisco IOS Software, Version 15.1(4)M4\nhostname: sw01"
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["results"][0]["output"] == (
            "Cisco IOS Software, Version 15.1(4)M4\nhostname: sw01"
        )

    def test_uses_cisco_ios_device_type(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T021: netmiko is called with cisco_ios device type."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        mock_cisco_netmiko.assert_called_once()
        call_kwargs = mock_cisco_netmiko.call_args[1]
        assert call_kwargs["device_type"] == "cisco_ios"

    def test_ssh_connection_disconnected(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """SSH connection is properly disconnected after query."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        connection = mock_cisco_netmiko.return_value
        connection.disconnect.assert_called_once()

    def test_netmiko_called_with_correct_params(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """netmiko ConnectHandler called with correct parameters."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        cisco_ios_query(
            host="sw.example.com",
            port=22,
            commands=["show version"],
            timeout=30,
        )

        mock_cisco_netmiko.assert_called_once()
        call_kwargs = mock_cisco_netmiko.call_args[1]
        assert call_kwargs["device_type"] == "cisco_ios"
        assert call_kwargs["host"] == "sw.example.com"
        assert call_kwargs["port"] == 22
        assert call_kwargs["username"] == "testuser"
        assert call_kwargs["password"] == "testpass"
        assert call_kwargs["timeout"] == 30


class TestCiscoEnableMode:
    """Tests for enable mode functionality (US4 Enhancement)."""

    def test_enable_mode_called_when_password_set(
        self, mock_cisco_credentials_with_enable, mocker
    ):
        """T047: Enable mode is called when enable password is set."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.return_value = "output"
        mock_handler.disconnect.return_value = None
        mock_handler.enable.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show running-config"],
        )

        assert result["success"] is True
        mock_handler.enable.assert_called_once()

    def test_enable_mode_not_called_when_no_password(
        self, mock_cisco_credentials, mocker
    ):
        """T048: Enable mode is NOT called when no enable password."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.return_value = "output"
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is True
        mock_handler.enable.assert_not_called()


class TestCiscoEnableAuthFailed:
    """Tests for enable authentication failure (US2)."""

    def test_enable_auth_failed_on_wrong_enable_password(
        self, mock_cisco_credentials_with_enable, mocker
    ):
        """T032: Wrong enable password returns AUTH_FAILED."""
        mock_handler = mocker.MagicMock()
        mock_handler.enable.side_effect = Exception("Enable failed")
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show running-config"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "AUTH_FAILED"
        assert "Enable" in result["error"]["message"]
        mock_handler.disconnect.assert_called_once()


class TestCiscoBatchExecution:
    """Tests for batch command execution (US3)."""

    def test_multiple_commands_return_individual_results(
        self, mock_cisco_credentials, mocker
    ):
        """T039: Multiple commands return individual results."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "Cisco IOS Software, Version 15.1",
            "Interface              IP-Address",
            "Gateway of last resort is 10.0.0.1",
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=[
                "show version",
                "show ip interface brief",
                "show ip route",
            ],
        )

        assert result["success"] is True
        assert len(result["results"]) == 3
        assert result["results"][0]["command"] == "show version"
        assert result["results"][0]["output"] == "Cisco IOS Software, Version 15.1"
        assert result["results"][1]["command"] == "show ip interface brief"
        assert result["results"][2]["command"] == "show ip route"

    def test_each_command_has_duration_ms(self, mock_cisco_credentials, mocker):
        """T040: Each command in batch has duration_ms."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = ["out1", "out2", "out3"]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["cmd1", "cmd2", "cmd3"],
        )

        for cmd_result in result["results"]:
            assert "duration_ms" in cmd_result
            assert cmd_result["duration_ms"] >= 0

    def test_partial_failure_returns_completed_results(
        self, mock_cisco_credentials, mocker
    ):
        """T041: Partial failure returns completed results."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "output1",
            Exception("Command failed"),
            "output3",
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["cmd1", "cmd2", "cmd3"],
        )

        assert result["success"] is True
        assert len(result["results"]) == 3
        assert result["results"][0]["success"] is True
        assert result["results"][0]["output"] == "output1"
        assert result["results"][1]["success"] is False
        assert result["results"][1]["error"] is not None
        assert result["results"][2]["success"] is True
        assert result["results"][2]["output"] == "output3"

    def test_batch_stops_on_connection_drop(self, mock_cisco_credentials, mocker):
        """T042: Batch stops on connection drop."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "output1",
            TimeoutError("Connection lost"),
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["cmd1", "cmd2", "cmd3"],
        )

        assert result["success"] is True
        assert len(result["results"]) == 2
        assert result["results"][0]["success"] is True
        assert result["results"][0]["output"] == "output1"
        assert result["results"][1]["success"] is False
        assert "Connection lost" in result["results"][1]["error"]
