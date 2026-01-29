"""
AWS CLI connector for AiCippy.

Provides access to AWS services through the AWS CLI.
"""

from __future__ import annotations

import shutil
from typing import Any

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus, ToolResult
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)

# Dangerous AWS commands that require extra caution
DANGEROUS_PATTERNS = frozenset({
    "delete",
    "terminate",
    "remove",
    "destroy",
    "purge",
    "--force",
    "--no-dry-run",
})

# Always blocked commands
BLOCKED_COMMANDS = frozenset({
    "aws iam delete-user",
    "aws iam delete-role",
    "aws ec2 terminate-instances",
    "aws s3 rb",
    "aws rds delete-db-instance",
    "aws cloudformation delete-stack",
})


class AWSConnector(BaseConnector):
    """
    AWS CLI connector.

    Provides access to AWS services with safety validations
    and credential chain support.
    """

    name = "aws"
    description = "AWS CLI operations with full service coverage"
    version = "1.0.0"

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        """Initialize AWS connector."""
        super().__init__(config)
        self._aws_path: str | None = None

    async def check_availability(self) -> bool:
        """
        Check if AWS CLI is available.

        Returns:
            True if AWS CLI is installed and configured.
        """
        self._aws_path = shutil.which("aws")
        if not self._aws_path:
            self._status = ConnectorStatus.UNAVAILABLE
            self._last_error = "AWS CLI not found in PATH"
            return False

        # Check for credentials
        result = await self._run_command(
            [self._aws_path, "sts", "get-caller-identity"],
            timeout=10,
        )

        if result.success:
            self._status = ConnectorStatus.AVAILABLE
            return True
        else:
            self._status = ConnectorStatus.ERROR
            self._last_error = "AWS credentials not configured"
            return False

    async def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate an AWS CLI command.

        Args:
            command: Command to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Must start with "aws"
        if not command.strip().startswith("aws"):
            return False, "Command must start with 'aws'"

        # Check blocked commands
        for blocked in BLOCKED_COMMANDS:
            if command.startswith(blocked):
                return False, f"Command is blocked: {blocked}"

        # Check allowed commands if configured
        if not self._is_command_allowed(command):
            return False, "Command not in allowed list"

        # Warn about dangerous patterns
        for pattern in DANGEROUS_PATTERNS:
            if pattern in command.lower():
                logger.warning(
                    "dangerous_aws_command",
                    command=command[:50],
                    pattern=pattern,
                )
                if self.config.sandbox_mode:
                    return False, f"Dangerous command pattern in sandbox mode: {pattern}"

        return True, ""

    async def execute(self, command: str, **kwargs: Any) -> ToolResult:
        """
        Execute an AWS CLI command.

        Args:
            command: AWS CLI command (starting with 'aws').
            **kwargs: Additional arguments.

        Returns:
            ToolResult with command output.
        """
        # Validate
        is_valid, error = await self.validate_command(command)
        if not is_valid:
            return ToolResult.error_result(error)

        # Check availability
        if not self._aws_path:
            await self.check_availability()

        if not self.is_available:
            return ToolResult.error_result(self._last_error or "AWS CLI not available")

        # Parse command into arguments
        import shlex
        args = shlex.split(command)

        # Add output format if not specified
        if "--output" not in args and "-o" not in args:
            args.extend(["--output", "json"])

        # Execute
        logger.info("aws_command_executing", command=command[:100])
        result = await self._run_command(args)

        if result.success:
            logger.info("aws_command_success", execution_time_ms=result.execution_time_ms)
        else:
            logger.warning(
                "aws_command_failed",
                error=result.error,
                execution_time_ms=result.execution_time_ms,
            )

        return result

    async def get_current_identity(self) -> dict[str, Any]:
        """
        Get current AWS identity.

        Returns:
            Dictionary with account, ARN, and user ID.
        """
        result = await self.execute("aws sts get-caller-identity")
        if result.success:
            import json
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return {}
        return {}

    async def list_regions(self) -> list[str]:
        """
        List available AWS regions.

        Returns:
            List of region names.
        """
        result = await self.execute(
            "aws ec2 describe-regions --query 'Regions[].RegionName'"
        )
        if result.success:
            import json
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return []
        return []
