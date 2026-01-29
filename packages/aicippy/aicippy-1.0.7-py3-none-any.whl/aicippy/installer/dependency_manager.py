"""
Dependency Manager for AiCippy Installer.

Handles automatic detection and installation of required dependencies
across Windows, macOS, and Linux platforms.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final

from aicippy.installer.platform_detect import (
    OperatingSystem,
    PlatformInfo,
    run_shell_command,
)

# Required Python packages with minimum versions
REQUIRED_PACKAGES: Final[dict[str, str]] = {
    "pydantic": "2.6.0",
    "pydantic-settings": "2.2.0",
    "rich": "13.7.0",
    "typer": "0.12.0",
    "boto3": "1.34.0",
    "botocore": "1.34.0",
    "websockets": "12.0",
    "httpx": "0.27.0",
    "anyio": "4.3.0",
    "keyring": "25.0.0",
    "python-jose": "3.3.0",
    "aiofiles": "23.2.0",
    "tenacity": "8.2.0",
    "structlog": "24.1.0",
    "orjson": "3.9.0",
    "prompt-toolkit": "3.0.43",
    "feedparser": "6.0.11",
    "beautifulsoup4": "4.12.0",
    "lxml": "5.1.0",
    "markdown": "3.5.0",
    "cryptography": "42.0.0",
}

# Optional packages for enhanced features
OPTIONAL_PACKAGES: Final[dict[str, str]] = {
    "uvloop": "0.19.0",  # Unix only - faster event loop
}

# System dependencies per OS (package manager -> packages)
SYSTEM_DEPENDENCIES: Final[dict[OperatingSystem, dict[str, list[str]]]] = {
    OperatingSystem.MACOS: {
        "brew": ["openssl", "libffi"],
    },
    OperatingSystem.LINUX: {
        "apt": ["python3-dev", "libssl-dev", "libffi-dev", "build-essential"],
        "yum": ["python3-devel", "openssl-devel", "libffi-devel", "gcc"],
        "dnf": ["python3-devel", "openssl-devel", "libffi-devel", "gcc"],
        "pacman": ["python", "openssl", "libffi", "base-devel"],
    },
    OperatingSystem.WINDOWS: {},  # Windows doesn't need system packages
}


@dataclass
class PackageStatus:
    """Status of a package installation."""

    name: str
    required_version: str
    installed_version: str | None
    is_installed: bool
    needs_upgrade: bool
    error: str | None = None


@dataclass
class DependencyCheckResult:
    """Result of dependency check."""

    packages: list[PackageStatus]
    missing_count: int
    upgrade_count: int
    all_satisfied: bool
    errors: list[str]


def parse_version(version_str: str) -> tuple[int, ...]:
    """
    Parse version string to comparable tuple.

    Args:
        version_str: Version string like "1.2.3".

    Returns:
        Tuple of version numbers.
    """
    try:
        # Handle versions like "1.2.3.post1" or "1.2.3a1"
        clean = version_str.split("+")[0].split(".post")[0].split("a")[0].split("b")[0]
        parts = clean.split(".")
        return tuple(int(p) for p in parts if p.isdigit())
    except (ValueError, AttributeError):
        return (0,)


def compare_versions(installed: str, required: str) -> int:
    """
    Compare two version strings.

    Args:
        installed: Installed version string.
        required: Required version string.

    Returns:
        -1 if installed < required, 0 if equal, 1 if installed > required.
    """
    inst_tuple = parse_version(installed)
    req_tuple = parse_version(required)

    # Pad shorter tuple with zeros
    max_len = max(len(inst_tuple), len(req_tuple))
    inst_tuple = inst_tuple + (0,) * (max_len - len(inst_tuple))
    req_tuple = req_tuple + (0,) * (max_len - len(req_tuple))

    if inst_tuple < req_tuple:
        return -1
    elif inst_tuple > req_tuple:
        return 1
    return 0


def get_installed_packages() -> dict[str, str]:
    """
    Get all installed Python packages and their versions.

    Returns:
        Dictionary of package_name -> version.
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            packages = json.loads(result.stdout)
            return {
                pkg["name"].lower().replace("_", "-"): pkg["version"]
                for pkg in packages
            }
    except Exception:
        pass

    # Fallback: try pip freeze
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            packages = {}
            for line in result.stdout.strip().split("\n"):
                if "==" in line:
                    name, version = line.split("==", 1)
                    packages[name.lower().replace("_", "-")] = version
            return packages
    except Exception:
        pass

    return {}


