"""Pydantic models for Cisco IOS SSH query tool."""

import os

from pydantic import BaseModel, Field, field_validator


class CiscoCredentials(BaseModel):
    """Credentials loaded from environment variables for Cisco devices."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1, repr=False)
    enable_password: str | None = Field(default=None, repr=False)

    @field_validator("enable_password")
    @classmethod
    def validate_enable_password(cls, v: str | None) -> str | None:
        """Treat empty or whitespace-only enable_password as None."""
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    @classmethod
    def from_env(cls) -> "CiscoCredentials":
        """Load credentials from environment variables."""
        username = os.environ.get("CISCO_USERNAME", "")
        password = os.environ.get("CISCO_PASSWORD", "")
        enable_password = os.environ.get("CISCO_ENABLE_PASSWORD")

        if not username:
            raise ValueError("CISCO_USERNAME must be set")
        if not password:
            raise ValueError("CISCO_PASSWORD must be set")

        return cls(
            username=username,
            password=password,
            enable_password=enable_password if enable_password else None,
        )
