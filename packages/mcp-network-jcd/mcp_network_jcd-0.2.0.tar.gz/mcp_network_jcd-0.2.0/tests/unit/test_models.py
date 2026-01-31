"""Unit tests for Palo Alto Pydantic models."""

import pytest


class TestCommandResult:
    """Tests for CommandResult model (T015)."""

    def test_successful_command(self):
        """CommandResult accepts successful command with output."""
        from mcp_network_jcd.models.paloalto import CommandResult

        result = CommandResult(
            command="show system info",
            success=True,
            output="hostname: fw01",
            duration_ms=100,
        )
        assert result.command == "show system info"
        assert result.success is True
        assert result.output == "hostname: fw01"
        assert result.error is None
        assert result.duration_ms == 100

    def test_failed_command_requires_error(self):
        """CommandResult requires error message when success=false."""
        from mcp_network_jcd.models.paloalto import CommandResult

        with pytest.raises(ValueError, match="error"):
            CommandResult(
                command="invalid command",
                success=False,
                duration_ms=50,
            )

    def test_failed_command_with_error(self):
        """CommandResult accepts failed command with error message."""
        from mcp_network_jcd.models.paloalto import CommandResult

        result = CommandResult(
            command="bad command",
            success=False,
            error="Unknown command",
            duration_ms=10,
        )
        assert result.success is False
        assert result.error == "Unknown command"

    def test_partial_result_output_and_error(self):
        """CommandResult accepts partial result with both output and error."""
        from mcp_network_jcd.models.paloalto import CommandResult

        result = CommandResult(
            command="show session all",
            success=False,
            output="session 1...",
            error="Connection lost during command",
            duration_ms=5000,
        )
        assert result.success is False
        assert result.output == "session 1..."
        assert result.error == "Connection lost during command"

    def test_duration_ms_non_negative(self):
        """CommandResult rejects negative duration_ms."""
        from mcp_network_jcd.models.paloalto import CommandResult

        with pytest.raises(ValueError):
            CommandResult(
                command="show system info",
                success=True,
                output="ok",
                duration_ms=-1,
            )


class TestQueryResponse:
    """Tests for QueryResponse model (T016)."""

    def test_successful_response(self):
        """QueryResponse accepts successful response with results."""
        from mcp_network_jcd.models.paloalto import (
            CommandResult,
            DeviceInfo,
            QueryResponse,
        )

        response = QueryResponse(
            success=True,
            device=DeviceInfo(host="192.168.1.1", port=22),
            results=[
                CommandResult(
                    command="show system info",
                    success=True,
                    output="hostname: fw01",
                    duration_ms=100,
                )
            ],
            total_duration_ms=150,
        )
        assert response.success is True
        assert response.device.host == "192.168.1.1"
        assert len(response.results) == 1
        assert response.error is None

    def test_failed_response_with_error(self):
        """QueryResponse accepts failed response with error info."""
        from mcp_network_jcd.models.paloalto import (
            DeviceInfo,
            ErrorInfo,
            QueryResponse,
        )

        response = QueryResponse(
            success=False,
            device=DeviceInfo(host="192.168.1.1", port=22),
            error=ErrorInfo(code="AUTH_FAILED", message="Invalid credentials"),
            total_duration_ms=5000,
        )
        assert response.success is False
        assert response.error.code == "AUTH_FAILED"
        assert response.results is None

    def test_timestamp_auto_generated(self):
        """QueryResponse generates ISO 8601 timestamp."""
        from mcp_network_jcd.models.paloalto import DeviceInfo, QueryResponse

        response = QueryResponse(
            success=True,
            device=DeviceInfo(host="192.168.1.1", port=22),
            results=[],
            total_duration_ms=100,
        )
        assert response.timestamp is not None
        assert "T" in response.timestamp
        assert response.timestamp.endswith("Z")

    def test_total_duration_non_negative(self):
        """QueryResponse rejects negative total_duration_ms."""
        from mcp_network_jcd.models.paloalto import DeviceInfo, QueryResponse

        with pytest.raises(ValueError):
            QueryResponse(
                success=True,
                device=DeviceInfo(host="192.168.1.1", port=22),
                results=[],
                total_duration_ms=-1,
            )


class TestErrorInfo:
    """Tests for ErrorInfo model (T025)."""

    def test_valid_error_info(self):
        """ErrorInfo accepts valid error code and message."""
        from mcp_network_jcd.models.paloalto import ErrorInfo

        error = ErrorInfo(code="AUTH_FAILED", message="Invalid credentials")
        assert error.code == "AUTH_FAILED"
        assert error.message == "Invalid credentials"

    def test_all_error_codes(self):
        """ErrorInfo accepts all defined error codes."""
        from mcp_network_jcd.models.paloalto import ErrorInfo

        codes = [
            "CONNECTION_TIMEOUT",
            "AUTH_FAILED",
            "CONNECTION_REFUSED",
            "COMMAND_FAILED",
            "VALIDATION_ERROR",
            "CONFIG_ERROR",
            "UNKNOWN_ERROR",
        ]
        for code in codes:
            error = ErrorInfo(code=code, message=f"Test message for {code}")
            assert error.code == code


