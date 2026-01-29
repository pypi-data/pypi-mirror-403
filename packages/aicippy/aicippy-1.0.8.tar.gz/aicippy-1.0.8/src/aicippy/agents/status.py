"""
Agent status tracking for AiCippy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentInfo:
    """Information about a single agent."""

    id: str
    type: str
    status: str
    progress: int
    message: str = ""


@dataclass
class StatusInfo:
    """Overall status information."""

    session_id: str | None = None
    connected: bool = False
    active_agents: int = 0
    total_tokens: int = 0
    agents: list[AgentInfo] = field(default_factory=list)


async def get_agent_status() -> StatusInfo:
    """
    Get current agent status information.

    Returns:
        StatusInfo with current session and agent state.
    """
    # This would normally fetch from the active session
    # For now, return placeholder data
    return StatusInfo(
        session_id=None,
        connected=False,
        active_agents=0,
        total_tokens=0,
        agents=[],
    )
