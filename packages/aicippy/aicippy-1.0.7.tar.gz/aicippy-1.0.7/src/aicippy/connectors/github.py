"""
GitHub CLI connector for AiCippy.

Provides access to GitHub operations through the gh CLI.
"""

from __future__ import annotations

import shutil
from typing import Any

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus, ToolResult
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)


class GitHubConnector(BaseConnector):
    """
    GitHub CLI connector.

    Provides access to repositories, PRs, issues, actions, and releases.
    """

    name = "gh"
    description = "GitHub CLI for repos, PRs, issues, actions, releases"
    version = "1.0.0"

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        """Initialize GitHub connector."""
        super().__init__(config)
        self._gh_path: str | None = None

    async def check_availability(self) -> bool:
        """
        Check if GitHub CLI is available and authenticated.

        Returns:
            True if gh CLI is installed and authenticated.
        """
        self._gh_path = shutil.which("gh")
        if not self._gh_path:
            self._status = ConnectorStatus.UNAVAILABLE
            self._last_error = "GitHub CLI (gh) not found in PATH"
            return False

        # Check authentication
        result = await self._run_command(
            [self._gh_path, "auth", "status"],
            timeout=10,
        )

        if result.success or "Logged in" in result.output:
            self._status = ConnectorStatus.AVAILABLE
            return True
        else:
            self._status = ConnectorStatus.ERROR
            self._last_error = "GitHub CLI not authenticated"
            return False

    async def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a GitHub CLI command.

        Args:
            command: Command to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        # Must start with "gh"
        if not command.strip().startswith("gh"):
            return False, "Command must start with 'gh'"

        # Check allowed commands if configured
        if not self._is_command_allowed(command):
            return False, "Command not in allowed list"

        # Block certain dangerous operations in sandbox mode
        if self.config.sandbox_mode:
            dangerous = ["delete", "archive", "--force"]
            for pattern in dangerous:
                if pattern in command.lower():
                    return False, f"Dangerous operation not allowed in sandbox: {pattern}"

        return True, ""

    async def execute(self, command: str, **kwargs: Any) -> ToolResult:
        """
        Execute a GitHub CLI command.

        Args:
            command: GitHub CLI command (starting with 'gh').
            **kwargs: Additional arguments.

        Returns:
            ToolResult with command output.
        """
        # Validate
        is_valid, error = await self.validate_command(command)
        if not is_valid:
            return ToolResult.error_result(error)

        # Check availability
        if not self._gh_path:
            await self.check_availability()

        if not self.is_available:
            return ToolResult.error_result(self._last_error or "GitHub CLI not available")

        # Parse command into arguments
        import shlex
        args = shlex.split(command)

        # Execute
        logger.info("github_command_executing", command=command[:100])
        result = await self._run_command(args)

        if result.success:
            logger.info("github_command_success", execution_time_ms=result.execution_time_ms)
        else:
            logger.warning(
                "github_command_failed",
                error=result.error,
                execution_time_ms=result.execution_time_ms,
            )

        return result

    async def list_repos(self, owner: str | None = None, limit: int = 30) -> list[dict[str, Any]]:
        """
        List repositories.

        Args:
            owner: Optional owner/org to list repos for.
            limit: Maximum number of repos to return.

        Returns:
            List of repository dictionaries.
        """
        cmd = f"gh repo list {owner or ''} --limit {limit} --json name,owner,description,isPrivate"
        result = await self.execute(cmd)

        if result.success:
            import json
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return []
        return []

    async def get_pr(self, number: int | str) -> dict[str, Any]:
        """
        Get pull request details.

        Args:
            number: PR number.

        Returns:
            PR details dictionary.
        """
        result = await self.execute(
            f"gh pr view {number} --json number,title,state,author,body,url"
        )

        if result.success:
            import json
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return {}
        return {}

    async def list_issues(self, state: str = "open", limit: int = 30) -> list[dict[str, Any]]:
        """
        List repository issues.

        Args:
            state: Issue state (open, closed, all).
            limit: Maximum number of issues.

        Returns:
            List of issue dictionaries.
        """
        result = await self.execute(
            f"gh issue list --state {state} --limit {limit} --json number,title,state,author"
        )

        if result.success:
            import json
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return []
        return []