def check_package_status(
    name: str,
    required_version: str,
    installed_packages: dict[str, str],
) -> PackageStatus:
    """
    Check the installation status of a single package.

    Args:
        name: Package name.
        required_version: Minimum required version.
        installed_packages: Dictionary of installed packages.

    Returns:
        PackageStatus for the package.
    """
    # Normalize name
    normalized_name = name.lower().replace("_", "-")
    installed_version = installed_packages.get(normalized_name)

    if installed_version is None:
        return PackageStatus(
            name=name,
            required_version=required_version,
            installed_version=None,
            is_installed=False,
            needs_upgrade=False,
        )

    needs_upgrade = compare_versions(installed_version, required_version) < 0

    return PackageStatus(
        name=name,
        required_version=required_version,
        installed_version=installed_version,
        is_installed=True,
        needs_upgrade=needs_upgrade,
    )


def check_dependencies(
    include_optional: bool = False,
) -> DependencyCheckResult:
    """
    Check all required dependencies.

    Args:
        include_optional: Whether to include optional packages.

    Returns:
        DependencyCheckResult with status of all packages.
    """
    installed = get_installed_packages()
    packages_to_check = dict(REQUIRED_PACKAGES)

    if include_optional:
        packages_to_check.update(OPTIONAL_PACKAGES)

    statuses: list[PackageStatus] = []
    errors: list[str] = []

    for name, version in packages_to_check.items():
        status = check_package_status(name, version, installed)
        statuses.append(status)

    missing_count = sum(1 for s in statuses if not s.is_installed)
    upgrade_count = sum(1 for s in statuses if s.needs_upgrade)

    return DependencyCheckResult(
        packages=statuses,
        missing_count=missing_count,
        upgrade_count=upgrade_count,
        all_satisfied=missing_count == 0 and upgrade_count == 0,
        errors=errors,
    )


def detect_package_manager(platform_info: PlatformInfo) -> str | None:
    """
    Detect the available package manager on Unix systems.

    Args:
        platform_info: Platform information.

    Returns:
        Package manager name or None.
    """
    if platform_info.is_windows:
        return None

    if platform_info.is_macos:
        # Check for Homebrew
        result = run_shell_command("which brew", platform_info, capture_output=True)
        if result.returncode == 0:
            return "brew"
        return None

    # Linux - check for various package managers
    managers = ["apt", "apt-get", "yum", "dnf", "pacman", "zypper"]
    for manager in managers:
        result = run_shell_command(f"which {manager}", platform_info, capture_output=True)
        if result.returncode == 0:
            # Normalize apt-get to apt
            return "apt" if manager == "apt-get" else manager

    return None


