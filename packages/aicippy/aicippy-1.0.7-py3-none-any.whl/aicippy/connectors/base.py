"""
Base connector interface for MCP-style tool bridges.

This module provides the abstract base class for all tool connectors,
including secure command execution, validation, and result handling.

Security Features:
- Command allowlist/blocklist enforcement
- Shell injection prevention
- Sandboxed subprocess execution
- Timeout enforcement
"""

from __future__ import annotations

import asyncio
import os
import re
import shlex
import time
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Final, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from aicippy.exceptions import (
    CommandBlockedError,
    CommandExecutionError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
    ErrorContext,
)
from aicippy.types import (
    CorrelationId,
    JsonDict,
    ToolResultDict,
)
from aicippy.utils.correlation import get_correlation_id
from aicippy.utils.logging import get_logger

if TYPE_CHECKING:
    from aicippy.types import Executable

logger = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

# Dangerous shell characters that could enable injection attacks
DANGEROUS_SHELL_CHARS: Final[frozenset[str]] = frozenset({
    ";", "&", "|", "`", "$", "(", ")", "{", "}", "<", ">", "\n", "\r",
})

# Common dangerous command patterns to block
DANGEROUS_COMMAND_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"\brm\s+-rf\s+/", re.IGNORECASE),
    re.compile(r"\bdd\s+if=/dev/zero", re.IGNORECASE),
    re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE),
    re.compile(r"\bmkfs\.", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
    re.compile(r"\bchmod\s+-R\s+777\s+/", re.IGNORECASE),
    re.compile(r"\bchown\s+-R\s+.*\s+/", re.IGNORECASE),
    re.compile(r"curl.*\|\s*(ba)?sh", re.IGNORECASE),
    re.compile(r"wget.*\|\s*(ba)?sh", re.IGNORECASE),
)


# ============================================================================
# Enums
# ============================================================================


class ConnectorStatus(str, Enum):
    """Status of a connector."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"
    DISABLED = "disabled"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass(frozen=True, slots=True)
class ToolResult:
    """
    Immutable result from a tool execution.

    Attributes:
        success: Whether the execution was successful.
        output: Standard output from the command.
        error: Error message if execution failed.
        execution_time_ms: Execution duration in milliseconds.
        metadata: Additional execution metadata.
        exit_code: Process exit code if applicable.
    """

    success: bool
    output: str
    error: str | None = None
    execution_time_ms: int = 0
    metadata: JsonDict = field(default_factory=dict)
    exit_code: int | None = None

    @classmethod
    def success_result(
        cls,
        output: str,
        execution_time_ms: int = 0,
        metadata: JsonDict | None = None,
        exit_code: int = 0,
    ) -> Self:
        """
        Create a successful result.

        Args:
            output: Command output.
            execution_time_ms: Execution duration.
            metadata: Additional metadata.
            exit_code: Process exit code.

        Returns:
            ToolResult indicating success.
        """
        return cls(
            success=True,
            output=output,
            execution_time_ms=execution_time_ms,
            metadata=metadata or {},
            exit_code=exit_code,
        )

    @classmethod
    def error_result(
        cls,
        error: str,
        output: str = "",
        execution_time_ms: int = 0,
        exit_code: int | None = None,
    ) -> Self:
        """
        Create an error result.

        Args:
            error: Error description.
            output: Any partial output.
            execution_time_ms: Execution duration.
            exit_code: Process exit code if available.

        Returns:
            ToolResult indicating failure.
        """
        return cls(
            success=False,
            output=output,
            error=error,
            execution_time_ms=execution_time_ms,
            exit_code=exit_code,
        )

    def to_dict(self) -> ToolResultDict:
        """Convert to dictionary representation."""
        return ToolResultDict(
            success=self.success,
            output=self.output,
            error=self.error,
            execution_time_ms=self.execution_time_ms,
            metadata=self.metadata,
        )


# ============================================================================
# Configuration
# ============================================================================


class ConnectorConfig(BaseModel):
    """
    Configuration for a connector with validation.

    Attributes:
        enabled: Whether the connector is enabled.
        timeout_seconds: Command execution timeout.
        max_retries: Maximum retry attempts for transient failures.
        sandbox_mode: Enable sandbox restrictions.
        allowed_commands: Allowlist of command prefixes.
        blocked_commands: Blocklist of command patterns.
        working_directory: Default working directory for commands.
        environment: Additional environment variables.
    """

    enabled: bool = True
    timeout_seconds: Annotated[int, Field(ge=1, le=600)] = 30
    max_retries: Annotated[int, Field(ge=0, le=10)] = 3
    sandbox_mode: bool = False
    allowed_commands: list[str] = Field(default_factory=list)
    blocked_commands: list[str] = Field(default_factory=list)
    working_directory: str | None = None
    environment: dict[str, str] = Field(default_factory=dict)

    model_config = {
        "extra": "forbid",
        "validate_default": True,
        "str_strip_whitespace": True,
    }

    @field_validator("allowed_commands", "blocked_commands", mode="after")
    @classmethod
    def normalize_command_lists(cls, v: list[str]) -> list[str]:
        """Normalize command lists by stripping whitespace."""
        return [cmd.strip().lower() for cmd in v if cmd.strip()]

    @field_validator("working_directory", mode="after")
    @classmethod
    def validate_working_directory(cls, v: str | None) -> str | None:
        """Validate working directory exists if specified."""
        if v is not None and not os.path.isdir(v):
            raise ValueError(f"Working directory does not exist: {v}")
        return v

    @model_validator(mode="after")
    def validate_command_lists_disjoint(self) -> Self:
        """Ensure allowed and blocked lists don't overlap."""
        allowed_set = set(self.allowed_commands)
        blocked_set = set(self.blocked_commands)
        overlap = allowed_set & blocked_set
        if overlap:
            raise ValueError(f"Commands cannot be both allowed and blocked: {overlap}")
        return self


