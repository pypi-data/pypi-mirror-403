"""Unit tests for Cisco IOS Pydantic models."""

import pytest


class TestCiscoCredentials:
    """Tests for CiscoCredentials model (US4 - Secure Credential Management)."""

    def test_credentials_from_env_success(self, monkeypatch):
        """T007: CiscoCredentials loads from environment variables."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        assert creds.username == "admin"
        assert creds.password == "secret"

    def test_credentials_missing_username_raises(self, monkeypatch):
        """T008: CiscoCredentials raises error when username missing."""
        monkeypatch.delenv("CISCO_USERNAME", raising=False)
        monkeypatch.setenv("CISCO_PASSWORD", "secret")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        with pytest.raises(ValueError, match="CISCO_USERNAME"):
            CiscoCredentials.from_env()

    def test_credentials_missing_password_raises(self, monkeypatch):
        """T009: CiscoCredentials raises error when password missing."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.delenv("CISCO_PASSWORD", raising=False)

        from mcp_network_jcd.models.cisco import CiscoCredentials

        with pytest.raises(ValueError, match="CISCO_PASSWORD"):
            CiscoCredentials.from_env()

    def test_enable_password_optional(self, monkeypatch):
        """T010: CiscoCredentials enable_password is optional."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")
        monkeypatch.delenv("CISCO_ENABLE_PASSWORD", raising=False)

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        assert creds.enable_password is None

    def test_enable_password_empty_string_treated_as_none(self, monkeypatch):
        """T011: CiscoCredentials treats empty enable_password as None."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")
        monkeypatch.setenv("CISCO_ENABLE_PASSWORD", "")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        assert creds.enable_password is None

    def test_enable_password_whitespace_treated_as_none(self, monkeypatch):
        """CiscoCredentials treats whitespace-only enable_password as None."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")
        monkeypatch.setenv("CISCO_ENABLE_PASSWORD", "   ")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        assert creds.enable_password is None

    def test_enable_password_loaded_when_set(self, monkeypatch):
        """CiscoCredentials loads enable_password when set."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")
        monkeypatch.setenv("CISCO_ENABLE_PASSWORD", "enablesecret")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        assert creds.enable_password == "enablesecret"

    def test_password_not_in_repr(self, monkeypatch):
        """CiscoCredentials password is hidden in repr."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "secret123")
        monkeypatch.setenv("CISCO_ENABLE_PASSWORD", "enablesecret")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        creds = CiscoCredentials.from_env()
        repr_str = repr(creds)
        assert "secret123" not in repr_str
        assert "enablesecret" not in repr_str

    def test_from_env_empty_username(self, monkeypatch):
        """CiscoCredentials raises error when username is empty."""
        monkeypatch.setenv("CISCO_USERNAME", "")
        monkeypatch.setenv("CISCO_PASSWORD", "secret")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        with pytest.raises(ValueError):
            CiscoCredentials.from_env()

    def test_from_env_empty_password(self, monkeypatch):
        """CiscoCredentials raises error when password is empty."""
        monkeypatch.setenv("CISCO_USERNAME", "admin")
        monkeypatch.setenv("CISCO_PASSWORD", "")

        from mcp_network_jcd.models.cisco import CiscoCredentials

        with pytest.raises(ValueError):
            CiscoCredentials.from_env()
