"""
Real-time WebSocket communication handler for AiCippy.

Provides smooth streaming, connection management, and UI integration
for real-time agent-user communication.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Final

from aicippy.utils.logging import get_logger
from aicippy.websocket.client import WebSocketClient
from aicippy.websocket.models import (
    AgentUpdate,
    MessageType,
    ToolOutput,
    WebSocketMessage,
)

logger = get_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

HEARTBEAT_INTERVAL: Final[float] = 15.0  # seconds
CONNECTION_TIMEOUT: Final[float] = 10.0  # seconds
RECONNECT_DELAY: Final[float] = 2.0  # initial delay
MAX_RECONNECT_ATTEMPTS: Final[int] = 5
STREAM_BUFFER_SIZE: Final[int] = 100  # characters before flush


class ConnectionState(Enum):
    """WebSocket connection states."""

    DISCONNECTED = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATING = auto()
    AUTHENTICATED = auto()
    RECONNECTING = auto()
    ERROR = auto()


class StreamState(Enum):
    """Streaming response states."""

    IDLE = auto()
    RECEIVING = auto()
    COMPLETE = auto()
    ERROR = auto()


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ConnectionStatus:
    """Current connection status."""

    state: ConnectionState = ConnectionState.DISCONNECTED
    latency_ms: float = 0.0
    last_ping: datetime | None = None
    reconnect_attempts: int = 0
    error_message: str | None = None
    connected_at: datetime | None = None

    @property
    def is_healthy(self) -> bool:
        """Check if connection is healthy."""
        return self.state in (
            ConnectionState.CONNECTED,
            ConnectionState.AUTHENTICATED,
        )

    @property
    def uptime_seconds(self) -> float:
        """Get connection uptime in seconds."""
        if self.connected_at is None:
            return 0.0
        return (datetime.now() - self.connected_at).total_seconds()


@dataclass
class StreamBuffer:
    """Buffer for streaming responses with smooth display."""

    content: str = ""
    tokens_received: int = 0
    state: StreamState = StreamState.IDLE
    started_at: datetime | None = None
    completed_at: datetime | None = None
    _pending: str = ""

    def append(self, chunk: str) -> str | None:
        """
        Append chunk to buffer and return displayable content.

        Returns content when buffer is ready to flush, None otherwise.
        """
        self._pending += chunk
        self.tokens_received += 1

        # Flush on newline, punctuation, or buffer size
        if (
            "\n" in chunk
            or chunk.endswith((".", "!", "?", ":", ";"))
            or len(self._pending) >= STREAM_BUFFER_SIZE
        ):
            result = self._pending
            self._pending = ""
            self.content += result
            return result

        return None

    def flush(self) -> str:
        """Force flush any pending content."""
        if self._pending:
            result = self._pending
            self._pending = ""
            self.content += result
            return result
        return ""

    def reset(self) -> None:
        """Reset buffer for new stream."""
        self.content = ""
        self.tokens_received = 0
        self.state = StreamState.IDLE
        self.started_at = None
        self.completed_at = None
        self._pending = ""

    @property
    def duration_seconds(self) -> float:
        """Get streaming duration."""
        if self.started_at is None:
            return 0.0
        end = self.completed_at or datetime.now()
        return (end - self.started_at).total_seconds()

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second."""
        duration = self.duration_seconds
        if duration <= 0:
            return 0.0
        return self.tokens_received / duration


@dataclass
class AgentState:
    """Track agent state for UI display."""

    agent_id: str
    agent_type: str
    status: str = "idle"
    progress: int = 0
    message: str = ""
    tokens_used: int = 0
    started_at: datetime | None = None
    last_update: datetime = field(default_factory=datetime.now)

    def update(self, update: AgentUpdate) -> bool:
        """
        Update agent state from update message.

        Returns True if state changed.
        """
        changed = (
            self.status != update.status
            or self.progress != update.progress
            or self.message != update.message
        )

        self.status = update.status
        self.progress = update.progress
        self.message = update.message
        self.tokens_used = update.tokens_used
        self.last_update = datetime.now()

        if self.started_at is None and update.status == "running":
            self.started_at = datetime.now()

        return changed


