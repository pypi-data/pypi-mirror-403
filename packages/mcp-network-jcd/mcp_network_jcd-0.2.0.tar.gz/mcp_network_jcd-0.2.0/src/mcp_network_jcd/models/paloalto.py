"""Pydantic models for Palo Alto SSH query tool."""

import os
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class ServerCredentials(BaseModel):
    """Credentials loaded from environment variables at server startup."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1, repr=False)

    @classmethod
    def from_env(cls) -> "ServerCredentials":
        """Load credentials from environment variables."""
        username = os.environ.get("PALOALTO_USERNAME", "")
        password = os.environ.get("PALOALTO_PASSWORD", "")
        if not username:
            raise ValueError("PALOALTO_USERNAME must be set")
        if not password:
            raise ValueError("PALOALTO_PASSWORD must be set")
        return cls(username=username, password=password)


class DeviceConnection(BaseModel):
    """Connection parameters for a Palo Alto device."""

    host: str = Field(..., min_length=1, description="Device hostname or IP address")
    port: int = Field(default=22, ge=1, le=65535, description="SSH port")
    timeout: int = Field(default=30, ge=1, le=300, description="Connection timeout in seconds")

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate and trim host."""
        if not v.strip():
            raise ValueError("Host cannot be empty or whitespace")
        return v.strip()


class QueryRequest(BaseModel):
    """User request containing connection info and commands."""

    host: str = Field(..., min_length=1)
    port: int = Field(default=22, ge=1, le=65535)
    commands: list[str] = Field(..., min_length=1, max_length=10)
    timeout: int = Field(default=30, ge=1, le=300)

    @field_validator("host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate and trim host."""
        if not v.strip():
            raise ValueError("Host cannot be empty or whitespace")
        return v.strip()

    @field_validator("commands")
    @classmethod
    def validate_commands(cls, v: list[str]) -> list[str]:
        """Validate and trim commands."""
        validated = []
        for cmd in v:
            if not cmd.strip():
                raise ValueError("Commands cannot be empty or whitespace")
            validated.append(cmd.strip())
        return validated


class CommandResult(BaseModel):
    """Result of executing a single command."""

    command: str
    success: bool
    output: str | None = None
    error: str | None = None
    duration_ms: int = Field(ge=0)

    @model_validator(mode="after")
    def check_output_or_error(self) -> "CommandResult":
        """Failed commands must have error message."""
        if not self.success and self.error is None:
            raise ValueError("Failed command must have error message")
        return self


class DeviceInfo(BaseModel):
    """Device info in response (no credentials)."""

    host: str
    port: int


class ErrorInfo(BaseModel):
    """Connection-level error information."""

    code: str
    message: str


class QueryResponse(BaseModel):
    """Complete response for a query request."""

    success: bool
    device: DeviceInfo
    results: list[CommandResult] | None = None
    error: ErrorInfo | None = None
    total_duration_ms: int = Field(ge=0)
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat().replace("+00:00", "Z")
    )