def install_system_dependencies(
    platform_info: PlatformInfo,
    progress_callback: Callable[[str, int], None] | None = None,
) -> tuple[bool, list[str]]:
    """
    Install system-level dependencies.

    Args:
        platform_info: Platform information.
        progress_callback: Optional callback for progress updates.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: list[str] = []

    if platform_info.is_windows:
        # Windows doesn't typically need system packages
        return True, errors

    package_manager = detect_package_manager(platform_info)
    if package_manager is None:
        return True, errors  # No package manager, skip system deps

    deps = SYSTEM_DEPENDENCIES.get(platform_info.os_type, {})
    packages = deps.get(package_manager, [])

    if not packages:
        return True, errors

    if progress_callback:
        progress_callback("Installing system dependencies...", 0)

    # Build install command
    if package_manager == "brew":
        cmd = f"brew install {' '.join(packages)}"
        use_sudo = False
    elif package_manager in ("apt", "apt-get"):
        cmd = f"apt-get update && apt-get install -y {' '.join(packages)}"
        use_sudo = not platform_info.is_admin
    elif package_manager in ("yum", "dnf"):
        cmd = f"{package_manager} install -y {' '.join(packages)}"
        use_sudo = not platform_info.is_admin
    elif package_manager == "pacman":
        cmd = f"pacman -S --noconfirm {' '.join(packages)}"
        use_sudo = not platform_info.is_admin
    else:
        return True, errors

    if use_sudo and platform_info.has_sudo:
        cmd = f"sudo {cmd}"
    elif use_sudo and not platform_info.has_sudo:
        errors.append("System dependencies require root privileges. Please run with sudo.")
        return False, errors

    try:
        result = run_shell_command(cmd, platform_info, capture_output=True, timeout=300)
        if result.returncode != 0:
            errors.append(f"Failed to install system dependencies: {result.stderr}")
            return False, errors
    except subprocess.TimeoutExpired:
        errors.append("System dependency installation timed out")
        return False, errors
    except Exception as e:
        errors.append(f"Error installing system dependencies: {e}")
        return False, errors

    if progress_callback:
        progress_callback("System dependencies installed", 100)

    return True, errors


def install_python_packages(
    packages: list[PackageStatus],
    platform_info: PlatformInfo,
    progress_callback: Callable[[str, int], None] | None = None,
    upgrade_pip: bool = True,
) -> tuple[bool, list[str]]:
    """
    Install or upgrade Python packages.

    Args:
        packages: List of packages to install/upgrade.
        platform_info: Platform information.
        progress_callback: Optional callback for progress updates.
        upgrade_pip: Whether to upgrade pip first.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: list[str] = []
    total = len(packages) + (1 if upgrade_pip else 0)
    current = 0

    # Upgrade pip first
    if upgrade_pip:
        if progress_callback:
            progress_callback("Upgrading pip...", int(current / total * 100))

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode != 0:
                errors.append(f"Warning: pip upgrade failed: {result.stderr}")
        except Exception as e:
            errors.append(f"Warning: pip upgrade failed: {e}")

        current += 1

    # Install/upgrade packages
    for pkg in packages:
        if progress_callback:
            action = "Upgrading" if pkg.needs_upgrade else "Installing"
            progress_callback(f"{action} {pkg.name}...", int(current / total * 100))

        package_spec = f"{pkg.name}>={pkg.required_version}"

        try:
            cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_spec]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                errors.append(f"Failed to install {pkg.name}: {result.stderr}")
        except subprocess.TimeoutExpired:
            errors.append(f"Installation of {pkg.name} timed out")
        except Exception as e:
            errors.append(f"Error installing {pkg.name}: {e}")

        current += 1

    if progress_callback:
        progress_callback("Package installation complete", 100)

    return len(errors) == 0, errors


def install_all_dependencies(
    platform_info: PlatformInfo,
    progress_callback: Callable[[str, int], None] | None = None,
    include_optional: bool = False,
) -> tuple[bool, list[str]]:
    """
    Install all required dependencies.

    Args:
        platform_info: Platform information.
        progress_callback: Optional callback for progress updates.
        include_optional: Whether to include optional packages.

    Returns:
        Tuple of (success, list of errors).
    """
    all_errors: list[str] = []

    # Phase 1: System dependencies
    if progress_callback:
        progress_callback("Checking system dependencies...", 0)

    success, errors = install_system_dependencies(platform_info, progress_callback)
    all_errors.extend(errors)

    # Phase 2: Check Python packages
    if progress_callback:
        progress_callback("Checking Python packages...", 25)

    check_result = check_dependencies(include_optional)

    # Get packages that need installation or upgrade
    packages_to_install = [
        pkg for pkg in check_result.packages
        if not pkg.is_installed or pkg.needs_upgrade
    ]

    if not packages_to_install:
        if progress_callback:
            progress_callback("All dependencies satisfied", 100)
        return True, all_errors

    # Phase 3: Install Python packages
    def wrapped_callback(msg: str, pct: int) -> None:
        if progress_callback:
            # Scale 0-100 to 25-100
            scaled_pct = 25 + int(pct * 0.75)
            progress_callback(msg, scaled_pct)

    success, errors = install_python_packages(
        packages_to_install,
        platform_info,
        wrapped_callback,
    )
    all_errors.extend(errors)

    return len(all_errors) == 0, all_errors


def verify_installation() -> tuple[bool, str]:
    """
    Verify that all dependencies are properly installed.

    Returns:
        Tuple of (success, message).
    """
    result = check_dependencies()

    if result.all_satisfied:
        return True, "All dependencies verified successfully"

    messages = []
    for pkg in result.packages:
        if not pkg.is_installed:
            messages.append(f"Missing: {pkg.name} (>={pkg.required_version})")
        elif pkg.needs_upgrade:
            messages.append(
                f"Needs upgrade: {pkg.name} "
                f"({pkg.installed_version} -> >={pkg.required_version})"
            )

    return False, "\n".join(messages)
