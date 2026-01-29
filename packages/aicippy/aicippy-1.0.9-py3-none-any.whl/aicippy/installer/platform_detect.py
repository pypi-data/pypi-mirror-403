"""
Platform Detection Module for AiCippy Installer.

Detects operating system, shell type, and system configuration
to enable cross-platform installation support.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Final


class OperatingSystem(Enum):
    """Supported operating systems."""

    WINDOWS = auto()
    MACOS = auto()
    LINUX = auto()
    UNKNOWN = auto()


class ShellType(Enum):
    """Shell types for command execution."""

    POWERSHELL = auto()
    CMD = auto()
    BASH = auto()
    ZSH = auto()
    FISH = auto()
    SH = auto()
    UNKNOWN = auto()


class Architecture(Enum):
    """CPU architecture types."""

    X86_64 = auto()
    ARM64 = auto()
    X86 = auto()
    ARM = auto()
    UNKNOWN = auto()


# Default installation paths per OS
DEFAULT_INSTALL_PATHS: Final[dict[OperatingSystem, Path]] = {
    OperatingSystem.WINDOWS: Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "AiCippy",
    OperatingSystem.MACOS: Path("/usr/local/opt/aicippy"),
    OperatingSystem.LINUX: Path("/opt/aicippy"),
}

# User-level installation paths
USER_INSTALL_PATHS: Final[dict[OperatingSystem, Path]] = {
    OperatingSystem.WINDOWS: Path(os.environ.get("LOCALAPPDATA", "~")) / "Programs" / "AiCippy",
    OperatingSystem.MACOS: Path("~/Library/Application Support/AiCippy"),
    OperatingSystem.LINUX: Path("~/.local/share/aicippy"),
}

# Cache/temp directory paths
CACHE_PATHS: Final[dict[OperatingSystem, Path]] = {
    OperatingSystem.WINDOWS: Path(os.environ.get("TEMP", "C:\\Temp")) / "aicippy",
    OperatingSystem.MACOS: Path("~/Library/Caches/aicippy"),
    OperatingSystem.LINUX: Path("~/.cache/aicippy"),
}

# Config directory paths
CONFIG_PATHS: Final[dict[OperatingSystem, Path]] = {
    OperatingSystem.WINDOWS: Path(os.environ.get("APPDATA", "~")) / "AiCippy",
    OperatingSystem.MACOS: Path("~/.aicippy"),
    OperatingSystem.LINUX: Path("~/.aicippy"),
}

# Minimum Python version
MIN_PYTHON_VERSION: Final[tuple[int, int]] = (3, 11)


@dataclass
class PlatformInfo:
    """Complete platform information."""

    os_type: OperatingSystem
    os_name: str
    os_version: str
    architecture: Architecture
    shell_type: ShellType
    python_version: tuple[int, int, int]
    python_path: Path
    pip_path: Path | None
    is_admin: bool
    home_dir: Path
    install_path: Path
    user_install_path: Path
    cache_path: Path
    config_path: Path
    path_separator: str
    env_path_key: str
    has_sudo: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def python_meets_minimum(self) -> bool:
        """Check if Python version meets minimum requirement."""
        return self.python_version[:2] >= MIN_PYTHON_VERSION

    @property
    def is_windows(self) -> bool:
        """Check if running on Windows."""
        return self.os_type == OperatingSystem.WINDOWS

    @property
    def is_macos(self) -> bool:
        """Check if running on macOS."""
        return self.os_type == OperatingSystem.MACOS

    @property
    def is_linux(self) -> bool:
        """Check if running on Linux."""
        return self.os_type == OperatingSystem.LINUX

    @property
    def is_unix(self) -> bool:
        """Check if running on Unix-like system."""
        return self.os_type in (OperatingSystem.MACOS, OperatingSystem.LINUX)


def detect_os() -> OperatingSystem:
    """Detect the operating system."""
    system = platform.system().lower()
    if system == "windows":
        return OperatingSystem.WINDOWS
    elif system == "darwin":
        return OperatingSystem.MACOS
    elif system == "linux":
        return OperatingSystem.LINUX
    return OperatingSystem.UNKNOWN


def detect_architecture() -> Architecture:
    """Detect CPU architecture."""
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return Architecture.X86_64
    elif machine in ("arm64", "aarch64"):
        return Architecture.ARM64
    elif machine in ("i386", "i686", "x86"):
        return Architecture.X86
    elif machine.startswith("arm"):
        return Architecture.ARM
    return Architecture.UNKNOWN


def detect_shell() -> ShellType:
    """Detect the current shell type."""
    os_type = detect_os()

    if os_type == OperatingSystem.WINDOWS:
        # Check for PowerShell
        if os.environ.get("PSModulePath"):
            return ShellType.POWERSHELL
        return ShellType.CMD

    # Unix-like systems
    shell = os.environ.get("SHELL", "").lower()
    if "zsh" in shell:
        return ShellType.ZSH
    elif "bash" in shell:
        return ShellType.BASH
    elif "fish" in shell:
        return ShellType.FISH
    elif "sh" in shell:
        return ShellType.SH
    return ShellType.UNKNOWN


def detect_pip_path() -> Path | None:
    """Find pip executable path."""
    # Try pip3 first, then pip
    for pip_name in ("pip3", "pip"):
        pip_path = shutil.which(pip_name)
        if pip_path:
            return Path(pip_path)
    return None


def check_admin_privileges() -> bool:
    """Check if running with admin/root privileges."""
    os_type = detect_os()

    if os_type == OperatingSystem.WINDOWS:
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0


def check_sudo_available() -> bool:
    """Check if sudo is available on Unix systems."""
    os_type = detect_os()
    if os_type == OperatingSystem.WINDOWS:
        return False
    return shutil.which("sudo") is not None


def get_python_version() -> tuple[int, int, int]:
    """Get current Python version as tuple."""
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def detect_platform() -> PlatformInfo:
    """
    Detect complete platform information.

    Returns:
        PlatformInfo with all detected system information.
    """
    os_type = detect_os()
    errors: list[str] = []

    # Get paths with expansion
    home_dir = Path.home()

    install_path = DEFAULT_INSTALL_PATHS.get(
        os_type, Path("/opt/aicippy")
    )
    user_install_path = USER_INSTALL_PATHS.get(
        os_type, home_dir / ".local" / "share" / "aicippy"
    ).expanduser()
    cache_path = CACHE_PATHS.get(
        os_type, home_dir / ".cache" / "aicippy"
    ).expanduser()
    config_path = CONFIG_PATHS.get(
        os_type, home_dir / ".aicippy"
    ).expanduser()

    # Detect pip
    pip_path = detect_pip_path()
    if pip_path is None:
        errors.append("pip not found in PATH")

    # Python version check
    py_version = get_python_version()
    if py_version[:2] < MIN_PYTHON_VERSION:
        errors.append(
            f"Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+ required, "
            f"found {py_version[0]}.{py_version[1]}"
        )

    return PlatformInfo(
        os_type=os_type,
        os_name=platform.system(),
        os_version=platform.release(),
        architecture=detect_architecture(),
        shell_type=detect_shell(),
        python_version=py_version,
        python_path=Path(sys.executable),
        pip_path=pip_path,
        is_admin=check_admin_privileges(),
        home_dir=home_dir,
        install_path=install_path,
        user_install_path=user_install_path,
        cache_path=cache_path,
        config_path=config_path,
        path_separator=";" if os_type == OperatingSystem.WINDOWS else ":",
        env_path_key="Path" if os_type == OperatingSystem.WINDOWS else "PATH",
        has_sudo=check_sudo_available(),
        errors=errors,
    )


def get_shell_profile_path(platform_info: PlatformInfo) -> Path | None:
    """
    Get the shell profile path for adding to PATH.

    Args:
        platform_info: Platform information.

    Returns:
        Path to shell profile or None if not applicable.
    """
    if platform_info.is_windows:
        return None  # Windows uses registry

    home = platform_info.home_dir
    shell = platform_info.shell_type

    profiles = {
        ShellType.ZSH: home / ".zshrc",
        ShellType.BASH: home / ".bashrc",
        ShellType.FISH: home / ".config" / "fish" / "config.fish",
        ShellType.SH: home / ".profile",
    }

    # Check for .bash_profile on macOS
    if platform_info.is_macos and shell == ShellType.BASH:
        bash_profile = home / ".bash_profile"
        if bash_profile.exists():
            return bash_profile

    return profiles.get(shell, home / ".profile")


def run_shell_command(
    command: str | list[str],
    platform_info: PlatformInfo,
    capture_output: bool = True,
    check: bool = False,
    timeout: int | None = 60,
) -> subprocess.CompletedProcess[str]:
    """
    Run a shell command appropriate for the platform.

    Args:
        command: Command to run (string or list).
        platform_info: Platform information.
        capture_output: Whether to capture stdout/stderr.
        check: Whether to raise on non-zero exit.
        timeout: Timeout in seconds.

    Returns:
        CompletedProcess result.
    """
    if platform_info.is_windows:
        if platform_info.shell_type == ShellType.POWERSHELL:
            if isinstance(command, str):
                cmd = ["powershell", "-NoProfile", "-Command", command]
            else:
                cmd = ["powershell", "-NoProfile", "-Command"] + command
        else:
            if isinstance(command, str):
                cmd = ["cmd", "/c", command]
            else:
                cmd = ["cmd", "/c"] + command
    else:
        if isinstance(command, str):
            cmd = command
            shell = True
        else:
            cmd = command
            shell = False

    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=check,
        timeout=timeout,
        shell=shell if platform_info.is_unix and isinstance(command, str) else False,
    )


def format_path_for_shell(path: Path, platform_info: PlatformInfo) -> str:
    """
    Format a path appropriately for the shell.

    Args:
        path: Path to format.
        platform_info: Platform information.

    Returns:
        Formatted path string.
    """
    if platform_info.is_windows:
        return str(path).replace("/", "\\")
    return str(path)
