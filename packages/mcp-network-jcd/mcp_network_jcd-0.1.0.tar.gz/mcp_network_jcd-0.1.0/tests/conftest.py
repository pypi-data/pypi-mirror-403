"""Shared pytest fixtures for MCP Network JCD tests."""

import pytest


@pytest.fixture
def mock_credentials(monkeypatch):
    """Mock Palo Alto credentials from environment variables."""
    monkeypatch.setenv("PALOALTO_USERNAME", "testuser")
    monkeypatch.setenv("PALOALTO_PASSWORD", "testpass")


@pytest.fixture
def mock_netmiko(mocker):
    """Mock netmiko ConnectHandler for SSH testing."""
    mock_handler = mocker.MagicMock()
    mock_handler.send_command.return_value = "hostname: test-fw\nserial: 001234567890"
    mock_handler.disconnect.return_value = None

    mock_connect = mocker.patch("netmiko.ConnectHandler", return_value=mock_handler)
    return mock_connect


@pytest.fixture
def sample_device_params():
    """Sample device connection parameters."""
    return {
        "host": "192.168.1.1",
        "port": 22,
        "timeout": 30,
    }


@pytest.fixture
def sample_commands():
    """Sample PAN-OS commands for testing."""
    return ["show system info", "show interface all"]
