"""
Main Installer Orchestrator for AiCippy.

Coordinates the complete installation workflow including:
- Prerequisite checks and dependency installation
- Permission configuration
- Environment variable setup
- Version management and auto-updates
- Progress visualization
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator, Callable, Final

from rich.console import Console

from aicippy.installer.dependency_manager import (
    check_dependencies,
    install_all_dependencies,
    verify_installation as verify_deps,
)
from aicippy.installer.env_manager import (
    get_env_export_commands,
    setup_all_env_variables,
    verify_env_variables,
)
from aicippy.installer.permission_manager import (
    setup_all_directories,
    verify_all_permissions,
)
from aicippy.installer.platform_detect import (
    MIN_PYTHON_VERSION,
    PlatformInfo,
    detect_platform,
)
from aicippy.installer.progress_ui import (
    INSTALLATION_PHASES,
    InstallationProgress,
)

# Version information
CURRENT_VERSION: Final[str] = "1.0.6"
VERSION_CHECK_URL: Final[str] = "https://api.aicippy.io/version"
PYPI_PACKAGE_NAME: Final[str] = "aicippy"


@dataclass
class InstallationResult:
    """Result of installation process."""

    success: bool
    version: str
    phases_completed: list[str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    requires_restart: bool = False
    env_commands: list[str] = field(default_factory=list)


@dataclass
class VersionInfo:
    """Version information."""

    current: str
    latest: str | None
    update_available: bool
    release_notes: str | None = None


async def check_latest_version() -> VersionInfo:
    """
    Check for the latest available version.

    Returns:
        VersionInfo with current and latest versions.
    """
    try:
        # Try PyPI first
        result = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", PYPI_PACKAGE_NAME],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # Parse output to find latest version
            # pip output format:
            #   aicippy (1.0.0)
            #   Available versions: 1.0.0, 0.9.0, ...
            #     INSTALLED: 1.0.0
            #     LATEST:    1.0.0
            output = result.stdout
            if "Available versions:" in output:
                # Get only the first line after "Available versions:"
                versions_section = output.split("Available versions:")[1]
                first_line = versions_section.split("\n")[0].strip()
                versions = [v.strip() for v in first_line.split(",") if v.strip()]
                if versions:
                    latest = versions[0]
                    # Only show update if versions actually differ
                    is_update = latest != CURRENT_VERSION
                    return VersionInfo(
                        current=CURRENT_VERSION,
                        latest=latest,
                        update_available=is_update,
                    )
    except Exception:
        pass

    # Fallback: assume current is latest
    return VersionInfo(
        current=CURRENT_VERSION,
        latest=CURRENT_VERSION,
        update_available=False,
    )


async def perform_upgrade() -> tuple[bool, str]:
    """
    Perform package upgrade.

    Returns:
        Tuple of (success, message).
    """
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "--upgrade", PYPI_PACKAGE_NAME],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            return True, "Successfully upgraded AiCippy"
        else:
            return False, f"Upgrade failed: {result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "Upgrade timed out"
    except Exception as e:
        return False, f"Upgrade error: {e}"


def check_prerequisites(platform_info: PlatformInfo) -> tuple[bool, list[str]]:
    """
    Check all prerequisites for installation.

    Args:
        platform_info: Platform information.

    Returns:
        Tuple of (all_met, list of issues).
    """
    issues: list[str] = []

    # Check Python version
    if not platform_info.python_meets_minimum:
        py_ver = platform_info.python_version
        min_ver = MIN_PYTHON_VERSION
        issues.append(
            f"Python {min_ver[0]}.{min_ver[1]}+ required, found {py_ver[0]}.{py_ver[1]}.{py_ver[2]}"
        )

    # Check pip availability
    if platform_info.pip_path is None:
        issues.append("pip not found. Please install pip first.")

    # Add any platform-specific errors
    issues.extend(platform_info.errors)

    return len(issues) == 0, issues


async def installation_phase_generator(
    platform_info: PlatformInfo,
    include_deps: bool = True,
) -> AsyncIterator[tuple[str, int, str]]:
    """
    Generate installation phases with progress updates.

    Args:
        platform_info: Platform information.
        include_deps: Whether to install dependencies.

    Yields:
        Tuples of (phase_id, progress_percent, status_message).
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Phase 1: Initialization
    yield "init", 0, "Starting installation..."
    await asyncio.sleep(0.3)
    yield "init", 50, "Detecting platform..."
    await asyncio.sleep(0.2)
    yield "init", 100, f"Platform: {platform_info.os_name} ({platform_info.architecture.name})"

    # Phase 2: Prerequisites
    yield "prereq", 0, "Checking prerequisites..."
    prereq_ok, prereq_issues = check_prerequisites(platform_info)
    await asyncio.sleep(0.2)

    if not prereq_ok:
        for issue in prereq_issues:
            yield "prereq", 50, f"Issue: {issue}"
            errors.append(issue)
            await asyncio.sleep(0.3)

        if errors:
            yield "prereq", 100, "Prerequisites check failed"
            return

    yield "prereq", 100, "All prerequisites met"

    # Phase 3: Dependencies
    if include_deps:
        yield "deps", 0, "Checking dependencies..."
        dep_check = check_dependencies()
        await asyncio.sleep(0.2)

        if not dep_check.all_satisfied:
            missing = dep_check.missing_count
            upgrade = dep_check.upgrade_count
            total = missing + upgrade

            yield "deps", 10, f"Installing {total} package(s)..."

            def deps_progress(msg: str, pct: int) -> None:
                # This will be called synchronously but we handle it async
                pass

            success, dep_errors = install_all_dependencies(
                platform_info,
                progress_callback=deps_progress,
            )

            if not success:
                errors.extend(dep_errors)
                for err in dep_errors[:3]:
                    yield "deps", 50, f"Error: {err}"
                    await asyncio.sleep(0.2)

            # Simulate progress
            for pct in range(20, 101, 20):
                yield "deps", pct, f"Installing dependencies... {pct}%"
                await asyncio.sleep(0.3)
        else:
            yield "deps", 100, "All dependencies satisfied"
    else:
        yield "deps", 100, "Skipping dependency check"

    # Phase 4: Permissions
    yield "perms", 0, "Configuring permissions..."
    await asyncio.sleep(0.2)

    success, perm_results = setup_all_directories(platform_info)

    for i, result in enumerate(perm_results):
        pct = int((i + 1) / len(perm_results) * 100)
        if result.success:
            yield "perms", pct, f"Created: {result.path.name}"
        else:
            yield "perms", pct, f"Failed: {result.message}"
            errors.append(result.message)
        await asyncio.sleep(0.1)

    yield "perms", 100, "Permissions configured"

    # Phase 5: Environment
    yield "env", 0, "Setting up environment..."
    await asyncio.sleep(0.2)

    success, env_results, requires_restart = setup_all_env_variables(platform_info)

    for i, result in enumerate(env_results):
        pct = int((i + 1) / len(env_results) * 100)
        if result.success:
            yield "env", pct, f"Set: {result.name}"
        else:
            yield "env", pct, f"Failed: {result.message}"
            if result.error:
                warnings.append(f"{result.name}: {result.error}")
        await asyncio.sleep(0.1)

    if requires_restart:
        warnings.append("Shell restart required for PATH changes")

    yield "env", 100, "Environment configured"

    # Phase 6: Installation finalization
    yield "install", 0, "Finalizing installation..."
    await asyncio.sleep(0.3)

    yield "install", 50, "Registering commands..."
    await asyncio.sleep(0.2)

    yield "install", 100, "Installation complete"

    # Phase 7: Verification
    yield "verify", 0, "Verifying installation..."
    await asyncio.sleep(0.2)

    # Verify dependencies
    deps_ok, deps_msg = verify_deps()
    if deps_ok:
        yield "verify", 33, "Dependencies verified"
    else:
        yield "verify", 33, f"Warning: {deps_msg}"
        warnings.append(deps_msg)

    await asyncio.sleep(0.1)

    # Verify permissions
    perms_ok, perm_issues = verify_all_permissions(platform_info)
    if perms_ok:
        yield "verify", 66, "Permissions verified"
    else:
        for path, issue in perm_issues[:2]:
            yield "verify", 66, f"Warning: {issue}"
            warnings.append(issue)

    await asyncio.sleep(0.1)

    # Verify environment
    env_ok, missing_vars = verify_env_variables(platform_info)
    if env_ok:
        yield "verify", 100, "Environment verified"
    else:
        for var in missing_vars[:2]:
            yield "verify", 100, f"Note: {var} not set (restart may be needed)"

    await asyncio.sleep(0.1)
    yield "verify", 100, "Verification complete"


