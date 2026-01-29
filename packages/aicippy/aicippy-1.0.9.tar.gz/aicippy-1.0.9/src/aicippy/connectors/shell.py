"""
Shell connector for AiCippy.

Provides sandboxed shell command execution.
"""

from __future__ import annotations

import os
import shutil
from typing import Any

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus, ToolResult
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)

# Safe commands that are always allowed
SAFE_COMMANDS = frozenset({
    "echo",
    "pwd",
    "whoami",
    "date",
    "hostname",
    "uname",
    "env",
    "printenv",
    "which",
    "type",
    "ls",
    "cat",
    "head",
    "tail",
    "wc",
    "sort",
    "uniq",
    "grep",
    "find",
    "tree",
    "file",
    "stat",
    "du",
    "df",
})

# Dangerous patterns that are blocked
DANGEROUS_PATTERNS = frozenset({
    "rm -rf",
    "rm -fr",
    "sudo",
    "chmod 777",
    "chmod -R",
    "chown",
    "mkfs",
    "dd if",
    "> /dev",
    "curl | sh",
    "wget | sh",
    "curl | bash",
    "wget | bash",
    ":(){:|:&};:",  # Fork bomb
})


class ShellConnector(BaseConnector):
    """
    Shell command connector with sandboxing.

    Provides restricted shell command execution with
    dangerous command blocking.
    """

    name = "bash"
    description = "Shell commands with security sandboxing"
    version = "1.0.0"

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        """Initialize shell connector."""
        if config is None:
            config = ConnectorConfig(sandbox_mode=True)
        super().__init__(config)
        self._shell_path: str | None = None

    async def check_availability(self) -> bool:
        """
        Check if shell is available.

        Returns:
            True (shell is always available).
        """
        self._shell_path = shutil.which("bash") or shutil.which("sh")
        if self._shell_path:
            self._status = ConnectorStatus.AVAILABLE
            return True
        else:
            self._status = ConnectorStatus.UNAVAILABLE
            self._last_error = "No shell found"
            return False

    async def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a shell command.

        Args:
            command: Command to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Check dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern in command:
                return False, f"Dangerous command pattern detected: {pattern}"

        # In sandbox mode, only allow safe commands
        if self.config.sandbox_mode:
            # Extract the base command
            base_cmd = command.strip().split()[0].split("/")[-1]
            if base_cmd not in SAFE_COMMANDS:
                # Check if it's in allowed list
                if not self._is_command_allowed(command):
                    return False, f"Command '{base_cmd}' not allowed in sandbox mode"

        return True, ""

    async def execute(self, command: str, **kwargs: Any) -> ToolResult:
        """
        Execute a shell command.

        Args:
            command: Shell command to execute.
            **kwargs: Additional arguments (cwd, env, timeout).

        Returns:
            ToolResult with command output.
        """
        # Validate
        is_valid, error = await self.validate_command(command)
        if not is_valid:
            return ToolResult.error_result(error)

        # Check availability
        if not self._shell_path:
            await self.check_availability()

        if not self.is_available:
            return ToolResult.error_result(self._last_error or "Shell not available")

        # Get optional parameters
        cwd = kwargs.get("cwd")
        env = kwargs.get("env")
        timeout = kwargs.get("timeout", self.config.timeout_seconds)

        # Execute via shell
        logger.info("shell_command_executing", command=command[:100])

        args = [self._shell_path, "-c", command]

        result = await self._run_command(
            args,
            timeout=timeout,
            env=env,
            cwd=cwd,
        )

        if result.success:
            logger.info("shell_command_success", execution_time_ms=result.execution_time_ms)
        else:
            logger.warning(
                "shell_command_failed",
                error=result.error,
                execution_time_ms=result.execution_time_ms,
            )

        return result

    async def execute_script(
        self,
        script: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> ToolResult:
        """
        Execute a multi-line shell script.

        Args:
            script: Multi-line script content.
            cwd: Working directory.
            env: Environment variables.

        Returns:
            ToolResult with script output.
        """
        # Write script to temp file
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".sh",
            delete=False,
        ) as f:
            f.write("#!/bin/bash\nset -e\n")
            f.write(script)
            script_path = f.name

        try:
            # Make executable
            os.chmod(script_path, 0o700)

            # Execute
            return await self._run_command(
                [self._shell_path or "/bin/bash", script_path],
                cwd=cwd,
                env=env,
            )
        finally:
            # Clean up
            try:
                os.unlink(script_path)
            except OSError:
                pass
