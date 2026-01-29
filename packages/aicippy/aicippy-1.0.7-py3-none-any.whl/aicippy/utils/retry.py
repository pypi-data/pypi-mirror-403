"""
Retry utilities with exponential backoff for AiCippy.

Provides decorators for both synchronous and asynchronous functions
with configurable retry behavior and circuit breaker patterns.

This module provides:
- Sync and async retry decorators with exponential backoff
- Circuit breaker pattern for external service calls
- Configurable retry conditions and limits
- Structured logging for observability

Example:
    >>> @async_retry(max_attempts=5, min_wait=1.0)
    ... async def fetch_data():
    ...     return await external_api.get_data()

    >>> breaker = CircuitBreaker(failure_threshold=5)
    >>> result = await breaker.call(risky_operation)
"""

from __future__ import annotations

import asyncio
import functools
import time
from collections.abc import Awaitable, Callable
from enum import Enum
from typing import Any, Final, ParamSpec, TypeVar

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from aicippy.utils.logging import get_logger

P = ParamSpec("P")
T = TypeVar("T")

logger = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

DEFAULT_MAX_ATTEMPTS: Final[int] = 3
DEFAULT_MIN_WAIT: Final[float] = 1.0
DEFAULT_MAX_WAIT: Final[float] = 60.0
DEFAULT_JITTER: Final[float] = 1.0

CIRCUIT_BREAKER_FAILURE_THRESHOLD: Final[int] = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT: Final[float] = 30.0
CIRCUIT_BREAKER_HALF_OPEN_REQUESTS: Final[int] = 3


# Default retryable exceptions
RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
    OSError,
)


# ============================================================================
# Retry Decorators
# ============================================================================


def sync_retry(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    jitter: float = DEFAULT_JITTER,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for synchronous functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3).
        min_wait: Minimum wait time between retries in seconds (default: 1.0).
        max_wait: Maximum wait time between retries in seconds (default: 60.0).
        jitter: Random jitter to add to wait time (default: 1.0).
        retryable_exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @sync_retry(max_attempts=5)
        ... def fetch_data():
        ...     return requests.get("https://api.example.com/data")

    Note:
        The wait time follows exponential backoff with jitter:
        wait = min(max_wait, min_wait * 2^attempt) + random(0, jitter)
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if min_wait <= 0:
        raise ValueError("min_wait must be positive")
    if max_wait < min_wait:
        raise ValueError("max_wait must be >= min_wait")

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retrying = Retrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential_jitter(
                    initial=min_wait,
                    max=max_wait,
                    jitter=jitter,
                ),
                retry=retry_if_exception_type(retryable_exceptions),
                reraise=True,
            )

            for attempt in retrying:
                with attempt:
                    attempt_number = attempt.retry_state.attempt_number
                    if attempt_number > 1:
                        logger.warning(
                            "retrying_operation",
                            function=func.__name__,
                            attempt=attempt_number,
                            max_attempts=max_attempts,
                        )
                    return func(*args, **kwargs)

            # This should never be reached due to reraise=True
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