# ============================================================================
# Base Connector
# ============================================================================


class BaseConnector(ABC):
    """
    Abstract base class for MCP-style tool connectors.

    Provides secure command execution with:
    - Command validation and sanitization
    - Allowlist/blocklist enforcement
    - Subprocess sandboxing with timeouts
    - Structured error handling

    Subclasses must implement:
    - execute(): Execute a command
    - validate_command(): Validate before execution
    - check_availability(): Verify tool availability

    Example:
        class GitConnector(BaseConnector):
            name = "git"
            description = "Git version control"

            async def execute(self, command: str, **kwargs) -> ToolResult:
                is_valid, error = await self.validate_command(command)
                if not is_valid:
                    return ToolResult.error_result(error)
                return await self._run_command(["git"] + shlex.split(command))
    """

    # Class-level connector metadata (override in subclasses)
    name: ClassVar[str] = "base"
    description: ClassVar[str] = "Base connector"
    version: ClassVar[str] = "1.0.0"
    category: ClassVar[str] = "other"

    __slots__ = ("config", "_status", "_last_error", "_error_count")

    def __init__(self, config: ConnectorConfig | None = None) -> None:
        """
        Initialize the connector.

        Args:
            config: Connector configuration. Uses defaults if not provided.
        """
        self.config = config or ConnectorConfig()
        self._status: ConnectorStatus = ConnectorStatus.AVAILABLE
        self._last_error: str | None = None
        self._error_count: int = 0

    @property
    def status(self) -> ConnectorStatus:
        """Get current connector status."""
        return self._status

    @property
    def is_available(self) -> bool:
        """Check if connector is available for use."""
        return self._status == ConnectorStatus.AVAILABLE and self.config.enabled

    @property
    def last_error(self) -> str | None:
        """Get the last error message if any."""
        return self._last_error

    @abstractmethod
    async def execute(self, command: str, **kwargs: Any) -> ToolResult:
        """
        Execute a command through this connector.

        Args:
            command: Command string to execute.
            **kwargs: Additional connector-specific arguments.

        Returns:
            ToolResult with execution outcome.

        Raises:
            CommandBlockedError: If command fails validation.
            CommandExecutionError: If execution fails.
            ConnectorTimeoutError: If execution times out.
        """
        ...

    @abstractmethod
    async def validate_command(self, command: str) -> tuple[bool, str]:
        """
        Validate a command before execution.

        Args:
            command: Command string to validate.

        Returns:
            Tuple of (is_valid, error_message).
            error_message is empty string if valid.
        """
        ...

    @abstractmethod
    async def check_availability(self) -> bool:
        """
        Check if the connector's underlying tool is available.

        Returns:
            True if the tool is available and functional.
        """
        ...

    def _sanitize_command(self, command: str) -> str:
        """
        Sanitize a command string for safe logging.

        Removes potentially sensitive information.

        Args:
            command: Raw command string.

        Returns:
            Sanitized command string.
        """
        # Mask potential secrets in environment variable assignments
        sanitized = re.sub(
            r"(API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)[=:]\S+",
            r"\1=[REDACTED]",
            command,
            flags=re.IGNORECASE,
        )
        return sanitized

    def _has_shell_injection(self, command: str) -> bool:
        """
        Check if command contains potential shell injection patterns.

        Args:
            command: Command string to check.

        Returns:
            True if injection patterns detected.
        """
        return any(char in command for char in DANGEROUS_SHELL_CHARS)

    def _is_dangerous_command(self, command: str) -> tuple[bool, str]:
        """
        Check if command matches known dangerous patterns.

        Args:
            command: Command string to check.

        Returns:
            Tuple of (is_dangerous, reason).
        """
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if pattern.search(command):
                return True, f"Command matches dangerous pattern: {pattern.pattern}"
        return False, ""

    def _is_command_allowed(self, command: str) -> tuple[bool, str]:
        """
        Check if a command is allowed by configuration.

        Args:
            command: Command to check.

        Returns:
            Tuple of (is_allowed, error_message).
        """
        command_lower = command.lower().strip()

        # Check blocked list first
        for blocked in self.config.blocked_commands:
            if blocked in command_lower:
                return False, f"Command contains blocked pattern: {blocked}"

        # If allowed list is specified, command must match
        if self.config.allowed_commands:
            if not any(command_lower.startswith(allowed) for allowed in self.config.allowed_commands):
                return False, "Command not in allowed list"

        return True, ""

    async def _run_command(
        self,
        args: Sequence[str],
        timeout: int | None = None,
        env: dict[str, str] | None = None,
        cwd: str | None = None,
        capture_stderr: bool = True,
    ) -> ToolResult:
        """
        Run a command as a subprocess with security controls.

        Args:
            args: Command arguments as sequence (no shell expansion).
            timeout: Execution timeout in seconds.
            env: Additional environment variables.
            cwd: Working directory for the command.
            capture_stderr: Whether to capture stderr separately.

        Returns:
            ToolResult with command output.

        Raises:
            ConnectorTimeoutError: If command exceeds timeout.
            CommandExecutionError: If execution fails.
        """
        correlation_id = get_correlation_id()
        start_time = time.monotonic()
        effective_timeout = timeout or self.config.timeout_seconds
        effective_cwd = cwd or self.config.working_directory

        # Validate args to prevent empty commands
        if not args:
            return ToolResult.error_result("Empty command")

        # Build environment
        full_env = os.environ.copy()
        full_env.update(self.config.environment)
        if env:
            full_env.update(env)

        # Sanitize command for logging
        sanitized_cmd = self._sanitize_command(" ".join(args))
        logger.debug(
            "executing_command",
            command=sanitized_cmd,
            timeout=effective_timeout,
            correlation_id=correlation_id,
        )

        try:
            # Create subprocess without shell to prevent injection
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE if capture_stderr else asyncio.subprocess.STDOUT,
                env=full_env,
                cwd=effective_cwd,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=effective_timeout,
                )
            except asyncio.TimeoutError:
                # Kill the process on timeout
                process.kill()
                await process.wait()
                execution_time_ms = int((time.monotonic() - start_time) * 1000)

                self._record_error(f"Timeout after {effective_timeout}s")
                logger.warning(
                    "command_timeout",
                    command=sanitized_cmd,
                    timeout=effective_timeout,
                    correlation_id=correlation_id,
                )

                raise ConnectorTimeoutError(
                    connector_name=self.name,
                    timeout_seconds=float(effective_timeout),
                    context=ErrorContext(
                        correlation_id=correlation_id,
                        operation="command_execution",
                        details={"command": sanitized_cmd},
                    ),
                )

            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            output = stdout.decode("utf-8", errors="replace").strip()
            error_output = stderr.decode("utf-8", errors="replace").strip() if stderr else ""

            if process.returncode == 0:
                self._record_success()
                logger.debug(
                    "command_success",
                    command=sanitized_cmd,
                    execution_time_ms=execution_time_ms,
                    correlation_id=correlation_id,
                )
                return ToolResult.success_result(
                    output=output,
                    execution_time_ms=execution_time_ms,
                    metadata={
                        "exit_code": process.returncode,
                        "stderr": error_output if error_output else None,
                    },
                    exit_code=process.returncode,
                )
            else:
                self._record_error(error_output or f"Exit code {process.returncode}")
                logger.warning(
                    "command_failed",
                    command=sanitized_cmd,
                    exit_code=process.returncode,
                    error=error_output[:500] if error_output else None,
                    correlation_id=correlation_id,
                )
                return ToolResult.error_result(
                    error=error_output or f"Command failed with exit code {process.returncode}",
                    output=output,
                    execution_time_ms=execution_time_ms,
                    exit_code=process.returncode,
                )

        except ConnectorTimeoutError:
            raise
        except FileNotFoundError:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            error_msg = f"Command not found: {args[0]}"
            self._record_error(error_msg)
            logger.error(
                "command_not_found",
                command=args[0],
                correlation_id=correlation_id,
            )
            return ToolResult.error_result(
                error=error_msg,
                execution_time_ms=execution_time_ms,
                exit_code=127,  # Standard "command not found" exit code
            )
        except PermissionError as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            error_msg = f"Permission denied: {e}"
            self._record_error(error_msg)
            logger.error(
                "command_permission_denied",
                command=sanitized_cmd,
                error=str(e),
                correlation_id=correlation_id,
            )
            return ToolResult.error_result(
                error=error_msg,
                execution_time_ms=execution_time_ms,
                exit_code=126,  # Standard "permission denied" exit code
            )
        except OSError as e:
            execution_time_ms = int((time.monotonic() - start_time) * 1000)
            error_msg = f"OS error executing command: {e}"
            self._record_error(error_msg)
            logger.exception(
                "command_os_error",
                command=sanitized_cmd,
                error=str(e),
                correlation_id=correlation_id,
            )
            raise CommandExecutionError(
                message=error_msg,
                context=ErrorContext(
                    correlation_id=correlation_id,
                    operation="command_execution",
                    details={"command": sanitized_cmd},
                ),
            ) from e

    def _record_success(self) -> None:
        """Record successful execution for status tracking."""
        self._error_count = max(0, self._error_count - 1)
        if self._status == ConnectorStatus.ERROR and self._error_count == 0:
            self._status = ConnectorStatus.AVAILABLE
            self._last_error = None

    def _record_error(self, error: str) -> None:
        """
        Record execution error for status tracking.

        Args:
            error: Error message.
        """
        self._last_error = error
        self._error_count += 1
        if self._error_count >= 5:  # Error threshold
            self._status = ConnectorStatus.ERROR

    def get_info(self) -> JsonDict:
        """
        Get connector information for status reporting.

        Returns:
            Dictionary with connector metadata and status.
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category,
            "status": self._status.value,
            "enabled": self.config.enabled,
            "sandbox_mode": self.config.sandbox_mode,
            "timeout_seconds": self.config.timeout_seconds,
            "error_count": self._error_count,
            "last_error": self._last_error,
        }

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        pass
