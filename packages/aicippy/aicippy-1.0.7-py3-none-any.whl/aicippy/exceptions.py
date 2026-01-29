"""
Custom exception hierarchy for AiCippy.

Provides structured error handling with error codes, context preservation,
and proper exception chaining for debugging and observability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum, auto
from typing import Any, Self


class ErrorCode(IntEnum):
    """Standardized error codes for AiCippy exceptions."""

    # General errors (1000-1099)
    UNKNOWN = 1000
    CONFIGURATION = 1001
    VALIDATION = 1002
    TIMEOUT = 1003
    CANCELLED = 1004

    # Authentication errors (1100-1199)
    AUTH_REQUIRED = 1100
    AUTH_EXPIRED = 1101
    AUTH_INVALID = 1102
    AUTH_REFRESH_FAILED = 1103
    AUTH_STORAGE_ERROR = 1104

    # Agent errors (1200-1299)
    AGENT_SPAWN_FAILED = 1200
    AGENT_TIMEOUT = 1201
    AGENT_EXECUTION_ERROR = 1202
    AGENT_COMMUNICATION_ERROR = 1203
    AGENT_QUOTA_EXCEEDED = 1204

    # Connector errors (1300-1399)
    CONNECTOR_UNAVAILABLE = 1300
    CONNECTOR_COMMAND_BLOCKED = 1301
    CONNECTOR_EXECUTION_FAILED = 1302
    CONNECTOR_TIMEOUT = 1303
    CONNECTOR_PERMISSION_DENIED = 1304

    # WebSocket errors (1400-1499)
    WEBSOCKET_CONNECTION_FAILED = 1400
    WEBSOCKET_DISCONNECTED = 1401
    WEBSOCKET_MESSAGE_ERROR = 1402
    WEBSOCKET_AUTH_FAILED = 1403

    # Knowledge Base errors (1500-1599)
    KB_CRAWL_FAILED = 1500
    KB_INDEX_FAILED = 1501
    KB_SEARCH_FAILED = 1502
    KB_STORAGE_ERROR = 1503

    # AWS/Infrastructure errors (1600-1699)
    AWS_SERVICE_ERROR = 1600
    AWS_CREDENTIALS_ERROR = 1601
    AWS_RESOURCE_NOT_FOUND = 1602
    AWS_QUOTA_EXCEEDED = 1603

    # Model/Bedrock errors (1700-1799)
    MODEL_INVOCATION_FAILED = 1700
    MODEL_RATE_LIMITED = 1701
    MODEL_CONTENT_FILTERED = 1702
    MODEL_CONTEXT_EXCEEDED = 1703


@dataclass(frozen=True, slots=True)
class ErrorContext:
    """
    Immutable context information for error debugging.

    Attributes:
        correlation_id: Request correlation ID for tracing.
        operation: Name of the operation that failed.
        details: Additional context details.
    """

    correlation_id: str | None = None
    operation: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def with_detail(self, key: str, value: Any) -> Self:
        """Create new context with additional detail."""
        new_details = {**self.details, key: value}
        return ErrorContext(
            correlation_id=self.correlation_id,
            operation=self.operation,
            details=new_details,
        )


class AiCippyError(Exception):
    """
    Base exception for all AiCippy errors.

    Provides structured error information including error codes,
    context preservation, and proper exception chaining.

    Attributes:
        message: Human-readable error message.
        code: Standardized error code.
        context: Additional debugging context.
        recoverable: Whether the error is potentially recoverable.
    """

    __slots__ = ("message", "code", "context", "recoverable")

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.UNKNOWN,
        context: ErrorContext | None = None,
        recoverable: bool = False,
    ) -> None:
        """
        Initialize AiCippy error.

        Args:
            message: Human-readable error description.
            code: Standardized error code for programmatic handling.
            context: Additional context for debugging.
            recoverable: Indicates if retry/recovery is possible.
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or ErrorContext()
        self.recoverable = recoverable

    def __str__(self) -> str:
        """Format error for display."""
        parts = [f"[{self.code.name}] {self.message}"]
        if self.context.operation:
            parts.append(f"Operation: {self.context.operation}")
        if self.context.correlation_id:
            parts.append(f"Correlation ID: {self.context.correlation_id}")
        return " | ".join(parts)

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"code={self.code.name}, "
            f"recoverable={self.recoverable})"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "code": self.code.value,
            "code_name": self.code.name,
            "recoverable": self.recoverable,
            "context": {
                "correlation_id": self.context.correlation_id,
                "operation": self.context.operation,
                "details": self.context.details,
            },
        }

    def with_context(self, **kwargs: Any) -> Self:
        """Create new error with additional context."""
        new_context = ErrorContext(
            correlation_id=kwargs.get("correlation_id", self.context.correlation_id),
            operation=kwargs.get("operation", self.context.operation),
            details={**self.context.details, **kwargs.get("details", {})},
        )
        return self.__class__(
            message=self.message,
            code=self.code,
            context=new_context,
            recoverable=self.recoverable,
        )