# ============================================================================
# Event Callbacks Type Definitions
# ============================================================================


OnConnectionChange = Callable[[ConnectionStatus], None]
OnStreamToken = Callable[[str, StreamBuffer], None]
OnStreamComplete = Callable[[str, StreamBuffer], None]
OnAgentUpdate = Callable[[AgentState], None]
OnToolOutput = Callable[[ToolOutput], None]
OnError = Callable[[str, Exception | None], None]


# ============================================================================
# Real-time Communication Manager
# ============================================================================


class RealtimeManager:
    """
    Manages real-time WebSocket communication with smooth streaming.

    Provides:
    - Connection state management with UI callbacks
    - Smooth streaming with buffered display
    - Agent state tracking
    - Heartbeat monitoring
    - Automatic reconnection with backoff

    Usage:
        manager = RealtimeManager()
        manager.on_connection_change = lambda s: print(f"State: {s.state}")
        manager.on_stream_token = lambda t, b: print(t, end="")

        await manager.connect()
        response = await manager.send_message("Hello!")
        await manager.disconnect()
    """

    def __init__(self) -> None:
        """Initialize realtime manager."""
        self._client = WebSocketClient()
        self._connection_status = ConnectionStatus()
        self._stream_buffer = StreamBuffer()
        self._agents: dict[str, AgentState] = {}

        # Callbacks
        self._on_connection_change: OnConnectionChange | None = None
        self._on_stream_token: OnStreamToken | None = None
        self._on_stream_complete: OnStreamComplete | None = None
        self._on_agent_update: OnAgentUpdate | None = None
        self._on_tool_output: OnToolOutput | None = None
        self._on_error: OnError | None = None

        # Background tasks
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._ping_time: float | None = None

    # ========================================================================
    # Properties - Callbacks
    # ========================================================================

    @property
    def on_connection_change(self) -> OnConnectionChange | None:
        """Get connection change callback."""
        return self._on_connection_change

    @on_connection_change.setter
    def on_connection_change(self, callback: OnConnectionChange | None) -> None:
        """Set connection change callback."""
        self._on_connection_change = callback

    @property
    def on_stream_token(self) -> OnStreamToken | None:
        """Get stream token callback."""
        return self._on_stream_token

    @on_stream_token.setter
    def on_stream_token(self, callback: OnStreamToken | None) -> None:
        """Set stream token callback."""
        self._on_stream_token = callback

    @property
    def on_stream_complete(self) -> OnStreamComplete | None:
        """Get stream complete callback."""
        return self._on_stream_complete

    @on_stream_complete.setter
    def on_stream_complete(self, callback: OnStreamComplete | None) -> None:
        """Set stream complete callback."""
        self._on_stream_complete = callback

    @property
    def on_agent_update(self) -> OnAgentUpdate | None:
        """Get agent update callback."""
        return self._on_agent_update

    @on_agent_update.setter
    def on_agent_update(self, callback: OnAgentUpdate | None) -> None:
        """Set agent update callback."""
        self._on_agent_update = callback

    @property
    def on_tool_output(self) -> OnToolOutput | None:
        """Get tool output callback."""
        return self._on_tool_output

    @on_tool_output.setter
    def on_tool_output(self, callback: OnToolOutput | None) -> None:
        """Set tool output callback."""
        self._on_tool_output = callback

    @property
    def on_error(self) -> OnError | None:
        """Get error callback."""
        return self._on_error

    @on_error.setter
    def on_error(self, callback: OnError | None) -> None:
        """Set error callback."""
        self._on_error = callback

    # ========================================================================
    # Properties - State
    # ========================================================================

    @property
    def connection_status(self) -> ConnectionStatus:
        """Get current connection status."""
        return self._connection_status

    @property
    def is_connected(self) -> bool:
        """Check if connected and authenticated."""
        return self._connection_status.is_healthy

    @property
    def agents(self) -> dict[str, AgentState]:
        """Get tracked agents."""
        return self._agents.copy()

    @property
    def stream_buffer(self) -> StreamBuffer:
        """Get current stream buffer."""
        return self._stream_buffer

    # ========================================================================
    # Connection Management
    # ========================================================================

    async def connect(self) -> bool:
        """
        Establish WebSocket connection.

        Returns:
            True if connection successful.
        """
        self._set_connection_state(ConnectionState.CONNECTING)

        try:
            # Connect to WebSocket
            success = await asyncio.wait_for(
                self._client.connect(),
                timeout=CONNECTION_TIMEOUT,
            )

            if success:
                self._set_connection_state(ConnectionState.CONNECTED)
                self._connection_status.connected_at = datetime.now()
                self._connection_status.reconnect_attempts = 0

                # Setup message handlers
                self._setup_handlers()

                # Start heartbeat
                self._start_heartbeat()

                # Authenticate (happens automatically in client)
                self._set_connection_state(ConnectionState.AUTHENTICATED)

                return True
            else:
                self._set_connection_state(
                    ConnectionState.ERROR,
                    error="Connection failed",
                )
                return False

        except asyncio.TimeoutError:
            self._set_connection_state(
                ConnectionState.ERROR,
                error="Connection timeout",
            )
            return False
        except Exception as e:
            self._set_connection_state(
                ConnectionState.ERROR,
                error=str(e),
            )
            self._notify_error("Connection failed", e)
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        # Stop heartbeat
        self._stop_heartbeat()

        # Disconnect client
        await self._client.disconnect()

        # Update state
        self._set_connection_state(ConnectionState.DISCONNECTED)
        self._connection_status.connected_at = None

    async def reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.

        Returns:
            True if reconnection successful.
        """
        self._set_connection_state(ConnectionState.RECONNECTING)

        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            self._connection_status.reconnect_attempts = attempt

            delay = RECONNECT_DELAY * (2 ** (attempt - 1))
            logger.info(
                "reconnecting",
                attempt=attempt,
                delay=delay,
            )

            await asyncio.sleep(delay)

            if await self.connect():
                return True

        self._set_connection_state(
            ConnectionState.ERROR,
            error=f"Reconnection failed after {MAX_RECONNECT_ATTEMPTS} attempts",
        )
        return False

    # ========================================================================
    # Message Sending
    # ========================================================================

    async def send_message(
        self,
        message: str,
        stream: bool = True,
    ) -> str:
        """
        Send a chat message and get response.

        Args:
            message: User message to send.
            stream: Whether to stream the response.

        Returns:
            Complete response text.
        """
        if not self.is_connected:
            raise ConnectionError("Not connected")

        # Reset stream buffer
        self._stream_buffer.reset()
        self._stream_buffer.state = StreamState.RECEIVING
        self._stream_buffer.started_at = datetime.now()

        try:
            if stream:
                response = await self._client.stream_chat(
                    message=message,
                    on_token=self._handle_stream_token,
                    on_agent_update=self._handle_agent_update_message,
                    on_tool_output=self._handle_tool_output_message,
                )
            else:
                result = await self._client.send_and_wait(
                    MessageType.CHAT,
                    {"message": message},
                    timeout=300.0,
                )
                response = result.get("content", "")

            # Mark stream complete
            self._stream_buffer.state = StreamState.COMPLETE
            self._stream_buffer.completed_at = datetime.now()

            # Flush any remaining content
            remaining = self._stream_buffer.flush()
            if remaining and self._on_stream_token:
                self._on_stream_token(remaining, self._stream_buffer)

            # Notify completion
            if self._on_stream_complete:
                self._on_stream_complete(response, self._stream_buffer)

            return response

        except Exception as e:
            self._stream_buffer.state = StreamState.ERROR
            self._notify_error("Message send failed", e)
            raise

    async def send_command(
        self,
        command: str,
        args: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Send a command message.

        Args:
            command: Command name.
            args: Command arguments.

        Returns:
            Command response.
        """
        if not self.is_connected:
            raise ConnectionError("Not connected")

        payload = {"command": command}
        if args:
            payload["args"] = args

        return await self._client.send_and_wait(
            MessageType.COMMAND,
            payload,
            timeout=60.0,
        )

    # ========================================================================
    # Internal Handlers
    # ========================================================================

    def _setup_handlers(self) -> None:
        """Setup WebSocket message handlers."""
        self._client.on_message(MessageType.RESPONSE, self._handle_response)
        self._client.on_message(MessageType.AGENT_UPDATE, self._handle_agent_update)
        self._client.on_message(MessageType.TOOL_OUTPUT, self._handle_tool_output)
        self._client.on_message(MessageType.ERROR, self._handle_error)
        self._client.on_message(MessageType.PONG, self._handle_pong)

    def _handle_response(self, payload: dict[str, Any]) -> None:
        """Handle response message."""
        # Response chunks handled via stream_chat callback
        pass

    def _handle_stream_token(self, token: str) -> None:
        """Handle streaming token."""
        displayable = self._stream_buffer.append(token)

        if displayable and self._on_stream_token:
            self._on_stream_token(displayable, self._stream_buffer)

    def _handle_agent_update(self, payload: dict[str, Any]) -> None:
        """Handle agent update message."""
        try:
            update = AgentUpdate.from_dict(payload)
            self._handle_agent_update_message(update)
        except Exception as e:
            logger.warning("agent_update_parse_error", error=str(e))

    def _handle_agent_update_message(self, update: AgentUpdate) -> None:
        """Process agent update."""
        agent_id = update.agent_id

        # Get or create agent state
        if agent_id not in self._agents:
            self._agents[agent_id] = AgentState(
                agent_id=agent_id,
                agent_type=update.agent_type,
            )

        agent_state = self._agents[agent_id]
        changed = agent_state.update(update)

        # Notify if changed
        if changed and self._on_agent_update:
            self._on_agent_update(agent_state)

    def _handle_tool_output(self, payload: dict[str, Any]) -> None:
        """Handle tool output message."""
        try:
            output = ToolOutput.from_dict(payload)
            self._handle_tool_output_message(output)
        except Exception as e:
            logger.warning("tool_output_parse_error", error=str(e))

    def _handle_tool_output_message(self, output: ToolOutput) -> None:
        """Process tool output."""
        if self._on_tool_output:
            self._on_tool_output(output)

    def _handle_error(self, payload: dict[str, Any]) -> None:
        """Handle error message from server."""
        error_msg = payload.get("message", "Unknown error")
        self._notify_error(error_msg, None)

    def _handle_pong(self, payload: dict[str, Any]) -> None:
        """Handle pong response for latency measurement."""
        if self._ping_time is not None:
            import time

            latency = (time.monotonic() - self._ping_time) * 1000
            self._connection_status.latency_ms = latency
            self._connection_status.last_ping = datetime.now()
            self._ping_time = None

    # ========================================================================
    # Heartbeat
    # ========================================================================

    def _start_heartbeat(self) -> None:
        """Start heartbeat task."""
        if self._heartbeat_task is None:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

    def _stop_heartbeat(self) -> None:
        """Stop heartbeat task."""
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
            self._heartbeat_task = None

    async def _heartbeat_loop(self) -> None:
        """Background heartbeat loop."""
        import time

        while self.is_connected:
            try:
                # Send ping
                self._ping_time = time.monotonic()
                await self._client.send(MessageType.PING, {})
                await asyncio.sleep(HEARTBEAT_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning("heartbeat_error", error=str(e))
                # Connection may be lost
                if not self._client.is_connected:
                    await self.reconnect()
                    break

    # ========================================================================
    # State Management
    # ========================================================================

    def _set_connection_state(
        self,
        state: ConnectionState,
        error: str | None = None,
    ) -> None:
        """Update connection state and notify."""
        self._connection_status.state = state
        self._connection_status.error_message = error

        if self._on_connection_change:
            self._on_connection_change(self._connection_status)

    def _notify_error(self, message: str, exception: Exception | None) -> None:
        """Notify error callback."""
        logger.error("realtime_error", message=message, error=str(exception))

        if self._on_error:
            self._on_error(message, exception)

    def clear_agents(self) -> None:
        """Clear tracked agents."""
        self._agents.clear()

    # ========================================================================
    # Context Manager
    # ========================================================================

    async def __aenter__(self) -> "RealtimeManager":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()
