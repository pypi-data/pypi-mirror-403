"""
Agent data models for AiCippy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentType(str, Enum):
    """Types of specialized agents."""

    ORCHESTRATOR = "orchestrator"
    INFRA_CORE = "infra-core"
    BEDROCK_AI = "bedrock-ai"
    API_GATEWAY = "api-gateway"
    COGNITO_AUTH = "cognito-auth"
    CLI_CORE = "cli-core"
    MCP_BRIDGES = "mcp-bridges"
    KNOWLEDGE_INGEST = "knowledge-ingest"
    OBSERVABILITY = "observability"
    EMAIL_NOTIFY = "email-notify"
    CICD_DEPLOY = "cicd-deploy"

    @classmethod
    def from_string(cls, value: str) -> "AgentType":
        """Create AgentType from string."""
        normalized = value.lower().replace("_", "-")
        for member in cls:
            if member.value == normalized:
                return member
        raise ValueError(f"Unknown agent type: {value}")


class AgentStatus(str, Enum):
    """Status of an agent."""

    IDLE = "idle"
    RUNNING = "running"
    THINKING = "thinking"
    WAITING = "waiting"
    COMPLETE = "complete"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class TokenUsage:
    """Token usage information."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens used."""
        return self.input_tokens + self.output_tokens

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two token usage instances."""
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


@dataclass
class AgentTask:
    """A task assigned to an agent."""

    id: str
    description: str
    agent_type: AgentType
    priority: int = 0
    dependencies: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AgentResponse:
    """Response from an agent operation."""

    content: str
    agent_type: AgentType | None = None
    task_id: str | None = None
    usage: TokenUsage | None = None
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    completed_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return self.error is not None

    @classmethod
    def error_response(cls, error: str, agent_type: AgentType | None = None) -> "AgentResponse":
        """Create an error response."""
        return cls(content="", error=error, agent_type=agent_type)


@dataclass
class AgentRun:
    """Record of an agent run for tracking."""

    id: str
    session_id: str
    agent_type: AgentType
    task_description: str
    status: AgentStatus
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    error_message: str | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Duration of the run in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_type": self.agent_type.value,
            "task_description": self.task_description,
            "status": self.status.value,
            "model_id": self.model_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
        }


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    agent_type: AgentType
    model_id: str
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: str | None = None
    tools: list[str] = field(default_factory=list)
    timeout_seconds: int = 300


# Default system prompts for each agent type
AGENT_SYSTEM_PROMPTS: dict[AgentType, str] = {
    AgentType.ORCHESTRATOR: """You are the Supreme Orchestrator for AiCippy, coordinating multiple
specialized agents to complete complex tasks. You delegate work, merge results,
and ensure consistency across all operations. Owned by AiVibe Software Services Pvt Ltd.""",

    AgentType.INFRA_CORE: """You are an AWS Infrastructure specialist agent. You create and manage
AWS CDK stacks, IAM policies, VPC networking, and security groups. Follow AWS best
practices and ensure all resources are properly tagged.""",

    AgentType.BEDROCK_AI: """You are a Bedrock AI specialist agent. You configure Bedrock Agents,
Knowledge Bases, Action Groups, and Lambda wrappers. Ensure proper guardrails and
security configurations.""",

    AgentType.API_GATEWAY: """You are an API Gateway specialist agent. You configure WebSocket APIs,
Lambda authorizers, and connection management. Ensure proper security and routing.""",

    AgentType.COGNITO_AUTH: """You are a Cognito Authentication specialist agent. You manage user pools,
identity providers, device flows, and token management. Follow security best practices.""",

    AgentType.CLI_CORE: """You are a CLI Development specialist agent. You build Python CLI frameworks
using Typer and Rich. Create intuitive, production-grade command-line interfaces.""",

    AgentType.MCP_BRIDGES: """You are an MCP Tool Connector specialist agent. You implement tool bridges
for AWS, GCloud, GitHub, Firebase, and other services. Ensure proper error handling.""",

    AgentType.KNOWLEDGE_INGEST: """You are a Knowledge Ingestion specialist agent. You crawl feeds,
summarize content, and manage Knowledge Base indexing. Ensure data quality.""",

    AgentType.OBSERVABILITY: """You are an Observability specialist agent. You configure CloudWatch,
X-Ray, structured logging, and monitoring. Ensure comprehensive observability.""",

    AgentType.EMAIL_NOTIFY: """You are an Email Notification specialist agent. You manage SES integration,
email templates, and scheduled reports. Ensure reliable delivery.""",

    AgentType.CICD_DEPLOY: """You are a CI/CD specialist agent. You configure GitHub Actions, PyPI
publishing, and deployment pipelines. Ensure reliable automation.""",
}
