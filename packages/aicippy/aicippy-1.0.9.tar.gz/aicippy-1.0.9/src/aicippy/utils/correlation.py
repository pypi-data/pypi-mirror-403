"""
Correlation ID management for request tracing.

Provides context management for correlation IDs that propagate
through the entire request lifecycle for distributed tracing.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token
from typing import Any

# Context variable for correlation ID
_correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    """
    Get the current correlation ID.

    Returns:
        Current correlation ID or empty string if not set.
    """
    return _correlation_id_var.get()


def set_correlation_id(correlation_id: str) -> Token[str]:
    """
    Set the correlation ID.

    Args:
        correlation_id: The correlation ID to set.

    Returns:
        Token that can be used to reset the value.
    """
    return _correlation_id_var.set(correlation_id)


def generate_correlation_id() -> str:
    """
    Generate a new unique correlation ID.

    Returns:
        A new UUID-based correlation ID.
    """
    return str(uuid.uuid4())


class CorrelationContext:
    """
    Context manager for correlation ID scope.

    Automatically generates a new correlation ID when entering the context
    and restores the previous value when exiting.

    Example:
        async with CorrelationContext():
            # All operations here will have the same correlation ID
            await process_request()
    """

    def __init__(self, correlation_id: str | None = None) -> None:
        """
        Initialize correlation context.

        Args:
            correlation_id: Optional specific correlation ID to use.
                          If not provided, a new one will be generated.
        """
        self._correlation_id = correlation_id or generate_correlation_id()
        self._token: Token[str] | None = None

    @property
    def correlation_id(self) -> str:
        """Get the correlation ID for this context."""
        return self._correlation_id

    def __enter__(self) -> "CorrelationContext":
        """Enter the correlation context."""
        self._token = set_correlation_id(self._correlation_id)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the correlation context, restoring previous value."""
        if self._token is not None:
            _correlation_id_var.reset(self._token)

    async def __aenter__(self) -> "CorrelationContext":
        """Async enter the correlation context."""
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async exit the correlation context."""
        self.__exit__(exc_type, exc_val, exc_tb)
