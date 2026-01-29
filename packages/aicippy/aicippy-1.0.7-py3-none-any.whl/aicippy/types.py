"""
Type definitions and protocols for AiCippy.

This module provides type aliases, protocols, and typed containers
for use throughout the codebase, enabling strict type checking.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import (
    TYPE_CHECKING,
    Any,
    Final,
    Literal,
    NewType,
    Protocol,
    TypeAlias,
    TypedDict,
    TypeVar,
    runtime_checkable,
)

if TYPE_CHECKING:
    from aicippy.agents.models import AgentResponse, AgentTask

# ============================================================================
# NewTypes for Domain-Specific Identifiers
# ============================================================================

SessionId = NewType("SessionId", str)
CorrelationId = NewType("CorrelationId", str)
AgentId = NewType("AgentId", str)
TaskId = NewType("TaskId", str)
DocumentId = NewType("DocumentId", str)
ConnectionId = NewType("ConnectionId", str)

# ============================================================================
# Type Aliases
# ============================================================================

JsonValue: TypeAlias = (
    str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]
)
JsonDict: TypeAlias = dict[str, JsonValue]
Headers: TypeAlias = Mapping[str, str]

# Callback types
ProgressCallback: TypeAlias = Callable[[str, int], None]
TokenCallback: TypeAlias = Callable[[str], None]
ErrorCallback: TypeAlias = Callable[[Exception], None]

# Async callback types
AsyncProgressCallback: TypeAlias = Callable[[str, int], Awaitable[None]]
AsyncTokenCallback: TypeAlias = Callable[[str], Awaitable[None]]

# ============================================================================
# Enums
# ============================================================================


class ExecutionMode(str, Enum):
    """CLI execution mode."""

    AGENT = "agent"
    EDIT = "edit"
    RESEARCH = "research"
    CODE = "code"


class ConnectionState(str, Enum):
    """WebSocket connection state."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    DISCONNECTED = "disconnected"
    FAILED = "failed"


class ToolCategory(str, Enum):
    """Categories of tool connectors."""

    CLOUD = "cloud"
    VERSION_CONTROL = "version_control"
    DATABASE = "database"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    SHELL = "shell"
    OTHER = "other"


# ============================================================================
# TypedDicts for Structured Data
# ============================================================================


class TokenUsageDict(TypedDict):
    """Token usage information."""

    input_tokens: int
    output_tokens: int


class AgentStatusDict(TypedDict):
    """Agent status information."""

    id: str
    type: str
    status: str
    progress: int
    message: str


class WebSocketMessageDict(TypedDict, total=False):
    """WebSocket message structure."""

    type: str
    payload: JsonDict
    correlation_id: str
    timestamp: str


class ToolResultDict(TypedDict, total=False):
    """Tool execution result."""

    success: bool
    output: str
    error: str | None
    execution_time_ms: int
    metadata: JsonDict


class FeedItemDict(TypedDict, total=False):
    """Feed item structure."""

    title: str
    link: str
    content: str
    published: str | None
    source: str


# ============================================================================
# Protocols for Duck Typing
# ============================================================================


@runtime_checkable
class Closeable(Protocol):
    """Protocol for objects that can be closed."""

    async def close(self) -> None:
        """Close the resource."""
        ...


@runtime_checkable
class Connectable(Protocol):
    """Protocol for connectable resources."""

    async def connect(self) -> bool:
        """Establish connection."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from resource."""
        ...

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        ...


@runtime_checkable
class Executable(Protocol):
    """Protocol for executable tools."""

    async def execute(self, command: str, **kwargs: Any) -> ToolResultDict:
        """Execute a command."""
        ...

    async def validate_command(self, command: str) -> tuple[bool, str]:
        """Validate a command before execution."""
        ...


@runtime_checkable
class Serializable(Protocol):
    """Protocol for serializable objects."""

    def to_dict(self) -> JsonDict:
        """Convert to dictionary."""
        ...

    @classmethod
    def from_dict(cls, data: JsonDict) -> "Serializable":
        """Create from dictionary."""
        ...


@runtime_checkable
class ProgressReporter(Protocol):
    """Protocol for progress reporting."""

    def update_progress(self, task_id: str, progress: int, message: str = "") -> None:
        """Update progress for a task."""
        ...

    def complete_task(self, task_id: str) -> None:
        """Mark a task as complete."""
        ...

    def fail_task(self, task_id: str, error: str) -> None:
        """Mark a task as failed."""
        ...


# ============================================================================
# Generic Type Variables
# ============================================================================

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)

# Bound type variables
ConnectorT = TypeVar("ConnectorT", bound="Executable")
MessageT = TypeVar("MessageT", bound="Serializable")

# ============================================================================
# Constants
# ============================================================================

# Maximum values
MAX_PARALLEL_AGENTS: Final[int] = 10
MAX_RETRY_ATTEMPTS: Final[int] = 5
MAX_TOKEN_LENGTH: Final[int] = 200_000
MAX_MESSAGE_SIZE: Final[int] = 10_000_000  # 10MB

# Timeouts (in seconds)
DEFAULT_TIMEOUT: Final[float] = 30.0
AGENT_TIMEOUT: Final[float] = 300.0
WEBSOCKET_TIMEOUT: Final[float] = 60.0
COMMAND_TIMEOUT: Final[float] = 120.0

# Model identifiers
CLAUDE_OPUS_MODEL: Final[str] = "anthropic.claude-opus-4-5-20251101-v1:0"
CLAUDE_SONNET_MODEL: Final[str] = "anthropic.claude-sonnet-4-5-20251101-v1:0"
LLAMA_MAVERICK_MODEL: Final[str] = "meta.llama4-maverick-17b-instruct-v1:0"


# ============================================================================
# Result Types
# ============================================================================


@dataclass(frozen=True, slots=True)
class Result[T]:
    """
    Generic result type for operations that may fail.

    Type-safe alternative to exceptions for expected failures.

    Example:
        >>> result = Result.ok(42)
        >>> if result.is_ok:
        ...     print(result.value)
        42
    """

    _value: T | None
    _error: str | None
    _is_ok: bool

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        """Create successful result."""
        return cls(_value=value, _error=None, _is_ok=True)

    @classmethod
    def err(cls, error: str) -> "Result[T]":
        """Create error result."""
        return cls(_value=None, _error=error, _is_ok=False)

    @property
    def is_ok(self) -> bool:
        """Check if result is successful."""
        return self._is_ok

    @property
    def is_err(self) -> bool:
        """Check if result is an error."""
        return not self._is_ok

    @property
    def value(self) -> T:
        """Get value (raises if error)."""
        if not self._is_ok:
            raise ValueError(f"Cannot get value from error result: {self._error}")
        return self._value  # type: ignore[return-value]

    @property
    def error(self) -> str:
        """Get error message (raises if ok)."""
        if self._is_ok:
            raise ValueError("Cannot get error from successful result")
        return self._error  # type: ignore[return-value]

    def unwrap_or(self, default: T) -> T:
        """Get value or return default if error."""
        return self._value if self._is_ok else default  # type: ignore[return-value]

    def map[U](self, fn: Callable[[T], U]) -> "Result[U]":
        """Map successful value through function."""
        if self._is_ok:
            return Result.ok(fn(self._value))  # type: ignore[arg-type]
        return Result.err(self._error)  # type: ignore[arg-type]