# ============================================================================
# Authentication Errors
# ============================================================================


class AuthenticationError(AiCippyError):
    """Base class for authentication-related errors."""

    def __init__(
        self,
        message: str,
        code: ErrorCode = ErrorCode.AUTH_REQUIRED,
        context: ErrorContext | None = None,
    ) -> None:
        super().__init__(message, code, context, recoverable=True)


class AuthenticationRequiredError(AuthenticationError):
    """Raised when authentication is required but not present."""

    def __init__(self, message: str = "Authentication required", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AUTH_REQUIRED, context)


class AuthenticationExpiredError(AuthenticationError):
    """Raised when authentication has expired."""

    def __init__(self, message: str = "Authentication expired", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AUTH_EXPIRED, context)


class AuthenticationInvalidError(AuthenticationError):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AUTH_INVALID, context)


class TokenRefreshError(AuthenticationError):
    """Raised when token refresh fails."""

    def __init__(self, message: str = "Token refresh failed", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AUTH_REFRESH_FAILED, context)


class CredentialStorageError(AuthenticationError):
    """Raised when credential storage operations fail."""

    def __init__(self, message: str = "Credential storage error", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AUTH_STORAGE_ERROR, context)


# ============================================================================
# Agent Errors
# ============================================================================


class AgentError(AiCippyError):
    """Base class for agent-related errors."""

    pass


class AgentSpawnError(AgentError):
    """Raised when agent spawning fails."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AGENT_SPAWN_FAILED, context, recoverable=True)


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    def __init__(self, message: str = "Agent execution timed out", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AGENT_TIMEOUT, context, recoverable=True)


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AGENT_EXECUTION_ERROR, context, recoverable=False)


class AgentQuotaExceededError(AgentError):
    """Raised when agent quota is exceeded."""

    def __init__(self, message: str = "Agent quota exceeded", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.AGENT_QUOTA_EXCEEDED, context, recoverable=False)


# ============================================================================
# Connector Errors
# ============================================================================


class ConnectorError(AiCippyError):
    """Base class for connector-related errors."""

    pass


class ConnectorUnavailableError(ConnectorError):
    """Raised when a connector is unavailable."""

    def __init__(self, connector_name: str, context: ErrorContext | None = None) -> None:
        super().__init__(
            f"Connector '{connector_name}' is unavailable",
            ErrorCode.CONNECTOR_UNAVAILABLE,
            context,
            recoverable=True,
        )


class CommandBlockedError(ConnectorError):
    """Raised when a command is blocked by security policy."""

    def __init__(self, command: str, reason: str, context: ErrorContext | None = None) -> None:
        super().__init__(
            f"Command blocked: {reason}",
            ErrorCode.CONNECTOR_COMMAND_BLOCKED,
            context,
            recoverable=False,
        )


class CommandExecutionError(ConnectorError):
    """Raised when command execution fails."""

    def __init__(self, message: str, exit_code: int | None = None, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        if exit_code is not None:
            ctx = ctx.with_detail("exit_code", exit_code)
        super().__init__(message, ErrorCode.CONNECTOR_EXECUTION_FAILED, ctx, recoverable=False)


class ConnectorTimeoutError(ConnectorError):
    """Raised when connector operation times out."""

    def __init__(self, connector_name: str, timeout_seconds: float, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("timeout_seconds", timeout_seconds)
        super().__init__(
            f"Connector '{connector_name}' timed out after {timeout_seconds}s",
            ErrorCode.CONNECTOR_TIMEOUT,
            ctx,
            recoverable=True,
        )


# ============================================================================
# WebSocket Errors
# ============================================================================


class WebSocketError(AiCippyError):
    """Base class for WebSocket-related errors."""

    pass


class WebSocketConnectionError(WebSocketError):
    """Raised when WebSocket connection fails."""

    def __init__(self, message: str = "WebSocket connection failed", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.WEBSOCKET_CONNECTION_FAILED, context, recoverable=True)


class WebSocketDisconnectedError(WebSocketError):
    """Raised when WebSocket is unexpectedly disconnected."""

    def __init__(self, message: str = "WebSocket disconnected", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.WEBSOCKET_DISCONNECTED, context, recoverable=True)


class WebSocketMessageError(WebSocketError):
    """Raised when WebSocket message handling fails."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.WEBSOCKET_MESSAGE_ERROR, context, recoverable=False)