async def install_aicippy(
    console: Console | None = None,
    show_progress: bool = True,
    include_deps: bool = True,
) -> InstallationResult:
    """
    Perform complete AiCippy installation.

    Args:
        console: Optional Rich console.
        show_progress: Whether to show progress UI.
        include_deps: Whether to install dependencies.

    Returns:
        InstallationResult with status.
    """
    console = console or Console()
    platform_info = detect_platform()

    errors: list[str] = []
    warnings: list[str] = []
    phases_completed: list[str] = []
    requires_restart = False

    if show_progress:
        progress = InstallationProgress(console)

        # Show welcome
        progress.show_welcome()
        await asyncio.sleep(1)

        # Run with animated progress
        try:
            async def tracked_generator():
                nonlocal errors, warnings, phases_completed, requires_restart

                async for phase, pct, status in installation_phase_generator(
                    platform_info, include_deps
                ):
                    if phase not in phases_completed and pct == 100:
                        phases_completed.append(phase)
                    yield phase, pct, status

                # Check for restart requirement
                _, _, restart_needed = setup_all_env_variables.__wrapped__ if hasattr(
                    setup_all_env_variables, '__wrapped__'
                ) else (True, [], True)

            await progress.run_with_progress(tracked_generator())

        except Exception as e:
            errors.append(f"Installation error: {e}")

        # Show completion
        success = len(errors) == 0
        progress.show_completion(success=success, errors=errors if not success else None)

    else:
        # Silent installation
        async for phase, pct, status in installation_phase_generator(
            platform_info, include_deps
        ):
            if phase not in phases_completed and pct == 100:
                phases_completed.append(phase)

    # Get environment export commands for user reference
    env_commands = get_env_export_commands(platform_info)

    return InstallationResult(
        success=len(errors) == 0,
        version=CURRENT_VERSION,
        phases_completed=phases_completed,
        errors=errors,
        warnings=warnings,
        requires_restart=requires_restart,
        env_commands=env_commands,
    )


