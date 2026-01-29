"""
Session Manager for AiCippy.

Handles user authentication sessions with automatic timeout after 12 hours
of inactivity or usage. Supports secure token storage and validation.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from aicippy.installer.platform_detect import PlatformInfo, detect_platform

# Session configuration
SESSION_TIMEOUT_HOURS: Final[int] = 12
SESSION_FILE_NAME: Final[str] = "session.json"
TOKEN_LENGTH: Final[int] = 32

# Session states
SESSION_VALID: Final[str] = "valid"
SESSION_EXPIRED: Final[str] = "expired"
SESSION_INVALID: Final[str] = "invalid"
SESSION_MISSING: Final[str] = "missing"


@dataclass
class SessionInfo:
    """User session information."""

    user_id: str
    username: str
    email: str
    session_token: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    device_id: str
    ip_address: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert session to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "session_token": self.session_token,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "device_id": self.device_id,
            "ip_address": self.ip_address,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> SessionInfo:
        """Create session from dictionary."""
        return cls(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            session_token=data["session_token"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_activity=datetime.fromisoformat(data["last_activity"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            device_id=data["device_id"],
            ip_address=data.get("ip_address"),
            metadata=data.get("metadata", {}),
        )

    @property
    def is_expired(self) -> bool:
        """Check if session has expired."""
        now = datetime.now(timezone.utc)
        return now >= self.expires_at

    @property
    def time_remaining(self) -> timedelta:
        """Get time remaining until expiration."""
        now = datetime.now(timezone.utc)
        remaining = self.expires_at - now
        return remaining if remaining.total_seconds() > 0 else timedelta(0)

    @property
    def hours_remaining(self) -> float:
        """Get hours remaining until expiration."""
        return self.time_remaining.total_seconds() / 3600


@dataclass
class SessionValidationResult:
    """Result of session validation."""

    status: str
    session: SessionInfo | None
    message: str
    needs_login: bool


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_hex(TOKEN_LENGTH)


def generate_device_id() -> str:
    """Generate a unique device identifier based on system info."""
    platform_info = detect_platform()

    # Combine system identifiers
    components = [
        platform_info.os_name,
        platform_info.os_version,
        str(platform_info.architecture),
        platform_info.home_dir.name,
        os.environ.get("USER", os.environ.get("USERNAME", "unknown")),
    ]

    # Create a hash
    combined = "|".join(components)
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def get_session_file_path(platform_info: PlatformInfo | None = None) -> Path:
    """
    Get the path to the session file.

    Args:
        platform_info: Optional platform info (will be detected if not provided).

    Returns:
        Path to the session file.
    """
    if platform_info is None:
        platform_info = detect_platform()

    sessions_dir = platform_info.config_path / "sessions"
    return sessions_dir / SESSION_FILE_NAME


def create_session(
    user_id: str,
    username: str,
    email: str,
    ip_address: str | None = None,
    metadata: dict[str, str] | None = None,
) -> SessionInfo:
    """
    Create a new user session.

    Args:
        user_id: Unique user identifier.
        username: User's display name.
        email: User's email address.
        ip_address: Optional IP address.
        metadata: Optional additional metadata.

    Returns:
        New SessionInfo instance.
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=SESSION_TIMEOUT_HOURS)

    return SessionInfo(
        user_id=user_id,
        username=username,
        email=email,
        session_token=generate_session_token(),
        created_at=now,
        last_activity=now,
        expires_at=expires_at,
        device_id=generate_device_id(),
        ip_address=ip_address,
        metadata=metadata or {},
    )


def save_session(
    session: SessionInfo,
    platform_info: PlatformInfo | None = None,
) -> tuple[bool, str]:
    """
    Save session to secure storage.

    Args:
        session: Session to save.
        platform_info: Optional platform info.

    Returns:
        Tuple of (success, message).
    """
    try:
        session_path = get_session_file_path(platform_info)

        # Ensure directory exists
        session_path.parent.mkdir(parents=True, exist_ok=True)

        # Write session data
        session_data = session.to_dict()
        session_path.write_text(json.dumps(session_data, indent=2))

        # Secure the file (Unix only)
        if os.name != "nt":
            os.chmod(session_path, 0o600)

        return True, f"Session saved for {session.username}"

    except PermissionError:
        return False, "Permission denied when saving session"
    except Exception as e:
        return False, f"Failed to save session: {e}"


