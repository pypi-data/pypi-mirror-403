"""
WebSocket message models for AiCippy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageType(str, Enum):
    """Types of WebSocket messages."""

    # Client -> Server
    AUTHENTICATE = "authenticate"
    CHAT = "chat"
    TASK = "task"
    COMMAND = "command"
    PING = "ping"

    # Server -> Client
    AUTHENTICATED = "authenticated"
    RESPONSE = "response"
    AGENT_UPDATE = "agent_update"
    TOOL_OUTPUT = "tool_output"
    DIFF = "diff"
    PROGRESS = "progress"
    ERROR = "error"
    PONG = "pong"


@dataclass
class WebSocketMessage:
    """Base WebSocket message structure."""

    type: MessageType
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WebSocketMessage":
        """Create from dictionary."""
        return cls(
            type=MessageType(data["type"]),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id"),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if "timestamp" in data
            else datetime.utcnow(),
        )


@dataclass
class AgentUpdate:
    """Agent status update message."""

    agent_id: str
    agent_type: str
    status: str
    progress: int
    message: str = ""
    tokens_used: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status,
            "progress": self.progress,
            "message": self.message,
            "tokens_used": self.tokens_used,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AgentUpdate":
        """Create from dictionary."""
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            status=data["status"],
            progress=data["progress"],
            message=data.get("message", ""),
            tokens_used=data.get("tokens_used", 0),
        )


@dataclass
class ToolOutput:
    """Tool execution output message."""

    tool_name: str
    output: str
    success: bool
    execution_time_ms: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "output": self.output,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolOutput":
        """Create from dictionary."""
        return cls(
            tool_name=data["tool_name"],
            output=data["output"],
            success=data["success"],
            execution_time_ms=data.get("execution_time_ms", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class DiffMessage:
    """File diff message for code changes."""

    file_path: str
    old_content: str
    new_content: str
    diff_type: str = "unified"  # unified, side_by_side
    language: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "old_content": self.old_content,
            "new_content": self.new_content,
            "diff_type": self.diff_type,
            "language": self.language,
        }


@dataclass
class ProgressMessage:
    """Progress update message."""

    task_id: str
    current: int
    total: int
    message: str = ""
    stage: str | None = None

    @property
    def percentage(self) -> float:
        """Calculate percentage complete."""
        if self.total == 0:
            return 0.0
        return (self.current / self.total) * 100

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "current": self.current,
            "total": self.total,
            "message": self.message,
            "stage": self.stage,
            "percentage": self.percentage,
        }