# ============================================================================
# Knowledge Base Errors
# ============================================================================


class KnowledgeBaseError(AiCippyError):
    """Base class for Knowledge Base errors."""

    pass


class CrawlError(KnowledgeBaseError):
    """Raised when feed crawling fails."""

    def __init__(self, source: str, message: str, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("source", source)
        super().__init__(f"Crawl failed for {source}: {message}", ErrorCode.KB_CRAWL_FAILED, ctx, recoverable=True)


class IndexingError(KnowledgeBaseError):
    """Raised when document indexing fails."""

    def __init__(self, document_id: str, message: str, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("document_id", document_id)
        super().__init__(message, ErrorCode.KB_INDEX_FAILED, ctx, recoverable=True)


# ============================================================================
# Model/Bedrock Errors
# ============================================================================


class ModelError(AiCippyError):
    """Base class for model invocation errors."""

    pass


class ModelInvocationError(ModelError):
    """Raised when model invocation fails."""

    def __init__(self, model_id: str, message: str, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("model_id", model_id)
        super().__init__(message, ErrorCode.MODEL_INVOCATION_FAILED, ctx, recoverable=True)


class ModelRateLimitedError(ModelError):
    """Raised when model API is rate limited."""

    def __init__(
        self,
        model_id: str,
        retry_after: float | None = None,
        context: ErrorContext | None = None,
    ) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("model_id", model_id)
        if retry_after:
            ctx = ctx.with_detail("retry_after", retry_after)
        super().__init__(
            f"Model {model_id} rate limited",
            ErrorCode.MODEL_RATE_LIMITED,
            ctx,
            recoverable=True,
        )


class ContentFilteredError(ModelError):
    """Raised when content is filtered by guardrails."""

    def __init__(self, message: str = "Content filtered by safety guardrails", context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.MODEL_CONTENT_FILTERED, context, recoverable=False)


class ContextExceededError(ModelError):
    """Raised when model context window is exceeded."""

    def __init__(
        self,
        model_id: str,
        tokens_used: int,
        max_tokens: int,
        context: ErrorContext | None = None,
    ) -> None:
        ctx = context or ErrorContext()
        ctx = ctx.with_detail("model_id", model_id)
        ctx = ctx.with_detail("tokens_used", tokens_used)
        ctx = ctx.with_detail("max_tokens", max_tokens)
        super().__init__(
            f"Context exceeded: {tokens_used}/{max_tokens} tokens",
            ErrorCode.MODEL_CONTEXT_EXCEEDED,
            ctx,
            recoverable=False,
        )


# ============================================================================
# Configuration Errors
# ============================================================================


class ConfigurationError(AiCippyError):
    """Raised when configuration is invalid."""

    def __init__(self, message: str, context: ErrorContext | None = None) -> None:
        super().__init__(message, ErrorCode.CONFIGURATION, context, recoverable=False)


class ValidationError(AiCippyError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None, context: ErrorContext | None = None) -> None:
        ctx = context or ErrorContext()
        if field:
            ctx = ctx.with_detail("field", field)
        super().__init__(message, ErrorCode.VALIDATION, ctx, recoverable=False)