def load_session(
    platform_info: PlatformInfo | None = None,
) -> SessionInfo | None:
    """
    Load session from storage.

    Args:
        platform_info: Optional platform info.

    Returns:
        SessionInfo if found, None otherwise.
    """
    try:
        session_path = get_session_file_path(platform_info)

        if not session_path.exists():
            return None

        session_data = json.loads(session_path.read_text())
        return SessionInfo.from_dict(session_data)

    except (json.JSONDecodeError, KeyError, ValueError):
        # Corrupted session file
        return None
    except Exception:
        return None


def validate_session(
    platform_info: PlatformInfo | None = None,
) -> SessionValidationResult:
    """
    Validate the current session.

    Args:
        platform_info: Optional platform info.

    Returns:
        SessionValidationResult with status and details.
    """
    session = load_session(platform_info)

    if session is None:
        return SessionValidationResult(
            status=SESSION_MISSING,
            session=None,
            message="No active session found. Please login.",
            needs_login=True,
        )

    # Check if session has expired
    if session.is_expired:
        return SessionValidationResult(
            status=SESSION_EXPIRED,
            session=session,
            message=f"Session expired. Last activity was {session.last_activity.strftime('%Y-%m-%d %H:%M:%S')} UTC.",
            needs_login=True,
        )

    # Check device ID matches
    current_device_id = generate_device_id()
    if session.device_id != current_device_id:
        return SessionValidationResult(
            status=SESSION_INVALID,
            session=session,
            message="Session was created on a different device. Please login again.",
            needs_login=True,
        )

    # Session is valid
    hours_left = session.hours_remaining
    return SessionValidationResult(
        status=SESSION_VALID,
        session=session,
        message=f"Welcome back, {session.username}! Session valid for {hours_left:.1f} more hours.",
        needs_login=False,
    )


def refresh_session(
    platform_info: PlatformInfo | None = None,
) -> tuple[bool, str]:
    """
    Refresh the current session's activity timestamp and extend expiration.

    Args:
        platform_info: Optional platform info.

    Returns:
        Tuple of (success, message).
    """
    session = load_session(platform_info)

    if session is None:
        return False, "No session to refresh"

    if session.is_expired:
        return False, "Session has expired and cannot be refreshed"

    # Update activity and extend expiration
    now = datetime.now(timezone.utc)
    session.last_activity = now
    session.expires_at = now + timedelta(hours=SESSION_TIMEOUT_HOURS)

    return save_session(session, platform_info)


def invalidate_session(
    platform_info: PlatformInfo | None = None,
) -> tuple[bool, str]:
    """
    Invalidate (logout) the current session.

    Args:
        platform_info: Optional platform info.

    Returns:
        Tuple of (success, message).
    """
    try:
        session_path = get_session_file_path(platform_info)

        if session_path.exists():
            session_path.unlink()
            return True, "Successfully logged out"

        return True, "No active session"

    except PermissionError:
        return False, "Permission denied when removing session"
    except Exception as e:
        return False, f"Failed to invalidate session: {e}"


def get_session_status_display(
    platform_info: PlatformInfo | None = None,
) -> str:
    """
    Get a formatted status display of the current session.

    Args:
        platform_info: Optional platform info.

    Returns:
        Formatted status string.
    """
    result = validate_session(platform_info)

    if result.status == SESSION_MISSING:
        return "Not logged in"

    if result.status == SESSION_EXPIRED:
        return f"Session expired (was: {result.session.username})"

    if result.status == SESSION_INVALID:
        return "Invalid session"

    # Valid session
    session = result.session
    hours_left = session.hours_remaining

    if hours_left < 1:
        minutes_left = int(session.time_remaining.total_seconds() / 60)
        time_str = f"{minutes_left} minutes"
    else:
        time_str = f"{hours_left:.1f} hours"

    return f"Logged in as {session.username} ({time_str} remaining)"


