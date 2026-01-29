"""
WebSocket module for AiCippy.

Provides real-time communication with the AiCippy backend
via API Gateway WebSocket.
"""

from __future__ import annotations

from aicippy.websocket.client import WebSocketClient
from aicippy.websocket.models import (
    WebSocketMessage,
    MessageType,
    AgentUpdate,
    ToolOutput,
    DiffMessage,
    ProgressMessage,
)
from aicippy.websocket.realtime import (
    RealtimeManager,
    ConnectionState,
    StreamState,
    ConnectionStatus,
    StreamBuffer,
    AgentState,
)

__all__ = [
    # Client
    "WebSocketClient",
    # Models
    "WebSocketMessage",
    "MessageType",
    "AgentUpdate",
    "ToolOutput",
    "DiffMessage",
    "ProgressMessage",
    # Realtime Manager
    "RealtimeManager",
    "ConnectionState",
    "StreamState",
    "ConnectionStatus",
    "StreamBuffer",
    "AgentState",
]
