"""
Authentication data models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class TokenInfo:
    """Token information from Cognito."""

    access_token: str
    id_token: str
    refresh_token: str
    expires_at: datetime
    token_type: str = "Bearer"

    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        return datetime.utcnow() >= self.expires_at

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "access_token": self.access_token,
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TokenInfo":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            id_token=data["id_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
            token_type=data.get("token_type", "Bearer"),
        )


@dataclass
class AuthResult:
    """Result of an authentication attempt."""

    success: bool
    user_email: str | None = None
    user_id: str | None = None
    expires_at: datetime | None = None
    error: str | None = None
    tokens: TokenInfo | None = None

    @classmethod
    def failure(cls, error: str) -> "AuthResult":
        """Create a failure result."""
        return cls(success=False, error=error)

    @classmethod
    def success_result(
        cls,
        user_email: str,
        user_id: str,
        expires_at: datetime,
        tokens: TokenInfo,
    ) -> "AuthResult":
        """Create a success result."""
        return cls(
            success=True,
            user_email=user_email,
            user_id=user_id,
            expires_at=expires_at,
            tokens=tokens,
        )


@dataclass
class DeviceCodeResponse:
    """Response from device authorization request."""

    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


@dataclass
class UserInfo:
    """User information from Cognito."""

    sub: str
    email: str
    email_verified: bool
    name: str | None = None
    phone_number: str | None = None
    phone_number_verified: bool = False
    custom_attributes: dict[str, str] | None = None