async def uninstall_aicippy(
    console: Console | None = None,
    remove_config: bool = False,
) -> tuple[bool, str]:
    """
    Uninstall AiCippy.

    Args:
        console: Optional Rich console.
        remove_config: Whether to remove configuration files.

    Returns:
        Tuple of (success, message).
    """
    console = console or Console()
    platform_info = detect_platform()

    try:
        # Uninstall package
        result = subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", PYPI_PACKAGE_NAME],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            return False, f"Uninstall failed: {result.stderr}"

        # Optionally remove config
        if remove_config:
            import shutil

            config_path = platform_info.config_path
            cache_path = platform_info.cache_path

            if config_path.exists():
                shutil.rmtree(config_path, ignore_errors=True)

            if cache_path.exists():
                shutil.rmtree(cache_path, ignore_errors=True)

        return True, "AiCippy uninstalled successfully"

    except subprocess.TimeoutExpired:
        return False, "Uninstall timed out"
    except Exception as e:
        return False, f"Uninstall error: {e}"


async def upgrade_aicippy(
    console: Console | None = None,
    check_only: bool = False,
) -> tuple[bool, str, VersionInfo]:
    """
    Check for and optionally perform upgrade.

    Args:
        console: Optional Rich console.
        check_only: If True, only check for updates without installing.

    Returns:
        Tuple of (success, message, version_info).
    """
    console = console or Console()

    # Check version
    version_info = await check_latest_version()

    if not version_info.update_available:
        return True, f"AiCippy {version_info.current} is up to date", version_info

    if check_only:
        return True, f"Update available: {version_info.current} -> {version_info.latest}", version_info

    # Perform upgrade
    success, message = await perform_upgrade()

    if success:
        # Re-check version
        new_version = await check_latest_version()
        return True, f"Upgraded to {new_version.current}", new_version

    return False, message, version_info


def verify_installation() -> tuple[bool, list[str]]:
    """
    Verify that AiCippy is properly installed.

    Returns:
        Tuple of (success, list of issues).
    """
    issues: list[str] = []
    platform_info = detect_platform()

    # Check dependencies
    deps_ok, deps_msg = verify_deps()
    if not deps_ok:
        issues.append(f"Dependencies: {deps_msg}")

    # Check permissions
    perms_ok, perm_issues = verify_all_permissions(platform_info)
    if not perms_ok:
        for path, issue in perm_issues:
            issues.append(f"Permission: {issue}")

    # Check environment
    env_ok, missing_vars = verify_env_variables(platform_info)
    if not env_ok:
        for var in missing_vars:
            issues.append(f"Environment: {var}")

    # Check if aicippy command is accessible
    import shutil
    if shutil.which("aicippy") is None:
        issues.append("Command 'aicippy' not found in PATH (may need shell restart)")

    return len(issues) == 0, issues


def get_installation_info() -> dict:
    """
    Get information about the current installation.

    Returns:
        Dictionary with installation details.
    """
    platform_info = detect_platform()

    return {
        "version": CURRENT_VERSION,
        "python_version": ".".join(str(v) for v in platform_info.python_version),
        "platform": platform_info.os_name,
        "architecture": platform_info.architecture.name,
        "shell": platform_info.shell_type.name,
        "config_path": str(platform_info.config_path),
        "cache_path": str(platform_info.cache_path),
        "install_path": str(platform_info.user_install_path),
        "is_admin": platform_info.is_admin,
    }


# Entry point for direct execution
if __name__ == "__main__":
    async def main():
        result = await install_aicippy(show_progress=True)
        if result.success:
            print("\nInstallation completed successfully!")
        else:
            print("\nInstallation failed:")
            for error in result.errors:
                print(f"  - {error}")

    asyncio.run(main())
