"""
Structured logging configuration for AiCippy.

Provides correlation ID tracking, JSON and console output formats,
and secure handling to prevent secret leakage.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

import structlog
from structlog.types import EventDict, Processor

if TYPE_CHECKING:
    from aicippy.config import Settings

# Context variable for correlation ID
_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str | None:
    """Get current correlation ID from context."""
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    _correlation_id.set(correlation_id)


def add_correlation_id(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add correlation ID to log event if available."""
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id
    return event_dict


def add_service_info(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """Add service information to log event."""
    event_dict["service"] = "aicippy"
    return event_dict


# Patterns that indicate sensitive data - NEVER log these
SENSITIVE_PATTERNS = frozenset({
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "api-key",
    "authorization",
    "bearer",
    "credential",
    "private_key",
    "privatekey",
    "access_key",
    "accesskey",
    "session_id",
    "sessionid",
    "jwt",
    "cookie",
})


def mask_sensitive_data(
    logger: logging.Logger,
    method_name: str,
    event_dict: EventDict,
) -> EventDict:
    """
    Mask sensitive data in log events.

    Replaces values for keys matching sensitive patterns with '[REDACTED]'.
    This is a critical security measure to prevent credential leakage.
    """
    def _mask_dict(d: dict[str, Any]) -> dict[str, Any]:
        masked = {}
        for key, value in d.items():
            key_lower = key.lower()
            is_sensitive = any(pattern in key_lower for pattern in SENSITIVE_PATTERNS)

            if is_sensitive:
                masked[key] = "[REDACTED]"
            elif isinstance(value, dict):
                masked[key] = _mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    _mask_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                masked[key] = value
        return masked

    return _mask_dict(event_dict)


def setup_logging(settings: Settings) -> None:
    """
    Configure structured logging for the application.

    Args:
        settings: Application settings containing log configuration.
    """
    # Determine processors based on output format
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_correlation_id,
        add_service_info,
        mask_sensitive_data,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        # JSON format for production/cloud logging
        renderer: Processor = structlog.processors.JSONRenderer()
    else:
        # Console format for local development
        renderer = structlog.dev.ConsoleRenderer(
            colors=True,
            exception_formatter=structlog.dev.plain_traceback,
        )

    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            processor=renderer,
            foreign_pre_chain=shared_processors,
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, settings.log_level))

    # Reduce noise from third-party libraries
    for logger_name in ("boto3", "botocore", "urllib3", "websockets"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger for the given name.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A bound structured logger instance.
    """
    return structlog.get_logger(name)
