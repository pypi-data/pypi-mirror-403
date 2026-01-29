"""
WebSocket client for AiCippy.

Provides real-time bidirectional communication with the backend
via API Gateway WebSocket.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

import websockets
from websockets.client import WebSocketClientProtocol
from websockets.exceptions import ConnectionClosed, WebSocketException

from aicippy.auth.cognito import CognitoAuth
from aicippy.config import get_settings
from aicippy.utils.correlation import get_correlation_id
from aicippy.utils.logging import get_logger
from aicippy.utils.retry import async_retry
from aicippy.websocket.models import (
    AgentUpdate,
    MessageType,
    ToolOutput,
    WebSocketMessage,
)

logger = get_logger(__name__)


class WebSocketClient:
    """
    WebSocket client for real-time communication.

    Handles connection management, authentication, reconnection,
    and message routing.
    """

    def __init__(self) -> None:
        """Initialize WebSocket client."""
        self._settings = get_settings()
        self._auth = CognitoAuth()
        self._ws: WebSocketClientProtocol | None = None
        self._connected = False
        self._reconnect_task: asyncio.Task[None] | None = None
        self._receive_task: asyncio.Task[None] | None = None
        self._message_handlers: dict[MessageType, list[Callable[[dict[str, Any]], None]]] = {}
        self._pending_responses: dict[str, asyncio.Future[dict[str, Any]]] = {}

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected and self._ws is not None and not self._ws.closed

    async def connect(self) -> bool:
        """
        Establish WebSocket connection.

        Returns:
            True if connection successful, False otherwise.
        """
        if self.is_connected:
            return True

        # Get authentication token
        tokens = self._auth.get_current_tokens()
        if not tokens:
            logger.error("websocket_no_auth_token")
            return False

        url = self._settings.websocket_url
        logger.info("websocket_connecting", url=url)

        try:
            self._ws = await websockets.connect(
                url,
                additional_headers={
                    "Authorization": f"Bearer {tokens.access_token}",
                },
                ping_interval=30,
                ping_timeout=10,
                close_timeout=5,
            )

            self._connected = True
            logger.info("websocket_connected")

            # Start receive loop
            self._receive_task = asyncio.create_task(self._receive_loop())

            # Authenticate
            await self._authenticate(tokens.access_token)

            return True

        except WebSocketException as e:
            logger.error("websocket_connection_failed", error=str(e))
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._connected = False

        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass
            self._reconnect_task = None

        if self._ws:
            await self._ws.close()
            self._ws = None

        logger.info("websocket_disconnected")

    async def _authenticate(self, token: str) -> None:
        """
        Send authentication message.

        Args:
            token: Access token for authentication.
        """
        await self.send(
            MessageType.AUTHENTICATE,
            {"token": token},
        )

    async def send(
        self,
        message_type: MessageType,
        payload: dict[str, Any],
        correlation_id: str | None = None,
    ) -> None:
        """
        Send a message through the WebSocket.

        Args:
            message_type: Type of message to send.
            payload: Message payload.
            correlation_id: Optional correlation ID for tracking.
        """
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")

        message = WebSocketMessage(
            type=message_type,
            payload=payload,
            correlation_id=correlation_id or get_correlation_id(),
        )

        try:
            await self._ws.send(json.dumps(message.to_dict()))  # type: ignore
            logger.debug("websocket_message_sent", type=message_type.value)
        except ConnectionClosed:
            logger.warning("websocket_send_connection_closed")
            self._connected = False
            raise ConnectionError("WebSocket connection closed")

    async def send_and_wait(
        self,
        message_type: MessageType,
        payload: dict[str, Any],
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """
        Send a message and wait for response.

        Args:
            message_type: Type of message to send.
            payload: Message payload.
            timeout: Maximum time to wait for response.

        Returns:
            Response payload.
        """
        correlation_id = get_correlation_id() or str(id(payload))
        future: asyncio.Future[dict[str, Any]] = asyncio.get_event_loop().create_future()
        self._pending_responses[correlation_id] = future

        try:
            await self.send(message_type, payload, correlation_id)
            return await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("websocket_response_timeout", correlation_id=correlation_id)
            raise TimeoutError("Response timeout")
        finally:
            self._pending_responses.pop(correlation_id, None)

    async def _receive_loop(self) -> None:
        """Background loop to receive messages."""
        while self._connected and self._ws:
            try:
                message = await self._ws.recv()
                await self._handle_message(message)
            except ConnectionClosed:
                logger.warning("websocket_connection_closed")
                self._connected = False
                await self._attempt_reconnect()
                break
            except Exception as e:
                logger.exception("websocket_receive_error", error=str(e))

    async def _handle_message(self, raw_message: str | bytes) -> None:
        """
        Handle incoming WebSocket message.

        Args:
            raw_message: Raw message data from WebSocket.
        """
        try:
            if isinstance(raw_message, bytes):
                raw_message = raw_message.decode("utf-8")

            data = json.loads(raw_message)
            message = WebSocketMessage.from_dict(data)

            logger.debug("websocket_message_received", type=message.type.value)

            # Check for pending response
            if message.correlation_id and message.correlation_id in self._pending_responses:
                future = self._pending_responses.pop(message.correlation_id)
                if not future.done():
                    future.set_result(message.payload)
                return

            # Route to registered handlers
            handlers = self._message_handlers.get(message.type, [])
            for handler in handlers:
                try:
                    handler(message.payload)
                except Exception as e:
                    logger.exception("websocket_handler_error", error=str(e))

        except json.JSONDecodeError as e:
            logger.warning("websocket_invalid_json", error=str(e))

    def on_message(
        self,
        message_type: MessageType,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Register a message handler.

        Args:
            message_type: Type of message to handle.
            handler: Callback function for the message.
        """
        if message_type not in self._message_handlers:
            self._message_handlers[message_type] = []
        self._message_handlers[message_type].append(handler)

    def remove_handler(
        self,
        message_type: MessageType,
        handler: Callable[[dict[str, Any]], None],
    ) -> None:
        """
        Remove a message handler.

        Args:
            message_type: Type of message.
            handler: Handler to remove.
        """
        if message_type in self._message_handlers:
            self._message_handlers[message_type] = [
                h for h in self._message_handlers[message_type] if h != handler
            ]

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect with exponential backoff."""
        max_attempts = self._settings.websocket_reconnect_attempts
        base_delay = self._settings.websocket_reconnect_delay

        for attempt in range(1, max_attempts + 1):
            delay = base_delay * (2 ** (attempt - 1))
            logger.info(
                "websocket_reconnecting",
                attempt=attempt,
                max_attempts=max_attempts,
                delay=delay,
            )

            await asyncio.sleep(delay)

            if await self.connect():
                logger.info("websocket_reconnected", attempt=attempt)
                return

        logger.error("websocket_reconnect_failed", attempts=max_attempts)

    @asynccontextmanager
    async def session(self) -> AsyncIterator["WebSocketClient"]:
        """
        Context manager for WebSocket session.

        Usage:
            async with client.session():
                await client.send(...)
        """
        try:
            connected = await self.connect()
            if not connected:
                raise ConnectionError("Failed to connect WebSocket")
            yield self
        finally:
            await self.disconnect()

    async def stream_chat(
        self,
        message: str,
        on_token: Callable[[str], None] | None = None,
        on_agent_update: Callable[[AgentUpdate], None] | None = None,
        on_tool_output: Callable[[ToolOutput], None] | None = None,
    ) -> str:
        """
        Stream a chat response with callbacks for tokens and updates.

        Args:
            message: User message to send.
            on_token: Callback for each response token.
            on_agent_update: Callback for agent status updates.
            on_tool_output: Callback for tool execution outputs.

        Returns:
            Complete response text.
        """
        response_parts: list[str] = []
        complete = asyncio.Event()

        def handle_response(payload: dict[str, Any]) -> None:
            token = payload.get("token", "")
            if token:
                response_parts.append(token)
                if on_token:
                    on_token(token)

            if payload.get("complete", False):
                complete.set()

        def handle_agent_update(payload: dict[str, Any]) -> None:
            if on_agent_update:
                on_agent_update(AgentUpdate.from_dict(payload))

        def handle_tool_output(payload: dict[str, Any]) -> None:
            if on_tool_output:
                on_tool_output(ToolOutput.from_dict(payload))

        # Register handlers
        self.on_message(MessageType.RESPONSE, handle_response)
        self.on_message(MessageType.AGENT_UPDATE, handle_agent_update)
        self.on_message(MessageType.TOOL_OUTPUT, handle_tool_output)

        try:
            await self.send(MessageType.CHAT, {"message": message})
            await asyncio.wait_for(complete.wait(), timeout=300.0)
            return "".join(response_parts)
        finally:
            self.remove_handler(MessageType.RESPONSE, handle_response)
            self.remove_handler(MessageType.AGENT_UPDATE, handle_agent_update)
            self.remove_handler(MessageType.TOOL_OUTPUT, handle_tool_output)
