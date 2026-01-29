"""
Environment Variable Manager for AiCippy Installer.

Handles system and user-level environment variable configuration
across Windows, macOS, and Linux platforms.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Final, Literal

from aicippy.installer.platform_detect import (
    OperatingSystem,
    PlatformInfo,
    ShellType,
    get_shell_profile_path,
    run_shell_command,
)

# Environment variable names
ENV_AICIPPY_HOME: Final[str] = "AICIPPY_HOME"
ENV_AICIPPY_CONFIG: Final[str] = "AICIPPY_CONFIG"
ENV_AICIPPY_CACHE: Final[str] = "AICIPPY_CACHE"
ENV_AICIPPY_LOG_LEVEL: Final[str] = "AICIPPY_LOG_LEVEL"

# Default values
DEFAULT_LOG_LEVEL: Final[str] = "INFO"


@dataclass
class EnvVariable:
    """Environment variable definition."""

    name: str
    value: str
    description: str
    scope: Literal["system", "user"] = "user"
    append_to_path: bool = False


@dataclass
class EnvSetResult:
    """Result of setting an environment variable."""

    success: bool
    name: str
    value: str
    scope: str
    message: str
    error: str | None = None
    requires_restart: bool = False


def get_required_env_variables(platform_info: PlatformInfo) -> list[EnvVariable]:
    """
    Get the list of environment variables to configure.

    Args:
        platform_info: Platform information.

    Returns:
        List of EnvVariable configurations.
    """
    # Determine install path (user or system level)
    if platform_info.is_admin:
        install_path = platform_info.install_path
    else:
        install_path = platform_info.user_install_path

    bin_path = install_path / "bin" if platform_info.is_unix else install_path / "Scripts"

    return [
        EnvVariable(
            name=ENV_AICIPPY_HOME,
            value=str(install_path),
            description="AiCippy installation directory",
            scope="user",
        ),
        EnvVariable(
            name=ENV_AICIPPY_CONFIG,
            value=str(platform_info.config_path),
            description="AiCippy configuration directory",
            scope="user",
        ),
        EnvVariable(
            name=ENV_AICIPPY_CACHE,
            value=str(platform_info.cache_path),
            description="AiCippy cache directory",
            scope="user",
        ),
        EnvVariable(
            name=ENV_AICIPPY_LOG_LEVEL,
            value=DEFAULT_LOG_LEVEL,
            description="AiCippy logging level",
            scope="user",
        ),
        EnvVariable(
            name="PATH",
            value=str(bin_path),
            description="Add AiCippy to PATH",
            scope="user",
            append_to_path=True,
        ),
    ]


def check_env_variable(name: str) -> tuple[bool, str | None]:
    """
    Check if an environment variable exists.

    Args:
        name: Variable name.

    Returns:
        Tuple of (exists, current_value).
    """
    value = os.environ.get(name)
    return value is not None, value


def set_env_variable_windows(
    env_var: EnvVariable,
    platform_info: PlatformInfo,
) -> EnvSetResult:
    """
    Set environment variable on Windows using registry.

    Args:
        env_var: Environment variable to set.
        platform_info: Platform information.

    Returns:
        EnvSetResult with status.
    """
    try:
        # Determine registry location based on scope
        if env_var.scope == "system" and platform_info.is_admin:
            reg_path = r"HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
        else:
            reg_path = r"HKCU\Environment"

        if env_var.append_to_path:
            # Get current PATH value
            cmd = f'reg query "{reg_path}" /v {env_var.name}'
            result = run_shell_command(cmd, platform_info, capture_output=True)

            current_path = ""
            if result.returncode == 0:
                # Parse the output to get current PATH
                match = re.search(r"REG_(?:EXPAND_)?SZ\s+(.+)", result.stdout)
                if match:
                    current_path = match.group(1).strip()

            # Check if already in PATH
            path_parts = current_path.split(";")
            if env_var.value not in path_parts:
                new_path = f"{env_var.value};{current_path}" if current_path else env_var.value
            else:
                return EnvSetResult(
                    success=True,
                    name=env_var.name,
                    value=env_var.value,
                    scope=env_var.scope,
                    message=f"{env_var.name} already contains {env_var.value}",
                    requires_restart=False,
                )

            value_to_set = new_path
        else:
            value_to_set = env_var.value

        # Set the variable using setx
        if env_var.scope == "system" and platform_info.is_admin:
            cmd = f'setx /M {env_var.name} "{value_to_set}"'
        else:
            cmd = f'setx {env_var.name} "{value_to_set}"'

        result = run_shell_command(cmd, platform_info, capture_output=True)

        if result.returncode == 0 or "SUCCESS" in result.stdout.upper():
            # Also set in current process
            os.environ[env_var.name] = value_to_set if not env_var.append_to_path else (
                f"{env_var.value}{platform_info.path_separator}{os.environ.get(env_var.name, '')}"
            )

            return EnvSetResult(
                success=True,
                name=env_var.name,
                value=value_to_set,
                scope=env_var.scope,
                message=f"Set {env_var.name}",
                requires_restart=True,
            )
        else:
            return EnvSetResult(
                success=False,
                name=env_var.name,
                value=value_to_set,
                scope=env_var.scope,
                message=f"Failed to set {env_var.name}",
                error=result.stderr or result.stdout,
            )

    except Exception as e:
        return EnvSetResult(
            success=False,
            name=env_var.name,
            value=env_var.value,
            scope=env_var.scope,
            message=f"Error setting {env_var.name}",
            error=str(e),
        )


def set_env_variable_unix(
    env_var: EnvVariable,
    platform_info: PlatformInfo,
) -> EnvSetResult:
    """
    Set environment variable on Unix by updating shell profile.

    Args:
        env_var: Environment variable to set.
        platform_info: Platform information.

    Returns:
        EnvSetResult with status.
    """
    try:
        profile_path = get_shell_profile_path(platform_info)
        if profile_path is None:
            return EnvSetResult(
                success=False,
                name=env_var.name,
                value=env_var.value,
                scope=env_var.scope,
                message=f"Could not determine shell profile for {env_var.name}",
                error="Unknown shell type",
            )

        profile_path = profile_path.expanduser()

        # Read current profile content
        current_content = ""
        if profile_path.exists():
            current_content = profile_path.read_text()

        # Check if variable already set
        export_pattern = re.compile(
            rf'^export\s+{re.escape(env_var.name)}=',
            re.MULTILINE
        )

        if env_var.append_to_path:
            # PATH handling
            path_export = f'export PATH="{env_var.value}:$PATH"'
            marker = f"# AiCippy PATH"

            if marker in current_content:
                return EnvSetResult(
                    success=True,
                    name=env_var.name,
                    value=env_var.value,
                    scope=env_var.scope,
                    message=f"PATH already configured for AiCippy",
                    requires_restart=False,
                )

            new_line = f"\n{marker}\n{path_export}\n"
        else:
            # Regular variable
            new_line = f'\nexport {env_var.name}="{env_var.value}"\n'

            if export_pattern.search(current_content):
                # Update existing
                new_content = export_pattern.sub(
                    f'export {env_var.name}="{env_var.value}"',
                    current_content
                )
                profile_path.write_text(new_content)

                return EnvSetResult(
                    success=True,
                    name=env_var.name,
                    value=env_var.value,
                    scope=env_var.scope,
                    message=f"Updated {env_var.name} in {profile_path}",
                    requires_restart=True,
                )

        # Append new variable
        with open(profile_path, "a") as f:
            f.write(new_line)

        # Set in current process
        if env_var.append_to_path:
            current = os.environ.get(env_var.name, "")
            os.environ[env_var.name] = f"{env_var.value}{platform_info.path_separator}{current}"
        else:
            os.environ[env_var.name] = env_var.value

        return EnvSetResult(
            success=True,
            name=env_var.name,
            value=env_var.value,
            scope=env_var.scope,
            message=f"Added {env_var.name} to {profile_path}",
            requires_restart=True,
        )

    except Exception as e:
        return EnvSetResult(
            success=False,
            name=env_var.name,
            value=env_var.value,
            scope=env_var.scope,
            message=f"Error setting {env_var.name}",
            error=str(e),
        )


def set_env_variable(
    env_var: EnvVariable,
    platform_info: PlatformInfo,
) -> EnvSetResult:
    """
    Set environment variable based on platform.

    Args:
        env_var: Environment variable to set.
        platform_info: Platform information.

    Returns:
        EnvSetResult with status.
    """
    if platform_info.is_windows:
        return set_env_variable_windows(env_var, platform_info)
    else:
        return set_env_variable_unix(env_var, platform_info)


def setup_all_env_variables(
    platform_info: PlatformInfo,
    progress_callback: Callable[[str, int], None] | None = None,
) -> tuple[bool, list[EnvSetResult], bool]:
    """
    Set up all required environment variables.

    Args:
        platform_info: Platform information.
        progress_callback: Optional callback for progress updates.

    Returns:
        Tuple of (all_success, list of results, requires_restart).
    """
    env_vars = get_required_env_variables(platform_info)
    results: list[EnvSetResult] = []
    total = len(env_vars)
    requires_restart = False

    for i, env_var in enumerate(env_vars):
        if progress_callback:
            pct = int((i / total) * 100)
            progress_callback(f"Configuring {env_var.name}...", pct)

        result = set_env_variable(env_var, platform_info)
        results.append(result)

        if result.requires_restart:
            requires_restart = True

    if progress_callback:
        progress_callback("Environment configuration complete", 100)

    all_success = all(r.success for r in results)
    return all_success, results, requires_restart


def verify_env_variables(platform_info: PlatformInfo) -> tuple[bool, list[str]]:
    """
    Verify all required environment variables are set.

    Args:
        platform_info: Platform information.

    Returns:
        Tuple of (all_set, list of missing variables).
    """
    env_vars = get_required_env_variables(platform_info)
    missing: list[str] = []

    for env_var in env_vars:
        if env_var.append_to_path:
            # Check if value is in PATH
            path = os.environ.get("PATH", "")
            if env_var.value not in path:
                missing.append(f"PATH does not contain {env_var.value}")
        else:
            exists, value = check_env_variable(env_var.name)
            if not exists:
                missing.append(env_var.name)

    return len(missing) == 0, missing


def get_env_export_commands(platform_info: PlatformInfo) -> list[str]:
    """
    Get commands to export environment variables for current shell session.

    Args:
        platform_info: Platform information.

    Returns:
        List of export commands.
    """
    env_vars = get_required_env_variables(platform_info)
    commands: list[str] = []

    for env_var in env_vars:
        if platform_info.is_windows:
            if platform_info.shell_type == ShellType.POWERSHELL:
                if env_var.append_to_path:
                    commands.append(f'$env:PATH = "{env_var.value};$env:PATH"')
                else:
                    commands.append(f'$env:{env_var.name} = "{env_var.value}"')
            else:
                if env_var.append_to_path:
                    commands.append(f'set PATH={env_var.value};%PATH%')
                else:
                    commands.append(f'set {env_var.name}={env_var.value}')
        else:
            if env_var.append_to_path:
                commands.append(f'export PATH="{env_var.value}:$PATH"')
            else:
                commands.append(f'export {env_var.name}="{env_var.value}"')

    return commands


def remove_env_variable_unix(name: str, platform_info: PlatformInfo) -> bool:
    """
    Remove an environment variable from Unix shell profile.

    Args:
        name: Variable name.
        platform_info: Platform information.

    Returns:
        True if successful.
    """
    try:
        profile_path = get_shell_profile_path(platform_info)
        if profile_path is None or not profile_path.exists():
            return True

        content = profile_path.read_text()

        # Remove export line
        pattern = re.compile(rf'^export\s+{re.escape(name)}=.*$\n?', re.MULTILINE)
        new_content = pattern.sub('', content)

        # Also remove AiCippy PATH marker if it's a PATH removal
        if name == "PATH":
            marker_pattern = re.compile(r'# AiCippy PATH\n.*\n?', re.MULTILINE)
            new_content = marker_pattern.sub('', new_content)

        profile_path.write_text(new_content)
        return True

    except Exception:
        return False


def remove_env_variable_windows(name: str, platform_info: PlatformInfo) -> bool:
    """
    Remove an environment variable on Windows.

    Args:
        name: Variable name.
        platform_info: Platform information.

    Returns:
        True if successful.
    """
    try:
        # Use reg delete for user variables
        cmd = f'reg delete "HKCU\\Environment" /v {name} /f'
        result = run_shell_command(cmd, platform_info, capture_output=True)
        return result.returncode == 0

    except Exception:
        return False


def cleanup_env_variables(platform_info: PlatformInfo) -> tuple[bool, list[str]]:
    """
    Remove all AiCippy environment variables.

    Args:
        platform_info: Platform information.

    Returns:
        Tuple of (success, list of errors).
    """
    errors: list[str] = []
    env_vars = get_required_env_variables(platform_info)

    for env_var in env_vars:
        if env_var.append_to_path:
            # Skip PATH cleanup - too complex
            continue

        if platform_info.is_windows:
            success = remove_env_variable_windows(env_var.name, platform_info)
        else:
            success = remove_env_variable_unix(env_var.name, platform_info)

        if not success:
            errors.append(f"Failed to remove {env_var.name}")

    return len(errors) == 0, errors
