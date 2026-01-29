"""
Permission Manager for AiCippy Installer.

Handles file and folder permissions across Windows, macOS, and Linux
to ensure proper access for temp, cache, and application directories.
"""

from __future__ import annotations

import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, TYPE_CHECKING

# Unix-only imports - handle gracefully on Windows
if os.name != "nt":
    import grp
    import pwd
else:
    grp = None  # type: ignore[assignment]
    pwd = None  # type: ignore[assignment]

from aicippy.installer.platform_detect import (
    OperatingSystem,
    PlatformInfo,
    run_shell_command,
)

# Permission modes for directories
DIR_PERMISSION_PRIVATE: Final[int] = 0o700  # rwx------
DIR_PERMISSION_SHARED: Final[int] = 0o755   # rwxr-xr-x
DIR_PERMISSION_FULL: Final[int] = 0o777     # rwxrwxrwx

# Permission modes for files
FILE_PERMISSION_PRIVATE: Final[int] = 0o600  # rw-------
FILE_PERMISSION_EXECUTABLE: Final[int] = 0o755  # rwxr-xr-x
FILE_PERMISSION_READONLY: Final[int] = 0o644  # rw-r--r--


@dataclass
class PermissionResult:
    """Result of a permission operation."""

    success: bool
    path: Path
    message: str
    error: str | None = None


@dataclass
class DirectorySetup:
    """Configuration for setting up a directory."""

    path: Path
    description: str
    mode: int
    create_if_missing: bool = True
    recursive: bool = True


def get_required_directories(platform_info: PlatformInfo) -> list[DirectorySetup]:
    """
    Get the list of directories that need to be created/configured.

    Args:
        platform_info: Platform information.

    Returns:
        List of DirectorySetup configurations.
    """
    return [
        DirectorySetup(
            path=platform_info.config_path,
            description="Configuration directory",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.cache_path,
            description="Cache directory",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.config_path / "sessions",
            description="Sessions directory",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.config_path / "logs",
            description="Logs directory",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.config_path / "tokens",
            description="Token storage directory",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.cache_path / "downloads",
            description="Downloads cache",
            mode=DIR_PERMISSION_PRIVATE,
        ),
        DirectorySetup(
            path=platform_info.cache_path / "kb",
            description="Knowledge base cache",
            mode=DIR_PERMISSION_PRIVATE,
        ),
    ]