def async_retry(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT,
    max_wait: float = DEFAULT_MAX_WAIT,
    jitter: float = DEFAULT_JITTER,
    retryable_exceptions: tuple[type[Exception], ...] = RETRYABLE_EXCEPTIONS,
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    """
    Decorator for asynchronous functions with exponential backoff retry.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3).
        min_wait: Minimum wait time between retries in seconds (default: 1.0).
        max_wait: Maximum wait time between retries in seconds (default: 60.0).
        jitter: Random jitter to add to wait time (default: 1.0).
        retryable_exceptions: Tuple of exception types to retry on.

    Returns:
        Decorated async function with retry logic.

    Example:
        >>> @async_retry(max_attempts=5, min_wait=0.5)
        ... async def fetch_data():
        ...     async with httpx.AsyncClient() as client:
        ...         return await client.get("https://api.example.com/data")

    Note:
        The wait time follows exponential backoff with jitter:
        wait = min(max_wait, min_wait * 2^attempt) + random(0, jitter)
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")
    if min_wait <= 0:
        raise ValueError("min_wait must be positive")
    if max_wait < min_wait:
        raise ValueError("max_wait must be >= min_wait")

    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retrying = AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential_jitter(
                    initial=min_wait,
                    max=max_wait,
                    jitter=jitter,
                ),
                retry=retry_if_exception_type(retryable_exceptions),
                reraise=True,
            )

            async for attempt in retrying:
                with attempt:
                    attempt_number = attempt.retry_state.attempt_number
                    if attempt_number > 1:
                        logger.warning(
                            "retrying_async_operation",
                            function=func.__name__,
                            attempt=attempt_number,
                            max_attempts=max_attempts,
                        )
                    return await func(*args, **kwargs)

            # This should never be reached due to reraise=True
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


# ============================================================================
# Circuit Breaker
# ============================================================================


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(Exception):
    """
    Raised when a call is attempted while the circuit breaker is open.

    Attributes:
        recovery_time: Seconds until the circuit may close.
    """

    __slots__ = ("recovery_time",)

    def __init__(self, message: str, recovery_time: float | None = None) -> None:
        super().__init__(message)
        self.recovery_time = recovery_time


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.

    Prevents cascading failures by temporarily stopping calls to
    a failing service after a threshold of failures is reached.

    States:
    - CLOSED: Normal operation, all calls pass through
    - OPEN: Failing, calls are rejected immediately
    - HALF_OPEN: Testing, limited calls allowed to check recovery

    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30.0)
        >>> try:
        ...     result = await breaker.call(risky_operation)
        ... except CircuitBreakerOpenError:
        ...     # Service is down, use fallback
        ...     result = get_cached_value()

    Thread Safety:
        This implementation uses asyncio.Lock for thread-safe state updates
        in async contexts.
    """

    __slots__ = (
        "_failure_threshold",
        "_recovery_timeout",
        "_half_open_requests",
        "_failure_count",
        "_success_count",
        "_last_failure_time",
        "_state",
        "_lock",
    )

    def __init__(
        self,
        failure_threshold: int = CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout: float = CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        half_open_requests: int = CIRCUIT_BREAKER_HALF_OPEN_REQUESTS,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit (default: 5).
            recovery_timeout: Seconds to wait before allowing test requests (default: 30.0).
            half_open_requests: Number of successful requests to close circuit (default: 3).

        Raises:
            ValueError: If any parameter is invalid.
        """
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be at least 1")
        if recovery_timeout <= 0:
            raise ValueError("recovery_timeout must be positive")
        if half_open_requests < 1:
            raise ValueError("half_open_requests must be at least 1")

        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._half_open_requests = half_open_requests

        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Current circuit breaker state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (rejecting calls)."""
        return self._state == CircuitState.OPEN

    @property
    def failure_count(self) -> int:
        """Current failure count."""
        return self._failure_count

    @property
    def time_until_recovery(self) -> float | None:
        """
        Seconds until circuit may transition to half-open.

        Returns:
            Seconds remaining, or None if not applicable.
        """
        if self._state != CircuitState.OPEN or self._last_failure_time is None:
            return None
        elapsed = time.monotonic() - self._last_failure_time
        remaining = self._recovery_timeout - elapsed
        return max(0.0, remaining)

    async def _check_state(self) -> None:
        """Check and potentially update circuit state based on timeout."""
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self._recovery_timeout:
                async with self._lock:
                    # Double-check after acquiring lock
                    if self._state == CircuitState.OPEN:
                        self._state = CircuitState.HALF_OPEN
                        self._success_count = 0
                        logger.info(
                            "circuit_breaker_half_open",
                            recovery_timeout=self._recovery_timeout,
                        )

    async def record_success(self) -> None:
        """
        Record a successful call.

        In half-open state, enough successes will close the circuit.
        In closed state, reduces the failure count.
        """
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self._half_open_requests:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._last_failure_time = None
                    logger.info(
                        "circuit_breaker_closed",
                        success_count=self._success_count,
                    )
            elif self._state == CircuitState.CLOSED:
                # Gradually reduce failure count on success
                self._failure_count = max(0, self._failure_count - 1)

    async def record_failure(self, error: Exception | None = None) -> None:
        """
        Record a failed call.

        In half-open state, immediately reopens the circuit.
        In closed state, may open the circuit if threshold is reached.

        Args:
            error: The exception that caused the failure (for logging).
        """
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                logger.warning(
                    "circuit_breaker_reopened",
                    error=str(error) if error else None,
                )
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self._failure_threshold:
                    self._state = CircuitState.OPEN
                    logger.warning(
                        "circuit_breaker_opened",
                        failure_count=self._failure_count,
                        threshold=self._failure_threshold,
                        error=str(error) if error else None,
                    )

    async def call(
        self,
        func: Callable[P, Awaitable[T]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Async function to call.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            Result of the function call.

        Raises:
            CircuitBreakerOpenError: If circuit is open and not ready for recovery.
            Exception: Any exception from the function call.
        """
        await self._check_state()

        if self._state == CircuitState.OPEN:
            time_remaining = self.time_until_recovery
            raise CircuitBreakerOpenError(
                f"Circuit breaker is open. Recovery in {time_remaining:.1f}s."
                if time_remaining
                else "Circuit breaker is open.",
                recovery_time=time_remaining,
            )

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure(e)
            raise

    def reset(self) -> None:
        """
        Reset the circuit breaker to closed state.

        Use this for manual recovery or testing.
        Note: This is not thread-safe for async contexts.
        """
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        logger.info("circuit_breaker_reset")

    def get_stats(self) -> dict[str, Any]:
        """
        Get circuit breaker statistics.

        Returns:
            Dictionary with current stats including state, counts, and timing.
        """
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self._failure_threshold,
            "recovery_timeout": self._recovery_timeout,
            "time_until_recovery": self.time_until_recovery,
        }
