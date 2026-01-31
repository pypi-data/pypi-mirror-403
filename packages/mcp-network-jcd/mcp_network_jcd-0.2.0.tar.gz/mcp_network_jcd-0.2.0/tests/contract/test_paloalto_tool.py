"""Contract tests for paloalto_query MCP tool (T017)."""

import json


class TestPaloAltoQuerySuccess:
    """Contract tests for successful paloalto_query responses (T017)."""

    def test_success_response_structure(self, mock_credentials, mock_netmiko):
        """Successful query returns JSON matching contract schema."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "device" in result
        assert result["device"]["host"] == "192.168.1.1"
        assert result["device"]["port"] == 22
        assert "results" in result
        assert len(result["results"]) == 1
        assert "total_duration_ms" in result
        assert result["total_duration_ms"] >= 0
        assert "timestamp" in result

    def test_command_result_structure(self, mock_credentials, mock_netmiko):
        """Command results match contract schema."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        cmd_result = result["results"][0]
        assert cmd_result["command"] == "show system info"
        assert cmd_result["success"] is True
        assert "output" in cmd_result
        assert "duration_ms" in cmd_result
        assert cmd_result["duration_ms"] >= 0

    def test_custom_port(self, mock_credentials, mock_netmiko):
        """Query with custom port uses specified port."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            port=2222,
            commands=["show system info"],
        )

        assert result["device"]["port"] == 2222

    def test_custom_timeout(self, mock_credentials, mock_netmiko):
        """Query with custom timeout passes to netmiko."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            timeout=60,
            commands=["show system info"],
        )

        assert result["success"] is True
        mock_netmiko.assert_called_once()
        call_kwargs = mock_netmiko.call_args[1]
        assert call_kwargs["timeout"] == 60

    def test_netmiko_called_with_correct_params(self, mock_credentials, mock_netmiko):
        """Netmiko ConnectHandler called with correct parameters."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        paloalto_query(
            host="fw.example.com",
            port=22,
            commands=["show system info"],
            timeout=30,
        )

        mock_netmiko.assert_called_once()
        call_kwargs = mock_netmiko.call_args[1]
        assert call_kwargs["device_type"] == "paloalto_panos"
        assert call_kwargs["host"] == "fw.example.com"
        assert call_kwargs["port"] == 22
        assert call_kwargs["username"] == "testuser"
        assert call_kwargs["password"] == "testpass"
        assert call_kwargs["timeout"] == 30

    def test_response_serializable_to_json(self, mock_credentials, mock_netmiko):
        """Response can be serialized to valid JSON."""
        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["success"] is True


class TestPaloAltoQueryAuthFailed:
    """Contract tests for AUTH_FAILED error (T026)."""

    def test_auth_failed_response_structure(self, mock_credentials, mocker):
        """Authentication failure returns proper error response."""
        from netmiko.exceptions import NetMikoAuthenticationException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoAuthenticationException("Authentication failed"),
        )

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["success"] is False
        assert "error" in result
        assert result["error"]["code"] == "AUTH_FAILED"
        assert "message" in result["error"]
        assert result["results"] is None

    def test_auth_failed_no_credentials_in_message(self, mock_credentials, mocker):
        """Authentication error does not expose credentials."""
        from netmiko.exceptions import NetMikoAuthenticationException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoAuthenticationException("Authentication failed"),
        )

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        message = result["error"]["message"]
        assert "testuser" not in message
        assert "testpass" not in message


class TestPaloAltoQueryTimeout:
    """Contract tests for CONNECTION_TIMEOUT error (T027)."""

    def test_timeout_response_structure(self, mock_credentials, mocker):
        """Timeout returns proper error response."""
        from netmiko.exceptions import NetMikoTimeoutException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoTimeoutException("Connection timed out"),
        )

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONNECTION_TIMEOUT"
        assert "message" in result["error"]


class TestPaloAltoQueryConnectionRefused:
    """Contract tests for CONNECTION_REFUSED error (T028)."""

    def test_connection_refused_response_structure(self, mock_credentials, mocker):
        """Connection refused returns proper error response."""
        from paramiko.ssh_exception import SSHException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=SSHException("Connection refused"),
        )

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONNECTION_REFUSED"
        assert "message" in result["error"]


class TestPaloAltoQueryConfigError:
    """Contract tests for CONFIG_ERROR (T029)."""

    def test_missing_env_vars_response(self, mocker):
        """Missing credentials returns CONFIG_ERROR."""
        mocker.patch.dict("os.environ", {}, clear=True)

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["show system info"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONFIG_ERROR"
        assert "PALOALTO" in result["error"]["message"]


class TestPaloAltoQueryBatch:
    """Contract tests for batch query (T036)."""

    def test_batch_query_multiple_commands(self, mock_credentials, mocker):
        """Batch query with 3 commands returns all results."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "hostname: fw01",
            "interface eth1: up",
            "route 0.0.0.0/0 via 10.0.0.1",
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=[
                "show system info",
                "show interface all",
                "show routing route",
            ],
        )

        assert result["success"] is True
        assert len(result["results"]) == 3
        assert result["results"][0]["command"] == "show system info"
        assert result["results"][0]["output"] == "hostname: fw01"
        assert result["results"][1]["command"] == "show interface all"
        assert result["results"][2]["command"] == "show routing route"

    def test_batch_query_all_have_duration(self, mock_credentials, mocker):
        """Each command in batch has duration_ms."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = ["out1", "out2", "out3"]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["cmd1", "cmd2", "cmd3"],
        )

        for cmd_result in result["results"]:
            assert "duration_ms" in cmd_result
            assert cmd_result["duration_ms"] >= 0


class TestPaloAltoQueryPartialFailure:
    """Contract tests for partial failure (T037)."""

    def test_partial_failure_command_error(self, mock_credentials, mocker):
        """Partial failure when one command raises exception."""
        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "output1",
            Exception("Command failed"),
            "output3",
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
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

    def test_partial_failure_ssh_disconnect_mid_batch(self, mock_credentials, mocker):
        """SSH disconnect mid-batch returns partial results."""

        mock_handler = mocker.MagicMock()
        mock_handler.send_command.side_effect = [
            "output1",
            TimeoutError("Connection lost"),
        ]
        mock_handler.disconnect.return_value = None
        mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)

        from mcp_network_jcd.tools.paloalto import paloalto_query

        result = paloalto_query(
            host="192.168.1.1",
            commands=["cmd1", "cmd2", "cmd3"],
        )

        assert result["success"] is True
        assert len(result["results"]) >= 1
        assert result["results"][0]["success"] is True
        assert result["results"][0]["output"] == "output1"