def create_directory_unix(
    dir_setup: DirectorySetup,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Create and configure directory on Unix systems.

    Args:
        dir_setup: Directory setup configuration.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    path = dir_setup.path.expanduser()

    try:
        # Create directory
        if dir_setup.create_if_missing:
            path.mkdir(parents=dir_setup.recursive, exist_ok=True)

        # Set permissions
        os.chmod(path, dir_setup.mode)

        # Verify
        if path.exists() and path.is_dir():
            return PermissionResult(
                success=True,
                path=path,
                message=f"Created {dir_setup.description}: {path}",
            )
        else:
            return PermissionResult(
                success=False,
                path=path,
                message=f"Failed to create {dir_setup.description}",
                error="Directory does not exist after creation",
            )

    except PermissionError as e:
        return PermissionResult(
            success=False,
            path=path,
            message=f"Permission denied for {dir_setup.description}",
            error=str(e),
        )
    except Exception as e:
        return PermissionResult(
            success=False,
            path=path,
            message=f"Error creating {dir_setup.description}",
            error=str(e),
        )


def create_directory_windows(
    dir_setup: DirectorySetup,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Create and configure directory on Windows.

    Args:
        dir_setup: Directory setup configuration.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    path = dir_setup.path.expanduser()

    try:
        # Create directory
        if dir_setup.create_if_missing:
            path.mkdir(parents=dir_setup.recursive, exist_ok=True)

        # Set permissions using icacls (Windows ACL)
        # Grant full control to current user
        username = os.environ.get("USERNAME", "")
        if username:
            cmd = f'icacls "{path}" /grant "{username}:(OI)(CI)F" /T /Q'
            result = run_shell_command(cmd, platform_info, capture_output=True)
            if result.returncode != 0:
                # Non-fatal - directory was created
                pass

        if path.exists() and path.is_dir():
            return PermissionResult(
                success=True,
                path=path,
                message=f"Created {dir_setup.description}: {path}",
            )
        else:
            return PermissionResult(
                success=False,
                path=path,
                message=f"Failed to create {dir_setup.description}",
                error="Directory does not exist after creation",
            )

    except PermissionError as e:
        return PermissionResult(
            success=False,
            path=path,
            message=f"Permission denied for {dir_setup.description}",
            error=str(e),
        )
    except Exception as e:
        return PermissionResult(
            success=False,
            path=path,
            message=f"Error creating {dir_setup.description}",
            error=str(e),
        )


def create_directory(
    dir_setup: DirectorySetup,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Create and configure directory based on platform.

    Args:
        dir_setup: Directory setup configuration.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    if platform_info.is_windows:
        return create_directory_windows(dir_setup, platform_info)
    else:
        return create_directory_unix(dir_setup, platform_info)


def setup_all_directories(
    platform_info: PlatformInfo,
    progress_callback: Callable[[str, int], None] | None = None,
) -> tuple[bool, list[PermissionResult]]:
    """
    Set up all required directories with proper permissions.

    Args:
        platform_info: Platform information.
        progress_callback: Optional callback for progress updates.

    Returns:
        Tuple of (all_success, list of results).
    """
    directories = get_required_directories(platform_info)
    results: list[PermissionResult] = []
    total = len(directories)

    for i, dir_setup in enumerate(directories):
        if progress_callback:
            pct = int((i / total) * 100)
            progress_callback(f"Setting up {dir_setup.description}...", pct)

        result = create_directory(dir_setup, platform_info)
        results.append(result)

    if progress_callback:
        progress_callback("Directory setup complete", 100)

    all_success = all(r.success for r in results)
    return all_success, results


def set_file_permissions(
    path: Path,
    mode: int,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Set permissions on a file.

    Args:
        path: Path to the file.
        mode: Permission mode.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    try:
        if platform_info.is_windows:
            # Windows handles permissions differently
            # Make file readable/writable by current user
            username = os.environ.get("USERNAME", "")
            if username:
                cmd = f'icacls "{path}" /grant "{username}:F" /Q'
                run_shell_command(cmd, platform_info, capture_output=True)
        else:
            os.chmod(path, mode)

        return PermissionResult(
            success=True,
            path=path,
            message=f"Set permissions on {path}",
        )

    except Exception as e:
        return PermissionResult(
            success=False,
            path=path,
            message=f"Failed to set permissions on {path}",
            error=str(e),
        )


def make_executable(
    path: Path,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Make a file executable.

    Args:
        path: Path to the file.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    return set_file_permissions(path, FILE_PERMISSION_EXECUTABLE, platform_info)


def check_directory_access(
    path: Path,
    read: bool = True,
    write: bool = True,
    execute: bool = True,
) -> tuple[bool, str]:
    """
    Check if the current user has required access to a directory.

    Args:
        path: Path to check.
        read: Check read access.
        write: Check write access.
        execute: Check execute access.

    Returns:
        Tuple of (has_access, message).
    """
    if not path.exists():
        return False, f"Path does not exist: {path}"

    if not path.is_dir():
        return False, f"Path is not a directory: {path}"

    issues = []

    if read and not os.access(path, os.R_OK):
        issues.append("read")
    if write and not os.access(path, os.W_OK):
        issues.append("write")
    if execute and not os.access(path, os.X_OK):
        issues.append("execute")

    if issues:
        return False, f"Missing permissions on {path}: {', '.join(issues)}"

    return True, f"Full access to {path}"


def verify_all_permissions(
    platform_info: PlatformInfo,
) -> tuple[bool, list[tuple[Path, str]]]:
    """
    Verify permissions on all required directories.

    Args:
        platform_info: Platform information.

    Returns:
        Tuple of (all_ok, list of (path, issue) for failures).
    """
    directories = get_required_directories(platform_info)
    issues: list[tuple[Path, str]] = []

    for dir_setup in directories:
        path = dir_setup.path.expanduser()
        if path.exists():
            ok, msg = check_directory_access(path)
            if not ok:
                issues.append((path, msg))
        else:
            issues.append((path, "Directory does not exist"))

    return len(issues) == 0, issues


def secure_file(
    path: Path,
    platform_info: PlatformInfo,
) -> PermissionResult:
    """
    Secure a file with restrictive permissions (for sensitive data).

    Args:
        path: Path to the file.
        platform_info: Platform information.

    Returns:
        PermissionResult with status.
    """
    return set_file_permissions(path, FILE_PERMISSION_PRIVATE, platform_info)


def get_current_user_info() -> tuple[str, str, int, int]:
    """
    Get current user information.

    Returns:
        Tuple of (username, home_dir, uid, gid).
    """
    try:
        if os.name == "nt" or pwd is None:
            # Windows
            username = os.environ.get("USERNAME", "unknown")
            home_dir = os.environ.get("USERPROFILE", "")
            return username, home_dir, 0, 0
        else:
            # Unix
            pw = pwd.getpwuid(os.getuid())
            return pw.pw_name, pw.pw_dir, pw.pw_uid, pw.pw_gid
    except Exception:
        return "unknown", str(Path.home()), 0, 0


def fix_permissions(
    path: Path,
    platform_info: PlatformInfo,
    recursive: bool = False,
) -> tuple[bool, list[str]]:
    """
    Attempt to fix permissions on a path.

    Args:
        path: Path to fix.
        platform_info: Platform information.
        recursive: Whether to fix recursively.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: list[str] = []

    try:
        if platform_info.is_windows:
            username = os.environ.get("USERNAME", "")
            if username:
                recurse_flag = "/T" if recursive else ""
                cmd = f'icacls "{path}" /grant "{username}:(OI)(CI)F" {recurse_flag} /Q'
                result = run_shell_command(cmd, platform_info, capture_output=True)
                if result.returncode != 0:
                    errors.append(f"icacls failed: {result.stderr}")
        else:
            # Unix - set owner to current user
            uid = os.getuid()
            gid = os.getgid()

            if recursive and path.is_dir():
                for item in path.rglob("*"):
                    try:
                        os.chown(item, uid, gid)
                        if item.is_dir():
                            os.chmod(item, DIR_PERMISSION_PRIVATE)
                        else:
                            os.chmod(item, FILE_PERMISSION_PRIVATE)
                    except Exception as e:
                        errors.append(f"Failed to fix {item}: {e}")

            os.chown(path, uid, gid)
            if path.is_dir():
                os.chmod(path, DIR_PERMISSION_PRIVATE)
            else:
                os.chmod(path, FILE_PERMISSION_PRIVATE)

    except Exception as e:
        errors.append(f"Failed to fix permissions: {e}")

    return len(errors) == 0, errors
