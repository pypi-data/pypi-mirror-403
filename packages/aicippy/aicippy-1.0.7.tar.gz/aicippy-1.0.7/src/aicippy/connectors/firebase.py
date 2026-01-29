"""
Firebase CLI connector for AiCippy.

Provides access to Firebase services through the Firebase CLI.
"""

from __future__ import annotations

import shutil
from typing import Any

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus, ToolResult
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)


class FirebaseConnector(BaseConnector):
    """
    Firebase CLI connector.

    Provides access to hosting, Firestore, Functions, and Auth.
    """

    name = "firebase"
    description = "Firebase CLI for hosting, Firestore, Functions, Auth"
    version = "1.0.0"

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        """Initialize Firebase connector."""
        super().__init__(config)
        self._firebase_path: str | None = None

    async def check_availability(self) -> bool:
        """
        Check if Firebase CLI is available.

        Returns:
            True if firebase CLI is installed.
        """
        self._firebase_path = shutil.which("firebase")
        if not self._firebase_path:
            self._status = ConnectorStatus.UNAVAILABLE
            self._last_error = "Firebase CLI not found in PATH"
            return False

        # Check if logged in
        result = await self._run_command(
            [self._firebase_path, "projects:list", "--json"],
            timeout=15,
        )

        if result.success:
            self._status = ConnectorStatus.AVAILABLE
            return True
        else:
            # CLI available but not logged in
            self._status = ConnectorStatus.ERROR
            self._last_error = "Firebase CLI not authenticated"
            return False

    async def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a Firebase CLI command.

        Args:
            command: Command to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Must start with "firebase"
        if not command.strip().startswith("firebase"):
            return False, "Command must start with 'firebase'"

        # Check allowed commands if configured
        if not self._is_command_allowed(command):
            return False, "Command not in allowed list"

        # Block dangerous operations in sandbox mode
        if self.config.sandbox_mode:
            dangerous = ["delete", "destroy", "--force"]
            for pattern in dangerous:
                if pattern in command.lower():
                    return False, f"Dangerous operation not allowed in sandbox: {pattern}"

        return True, ""

    async def execute(self, command: str, **kwargs: Any) -> ToolResult:
        """
        Execute a Firebase CLI command.

        Args:
            command: Firebase CLI command.
            **kwargs: Additional arguments.

        Returns:
            ToolResult with command output.
        """
        # Validate
        is_valid, error = await self.validate_command(command)
        if not is_valid:
            return ToolResult.error_result(error)

        # Check availability
        if not self._firebase_path:
            await self.check_availability()

        if not self.is_available:
            return ToolResult.error_result(self._last_error or "Firebase CLI not available")

        # Parse command into arguments
        import shlex
        args = shlex.split(command)

        # Add JSON output if not specified
        if "--json" not in args:
            args.append("--json")

        # Execute
        logger.info("firebase_command_executing", command=command[:100])
        result = await self._run_command(args)

        if result.success:
            logger.info("firebase_command_success", execution_time_ms=result.execution_time_ms)
        else:
            logger.warning(
                "firebase_command_failed",
                error=result.error,
                execution_time_ms=result.execution_time_ms,
            )

        return result

    async def list_projects(self) -> list[dict[str, Any]]:
        """
        List Firebase projects.

        Returns:
            List of project dictionaries.
        """
        result = await self.execute("firebase projects:list")

        if result.success:
            import json
            try:
                data = json.loads(result.output)
                return data.get("result", [])
            except json.JSONDecodeError:
                return []
        return []

    async def deploy(
        self,
        targets: list[str] | None = None,
        only: str | None = None,
    ) -> ToolResult:
        """
        Deploy to Firebase.

        Args:
            targets: Specific targets to deploy.
            only: Deploy only specific services (hosting, functions, etc.).

        Returns:
            ToolResult with deployment output.
        """
        cmd = "firebase deploy"

        if only:
            cmd += f" --only {only}"

        if targets:
            cmd += f" --only {','.join(targets)}"

        return await self.execute(cmd)