class TestServerCredentials:
    """Tests for ServerCredentials model (T006)."""

    def test_from_env_success(self, monkeypatch):
        """ServerCredentials loads from environment variables."""
        monkeypatch.setenv("PALOALTO_USERNAME", "admin")
        monkeypatch.setenv("PALOALTO_PASSWORD", "secret123")

        from mcp_network_jcd.models.paloalto import ServerCredentials

        creds = ServerCredentials.from_env()
        assert creds.username == "admin"
        assert creds.password == "secret123"

    def test_from_env_missing_username(self, monkeypatch):
        """ServerCredentials raises error when username missing."""
        monkeypatch.delenv("PALOALTO_USERNAME", raising=False)
        monkeypatch.setenv("PALOALTO_PASSWORD", "secret123")

        from mcp_network_jcd.models.paloalto import ServerCredentials

        with pytest.raises(ValueError, match="PALOALTO_USERNAME"):
            ServerCredentials.from_env()

    def test_from_env_missing_password(self, monkeypatch):
        """ServerCredentials raises error when password missing."""
        monkeypatch.setenv("PALOALTO_USERNAME", "admin")
        monkeypatch.delenv("PALOALTO_PASSWORD", raising=False)

        from mcp_network_jcd.models.paloalto import ServerCredentials

        with pytest.raises(ValueError, match="PALOALTO_PASSWORD"):
            ServerCredentials.from_env()

    def test_from_env_empty_username(self, monkeypatch):
        """ServerCredentials raises error when username is empty."""
        monkeypatch.setenv("PALOALTO_USERNAME", "")
        monkeypatch.setenv("PALOALTO_PASSWORD", "secret123")

        from mcp_network_jcd.models.paloalto import ServerCredentials

        with pytest.raises(ValueError):
            ServerCredentials.from_env()

    def test_password_not_in_repr(self, monkeypatch):
        """ServerCredentials password is hidden in repr."""
        monkeypatch.setenv("PALOALTO_USERNAME", "admin")
        monkeypatch.setenv("PALOALTO_PASSWORD", "secret123")

        from mcp_network_jcd.models.paloalto import ServerCredentials

        creds = ServerCredentials.from_env()
        repr_str = repr(creds)
        assert "secret123" not in repr_str


class TestDeviceConnection:
    """Tests for DeviceConnection model (T007)."""

    def test_valid_connection(self):
        """DeviceConnection accepts valid parameters."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        conn = DeviceConnection(host="192.168.1.1")
        assert conn.host == "192.168.1.1"
        assert conn.port == 22  # default
        assert conn.timeout == 30  # default

    def test_custom_port(self):
        """DeviceConnection accepts custom port."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        conn = DeviceConnection(host="fw.example.com", port=2222)
        assert conn.port == 2222

    def test_custom_timeout(self):
        """DeviceConnection accepts custom timeout."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        conn = DeviceConnection(host="10.0.0.1", timeout=60)
        assert conn.timeout == 60

    def test_empty_host_rejected(self):
        """DeviceConnection rejects empty host."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="")

    def test_whitespace_host_rejected(self):
        """DeviceConnection rejects whitespace-only host."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="   ")

    def test_host_trimmed(self):
        """DeviceConnection trims whitespace from host."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        conn = DeviceConnection(host="  192.168.1.1  ")
        assert conn.host == "192.168.1.1"

    def test_port_min_boundary(self):
        """DeviceConnection rejects port below 1."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="192.168.1.1", port=0)

    def test_port_max_boundary(self):
        """DeviceConnection rejects port above 65535."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="192.168.1.1", port=65536)

    def test_timeout_min_boundary(self):
        """DeviceConnection rejects timeout below 1."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="192.168.1.1", timeout=0)

    def test_timeout_max_boundary(self):
        """DeviceConnection rejects timeout above 300."""
        from mcp_network_jcd.models.paloalto import DeviceConnection

        with pytest.raises(ValueError):
            DeviceConnection(host="192.168.1.1", timeout=301)


class TestQueryRequest:
    """Tests for QueryRequest model (T008)."""

    def test_valid_single_command(self):
        """QueryRequest accepts single command."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        req = QueryRequest(host="192.168.1.1", commands=["show system info"])
        assert req.host == "192.168.1.1"
        assert req.commands == ["show system info"]

    def test_valid_multiple_commands(self):
        """QueryRequest accepts multiple commands."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        commands = ["show system info", "show interface all"]
        req = QueryRequest(host="192.168.1.1", commands=commands)
        assert len(req.commands) == 2

    def test_empty_commands_rejected(self):
        """QueryRequest rejects empty commands list."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        with pytest.raises(ValueError):
            QueryRequest(host="192.168.1.1", commands=[])

    def test_empty_command_string_rejected(self):
        """QueryRequest rejects empty command string in list."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        with pytest.raises(ValueError):
            QueryRequest(host="192.168.1.1", commands=["show system info", ""])

    def test_whitespace_command_rejected(self):
        """QueryRequest rejects whitespace-only command."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        with pytest.raises(ValueError):
            QueryRequest(host="192.168.1.1", commands=["   "])

    def test_commands_trimmed(self):
        """QueryRequest trims whitespace from commands."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        req = QueryRequest(host="192.168.1.1", commands=["  show system info  "])
        assert req.commands == ["show system info"]

    def test_max_commands_accepted(self):
        """QueryRequest accepts up to 10 commands."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        commands = [f"show interface e{i}" for i in range(10)]
        req = QueryRequest(host="192.168.1.1", commands=commands)
        assert len(req.commands) == 10

    def test_over_max_commands_rejected(self):
        """QueryRequest rejects more than 10 commands."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        commands = [f"show interface e{i}" for i in range(11)]
        with pytest.raises(ValueError):
            QueryRequest(host="192.168.1.1", commands=commands)

    def test_default_port(self):
        """QueryRequest uses default port 22."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        req = QueryRequest(host="192.168.1.1", commands=["show system info"])
        assert req.port == 22

    def test_default_timeout(self):
        """QueryRequest uses default timeout 30."""
        from mcp_network_jcd.models.paloalto import QueryRequest

        req = QueryRequest(host="192.168.1.1", commands=["show system info"])
        assert req.timeout == 30
