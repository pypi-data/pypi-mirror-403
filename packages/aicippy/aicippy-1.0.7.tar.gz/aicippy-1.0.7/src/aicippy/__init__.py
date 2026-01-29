"""
AiCippy - Enterprise-grade multi-agent CLI system powered by AWS Bedrock.

This package provides a production-ready CLI tool for orchestrating
AI agents with support for:

- Multi-agent task orchestration (up to 10 parallel agents)
- AWS Bedrock integration (Claude Opus 4.5, Sonnet 4.5, Llama 4)
- Cognito authentication with secure token storage
- MCP-style tool connectors for cloud services
- Knowledge base with automated feed crawling
- Real-time WebSocket communication
- Structured logging and observability

Quick Start:
    >>> from aicippy import get_settings, AgentOrchestrator
    >>> settings = get_settings()
    >>> async with AgentOrchestrator() as orchestrator:
    ...     response = await orchestrator.chat("Hello!")

Copyright (c) 2024-2026 AiVibe Software Services Pvt Ltd. All rights reserved.
ISO 27001:2022 Certified | NVIDIA Inception Partner | AWS Activate | Microsoft for Startups

Author: Aravind Jayamohan <aravind@aivibe.in>
"""

from __future__ import annotations

from typing import Final

# Package metadata
__version__: Final[str] = "1.0.7"
__author__: Final[str] = "Aravind Jayamohan"
__email__: Final[str] = "aravind@aivibe.in"
__license__: Final[str] = "Proprietary"
__copyright__: Final[str] = "Copyright (c) 2024-2026 AiVibe Software Services Pvt Ltd"

# Configuration
from aicippy.config import Settings, get_settings

# Exceptions (public API for error handling)
from aicippy.exceptions import (
    AgentError,
    AgentExecutionError,
    AgentQuotaExceededError,
    AgentSpawnError,
    AgentTimeoutError,
    AiCippyError,
    AuthenticationError,
    AuthenticationExpiredError,
    AuthenticationInvalidError,
    AuthenticationRequiredError,
    CommandBlockedError,
    CommandExecutionError,
    ConfigurationError,
    ConnectorError,
    ConnectorTimeoutError,
    ConnectorUnavailableError,
    ContentFilteredError,
    ContextExceededError,
    CredentialStorageError,
    ErrorCode,
    ErrorContext,
    KnowledgeBaseError,
    ModelError,
    ModelInvocationError,
    ModelRateLimitedError,
    TokenRefreshError,
    ValidationError,
    WebSocketConnectionError,
    WebSocketDisconnectedError,
    WebSocketError,
    WebSocketMessageError,
)

# Types (public type aliases and protocols)
from aicippy.types import (
    AgentId,
    ConnectionId,
    ConnectionState,
    CorrelationId,
    DocumentId,
    ExecutionMode,
    JsonDict,
    JsonValue,
    Result,
    SessionId,
    TaskId,
    ToolCategory,
)

# Lazy imports for heavy modules
def __getattr__(name: str):
    """Lazy import for heavy modules to improve startup time."""
    if name == "AgentOrchestrator":
        from aicippy.agents.orchestrator import AgentOrchestrator
        return AgentOrchestrator
    elif name == "CognitoAuth":
        from aicippy.auth.cognito import CognitoAuth
        return CognitoAuth
    elif name == "BaseConnector":
        from aicippy.connectors.base import BaseConnector
        return BaseConnector
    elif name == "ConnectorConfig":
        from aicippy.connectors.base import ConnectorConfig
        return ConnectorConfig
    elif name == "ToolResult":
        from aicippy.connectors.base import ToolResult
        return ToolResult
    elif name == "CircuitBreaker":
        from aicippy.utils.retry import CircuitBreaker
        return CircuitBreaker
    elif name == "CircuitBreakerOpenError":
        from aicippy.utils.retry import CircuitBreakerOpenError
        return CircuitBreakerOpenError
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Metadata
    "__version__",
    "__author__",
    "__email__",
    "__license__",
    "__copyright__",
    # Configuration
    "Settings",
    "get_settings",
    # Core Classes (lazy loaded)
    "AgentOrchestrator",
    "CognitoAuth",
    "BaseConnector",
    "ConnectorConfig",
    "ToolResult",
    "CircuitBreaker",
    "CircuitBreakerOpenError",
    # Type Aliases
    "SessionId",
    "CorrelationId",
    "AgentId",
    "TaskId",
    "DocumentId",
    "ConnectionId",
    "JsonValue",
    "JsonDict",
    "Result",
    # Enums
    "ExecutionMode",
    "ConnectionState",
    "ToolCategory",
    "ErrorCode",
    # Base Exceptions
    "AiCippyError",
    "ErrorContext",
    "ConfigurationError",
    "ValidationError",
    # Auth Exceptions
    "AuthenticationError",
    "AuthenticationRequiredError",
    "AuthenticationExpiredError",
    "AuthenticationInvalidError",
    "TokenRefreshError",
    "CredentialStorageError",
    # Agent Exceptions
    "AgentError",
    "AgentSpawnError",
    "AgentTimeoutError",
    "AgentExecutionError",
    "AgentQuotaExceededError",
    # Connector Exceptions
    "ConnectorError",
    "ConnectorUnavailableError",
    "CommandBlockedError",
    "CommandExecutionError",
    "ConnectorTimeoutError",
    # WebSocket Exceptions
    "WebSocketError",
    "WebSocketConnectionError",
    "WebSocketDisconnectedError",
    "WebSocketMessageError",
    # Knowledge Base Exceptions
    "KnowledgeBaseError",
    # Model Exceptions
    "ModelError",
    "ModelInvocationError",
    "ModelRateLimitedError",
    "ContentFilteredError",
    "ContextExceededError",
]
