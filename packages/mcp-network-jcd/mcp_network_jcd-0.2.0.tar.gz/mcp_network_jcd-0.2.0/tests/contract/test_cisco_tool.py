"""Contract tests for cisco_ios_query MCP tool."""

import json


class TestCiscoQuerySuccess:
    """Contract tests for successful cisco_ios_query responses (US1)."""

    def test_returns_success_response_structure(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T015: Successful query returns JSON matching contract schema."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert isinstance(result, dict)
        assert result["success"] is True
        assert "device" in result
        assert "results" in result
        assert "total_duration_ms" in result

    def test_response_includes_device_info(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T016: Response includes device info (host, port)."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            port=2222,
            commands=["show version"],
        )

        assert result["device"]["host"] == "192.168.1.1"
        assert result["device"]["port"] == 2222

    def test_response_includes_results_array(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T017: Response includes results array with command results."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert isinstance(result["results"], list)
        assert len(result["results"]) == 1
        assert result["results"][0]["command"] == "show version"
        assert result["results"][0]["success"] is True
        assert "output" in result["results"][0]
        assert "duration_ms" in result["results"][0]

    def test_response_includes_timestamp(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """T018: Response includes ISO 8601 timestamp."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert "timestamp" in result
        assert "T" in result["timestamp"]
        assert result["timestamp"].endswith("Z")

    def test_response_serializable_to_json(
        self, mock_cisco_credentials, mock_cisco_netmiko
    ):
        """Response can be serialized to valid JSON."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["success"] is True

    def test_custom_timeout(self, mock_cisco_credentials, mock_cisco_netmiko):
        """Query with custom timeout passes to netmiko."""
        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            timeout=60,
            commands=["show version"],
        )

        assert result["success"] is True
        mock_cisco_netmiko.assert_called_once()
        call_kwargs = mock_cisco_netmiko.call_args[1]
        assert call_kwargs["timeout"] == 60


class TestCiscoQueryConfigError:
    """Contract tests for CONFIG_ERROR (US2)."""

    def test_config_error_on_missing_credentials(self, mocker):
        """T027: Missing credentials returns CONFIG_ERROR."""
        mocker.patch.dict("os.environ", {}, clear=True)

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONFIG_ERROR"
        assert "CISCO" in result["error"]["message"]


class TestCiscoQueryAuthFailed:
    """Contract tests for AUTH_FAILED error (US2)."""

    def test_auth_failed_on_invalid_credentials(self, mock_cisco_credentials, mocker):
        """T028: Authentication failure returns AUTH_FAILED."""
        from netmiko.exceptions import NetMikoAuthenticationException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoAuthenticationException("Authentication failed"),
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "AUTH_FAILED"
        assert "message" in result["error"]
        assert result["results"] is None

    def test_auth_failed_no_credentials_in_message(self, mock_cisco_credentials, mocker):
        """Authentication error does not expose credentials."""
        from netmiko.exceptions import NetMikoAuthenticationException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoAuthenticationException("Authentication failed"),
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        message = result["error"]["message"]
        assert "testuser" not in message
        assert "testpass" not in message


class TestCiscoQueryTimeout:
    """Contract tests for CONNECTION_TIMEOUT error (US2)."""

    def test_connection_timeout_on_unreachable_host(self, mock_cisco_credentials, mocker):
        """T029: Timeout returns CONNECTION_TIMEOUT."""
        from netmiko.exceptions import NetMikoTimeoutException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=NetMikoTimeoutException("Connection timed out"),
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONNECTION_TIMEOUT"
        assert "message" in result["error"]


class TestCiscoQueryConnectionRefused:
    """Contract tests for CONNECTION_REFUSED error (US2)."""

    def test_connection_refused_on_ssh_rejection(self, mock_cisco_credentials, mocker):
        """T030: Connection refused returns CONNECTION_REFUSED."""
        from paramiko.ssh_exception import SSHException

        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=SSHException("Connection refused"),
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "CONNECTION_REFUSED"
        assert "message" in result["error"]


class TestCiscoQueryUnknownError:
    """Contract tests for UNKNOWN_ERROR (US2)."""

    def test_unknown_error_on_unexpected_exception(self, mock_cisco_credentials, mocker):
        """T031: Unexpected exception returns UNKNOWN_ERROR."""
        mocker.patch(
            "netmiko.ConnectHandler",
            side_effect=RuntimeError("Unexpected failure"),
        )

        from mcp_network_jcd.tools.cisco import cisco_ios_query

        result = cisco_ios_query(
            host="192.168.1.1",
            commands=["show version"],
        )

        assert result["success"] is False
        assert result["error"]["code"] == "UNKNOWN_ERROR"
        assert "RuntimeError" in result["error"]["message"]
