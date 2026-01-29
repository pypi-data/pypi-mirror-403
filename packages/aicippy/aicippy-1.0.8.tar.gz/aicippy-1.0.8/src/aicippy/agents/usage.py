"""
Token usage tracking for AiCippy.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentUsageStat:
    """Usage statistics for a single agent."""

    agent_type: str
    model: str
    total_tokens: int


@dataclass
class UsageStats:
    """Token usage statistics."""

    session_input: int = 0
    session_output: int = 0
    today_input: int = 0
    today_output: int = 0
    month_input: int = 0
    month_output: int = 0
    per_agent: list[AgentUsageStat] = field(default_factory=list)

    @property
    def session_total(self) -> int:
        """Total session tokens."""
        return self.session_input + self.session_output

    @property
    def today_total(self) -> int:
        """Total tokens today."""
        return self.today_input + self.today_output

    @property
    def month_total(self) -> int:
        """Total tokens this month."""
        return self.month_input + self.month_output


async def get_usage_stats() -> UsageStats:
    """
    Get token usage statistics.

    Returns:
        UsageStats with current usage data.
    """
    # This would normally fetch from DynamoDB
    # For now, return placeholder data
    return UsageStats(
        session_input=0,
        session_output=0,
        today_input=0,
        today_output=0,
        month_input=0,
        month_output=0,
        per_agent=[],
    )