def needs_login(platform_info: PlatformInfo | None = None) -> bool:
    """
    Check if login is required.

    Args:
        platform_info: Optional platform info.

    Returns:
        True if login is needed.
    """
    result = validate_session(platform_info)
    return result.needs_login


def get_current_user(
    platform_info: PlatformInfo | None = None,
) -> tuple[str | None, str | None]:
    """
    Get current logged-in user info.

    Args:
        platform_info: Optional platform info.

    Returns:
        Tuple of (username, email) or (None, None) if not logged in.
    """
    result = validate_session(platform_info)

    if result.status == SESSION_VALID and result.session:
        return result.session.username, result.session.email

    return None, None


class SessionManager:
    """
    High-level session manager for the AiCippy CLI.

    Provides a convenient interface for session operations with
    automatic platform detection and caching.
    """

    def __init__(self, platform_info: PlatformInfo | None = None) -> None:
        """Initialize session manager."""
        self._platform_info = platform_info or detect_platform()
        self._cached_session: SessionInfo | None = None
        self._last_check: float = 0
        self._check_interval: float = 60.0  # Re-check every 60 seconds

    @property
    def platform_info(self) -> PlatformInfo:
        """Get platform information."""
        return self._platform_info

    def _should_recheck(self) -> bool:
        """Check if we should re-validate the session."""
        return time.monotonic() - self._last_check > self._check_interval

    def login(
        self,
        user_id: str,
        username: str,
        email: str,
        ip_address: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        """
        Create a new login session.

        Args:
            user_id: User's unique ID.
            username: User's display name.
            email: User's email.
            ip_address: Optional IP address.
            metadata: Optional metadata.

        Returns:
            Tuple of (success, message).
        """
        session = create_session(
            user_id=user_id,
            username=username,
            email=email,
            ip_address=ip_address,
            metadata=metadata,
        )

        success, message = save_session(session, self._platform_info)

        if success:
            self._cached_session = session
            self._last_check = time.monotonic()

        return success, message

    def logout(self) -> tuple[bool, str]:
        """
        Logout the current session.

        Returns:
            Tuple of (success, message).
        """
        success, message = invalidate_session(self._platform_info)

        if success:
            self._cached_session = None

        return success, message

    def validate(self) -> SessionValidationResult:
        """
        Validate the current session.

        Returns:
            SessionValidationResult with status.
        """
        # Use cached session if recent
        if self._cached_session and not self._should_recheck():
            if not self._cached_session.is_expired:
                return SessionValidationResult(
                    status=SESSION_VALID,
                    session=self._cached_session,
                    message=f"Welcome back, {self._cached_session.username}!",
                    needs_login=False,
                )

        # Full validation
        result = validate_session(self._platform_info)
        self._last_check = time.monotonic()

        if result.status == SESSION_VALID:
            self._cached_session = result.session
        else:
            self._cached_session = None

        return result

    def refresh(self) -> tuple[bool, str]:
        """
        Refresh the current session.

        Returns:
            Tuple of (success, message).
        """
        success, message = refresh_session(self._platform_info)

        if success:
            self._cached_session = load_session(self._platform_info)
            self._last_check = time.monotonic()

        return success, message

    def needs_login(self) -> bool:
        """
        Check if login is required.

        Returns:
            True if login needed.
        """
        return self.validate().needs_login

    def get_user(self) -> tuple[str | None, str | None]:
        """
        Get current user info.

        Returns:
            Tuple of (username, email).
        """
        result = self.validate()

        if result.status == SESSION_VALID and result.session:
            return result.session.username, result.session.email

        return None, None

    def get_status(self) -> str:
        """
        Get formatted session status.

        Returns:
            Status string.
        """
        return get_session_status_display(self._platform_info)

    def touch(self) -> None:
        """Update session activity without full refresh."""
        if self._cached_session and not self._cached_session.is_expired:
            self._cached_session.last_activity = datetime.now(timezone.utc)
            # Save periodically (every 5 minutes of activity)
            if self._should_recheck():
                self.refresh()
