"""
AiCippy Installer Package.

Provides comprehensive cross-platform installation with:
- Automatic dependency detection and installation
- System-level permissions configuration
- Environment variable management
- Visual progress with animations
- Session management with auto-login timeout
"""

from __future__ import annotations

from aicippy.installer.main import (
    CURRENT_VERSION,
    InstallationResult,
    VersionInfo,
    check_latest_version,
    get_installation_info,
    install_aicippy,
    perform_upgrade,
    uninstall_aicippy,
    upgrade_aicippy,
    verify_installation,
)
from aicippy.installer.platform_detect import (
    Architecture,
    OperatingSystem,
    PlatformInfo,
    ShellType,
    detect_platform,
)
from aicippy.installer.session_manager import (
    SessionInfo,
    SessionManager,
    SessionValidationResult,
    create_session,
    get_current_user,
    invalidate_session,
    needs_login,
    validate_session,
)

__all__ = [
    # Main installer functions
    "install_aicippy",
    "uninstall_aicippy",
    "upgrade_aicippy",
    "verify_installation",
    "check_latest_version",
    "perform_upgrade",
    "get_installation_info",
    # Version info
    "CURRENT_VERSION",
    "InstallationResult",
    "VersionInfo",
    # Platform detection
    "detect_platform",
    "PlatformInfo",
    "OperatingSystem",
    "ShellType",
    "Architecture",
    # Session management
    "SessionManager",
    "SessionInfo",
    "SessionValidationResult",
    "create_session",
    "validate_session",
    "invalidate_session",
    "needs_login",
    "get_current_user",
]
