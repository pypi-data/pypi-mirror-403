"""
Configuration management for AiCippy using pydantic-settings.

All configuration is loaded from environment variables with secure defaults.
Secrets are NEVER logged or printed to console.

This module provides:
- Type-safe configuration with Pydantic v2 validators
- Environment variable loading with sensible defaults
- Path validation and automatic directory creation
- Model ID resolution with validation

Example:
    >>> from aicippy.config import get_settings
    >>> settings = get_settings()
    >>> settings.get_model_id("opus")
    'anthropic.claude-opus-4-5-20251101-v1:0'
"""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Final, Literal, Self

from pydantic import (
    AnyHttpUrl,
    EmailStr,
    Field,
    PositiveInt,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

# Type aliases for clarity
ModelName = Literal["opus", "sonnet", "llama"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["json", "console"]

# Constants
AWS_ACCOUNT_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^\d{12}$")
AWS_REGION_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z]{2}-[a-z]+-\d$")
COGNITO_POOL_ID_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[\w-]+_[\w]+$")


class Settings(BaseSettings):
    """
    AiCippy configuration settings with strict validation.

    Configuration is loaded from environment variables with AICIPPY_ prefix.
    All fields are validated at initialization to catch configuration errors early.

    Attributes:
        aws_account_id: 12-digit AWS account ID.
        aws_region: AWS region identifier (e.g., us-east-1).
        cognito_user_pool_id: Cognito User Pool ID.
        default_model: Default AI model (opus, sonnet, or llama).
        max_parallel_agents: Maximum concurrent agents (1-10).

    Example:
        >>> settings = Settings()
        >>> settings.default_model
        'opus'
    """

    model_config = SettingsConfigDict(
        env_prefix="AICIPPY_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_default=True,
        str_strip_whitespace=True,
    )

    # AWS Configuration
    aws_account_id: str = Field(
        default="936668162296",
        description="AWS Account ID for resource deployment",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="Primary AWS region",
    )
    aws_profile: str | None = Field(
        default=None,
        description="AWS CLI profile to use",
    )

    # Cognito Configuration
    cognito_user_pool_id: str = Field(
        default="us-east-1_S2Cpx3svp",
        description="Cognito User Pool ID",
    )
    cognito_client_id: str = Field(
        default="4g7n5j9ir90ju54bekqs88524k",
        description="Cognito App Client ID",
    )
    cognito_domain: str = Field(
        default="https://auth.vibekaro.ai",
        description="Cognito hosted UI domain",
    )

    # Domain Configuration
    domain: str = Field(
        default="aicippy.io",
        description="Primary domain for AiCippy",
    )
    route53_hosted_zone_id: str = Field(
        default="Z01837521OAC5AIIB7QE6",
        description="Route53 hosted zone ID for aicippy.io",
    )

    # WebSocket Configuration
    websocket_url: str = Field(
        default="wss://ws.aicippy.io",
        description="WebSocket API endpoint",
    )
    websocket_reconnect_attempts: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of reconnection attempts",
    )
    websocket_reconnect_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=30.0,
        description="Base delay between reconnection attempts in seconds",
    )

    # Email Configuration
    ses_verified_email: str = Field(
        default="noreply@aicippy.io",
        description="SES verified sender email",
    )
    admin_email: str = Field(
        default="aravind@aivibe.in",
        description="Administrator email for notifications",
    )

    # Model Configuration
    default_model: Literal["opus", "sonnet", "llama"] = Field(
        default="opus",
        description="Default AI model to use",
    )
    model_opus_id: str = Field(
        default="anthropic.claude-opus-4-5-20251101-v1:0",
        description="Claude Opus 4.5 model ID",
    )
    model_sonnet_id: str = Field(
        default="anthropic.claude-sonnet-4-5-20251101-v1:0",
        description="Claude Sonnet 4.5 model ID",
    )
    model_llama_id: str = Field(
        default="meta.llama4-maverick-17b-instruct-v1:0",
        description="Llama 4 Maverick model ID",
    )

    # Agent Configuration
    max_parallel_agents: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Maximum number of parallel agents",
    )
    agent_timeout_seconds: int = Field(
        default=300,
        ge=30,
        le=3600,
        description="Agent execution timeout in seconds",
    )

    # Session Configuration
    session_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Session time-to-live in hours",
    )

    # Local Storage Paths
    local_config_dir: Path = Field(
        default_factory=lambda: Path.home() / ".aicippy",
        description="Local configuration directory",
    )
    local_sessions_dir: Path = Field(
        default_factory=lambda: Path.home() / ".aicippy" / "sessions",
        description="Local sessions storage directory",
    )
    local_cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".aicippy" / "cache",
        description="Local cache directory",
    )

    # Logging Configuration
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["json", "console"] = Field(
        default="console",
        description="Log output format",
    )

    # Knowledge Base Configuration
    kb_sync_interval_hours: int = Field(
        default=6,
        ge=1,
        le=24,
        description="Knowledge Base sync interval in hours",
    )
    kb_retention_days: int = Field(
        default=90,
        ge=30,
        le=365,
        description="Knowledge Base data retention in days",
    )

    # Token Usage Tracking
    token_usage_report_interval_hours: int = Field(
        default=12,
        ge=1,
        le=24,
        description="Token usage report email interval in hours",
    )

    @field_validator("aws_account_id", mode="after")
    @classmethod
    def validate_aws_account_id(cls, v: str) -> str:
        """Validate AWS account ID format (12 digits)."""
        if not AWS_ACCOUNT_ID_PATTERN.match(v):
            raise ValueError(f"Invalid AWS account ID: must be 12 digits, got '{v}'")
        return v

    @field_validator("aws_region", mode="after")
    @classmethod
    def validate_aws_region(cls, v: str) -> str:
        """Validate AWS region format."""
        if not AWS_REGION_PATTERN.match(v):
            raise ValueError(f"Invalid AWS region format: '{v}'")
        return v

    @field_validator("cognito_user_pool_id", mode="after")
    @classmethod
    def validate_cognito_pool_id(cls, v: str) -> str:
        """Validate Cognito User Pool ID format."""
        if not COGNITO_POOL_ID_PATTERN.match(v):
            raise ValueError(f"Invalid Cognito User Pool ID format: '{v}'")
        return v

    @field_validator("websocket_url", mode="after")
    @classmethod
    def validate_websocket_url(cls, v: str) -> str:
        """Validate WebSocket URL uses secure protocol."""
        if not v.startswith("wss://"):
            raise ValueError("WebSocket URL must use secure protocol (wss://)")
        return v

    @field_validator("cognito_domain", mode="after")
    @classmethod
    def validate_https_url(cls, v: str) -> str:
        """Validate URL uses HTTPS."""
        if not v.startswith("https://"):
            raise ValueError("Cognito domain must use HTTPS")
        return v

    @field_validator("local_config_dir", "local_sessions_dir", "local_cache_dir", mode="after")
    @classmethod
    def ensure_dir_exists(cls, v: Path) -> Path:
        """Ensure directory exists with secure permissions."""
        v.mkdir(parents=True, exist_ok=True, mode=0o700)
        return v

    @model_validator(mode="after")
    def validate_model_configuration(self) -> Self:
        """Validate model configuration consistency."""
        # Ensure all model IDs are non-empty
        for model_name in ("opus", "sonnet", "llama"):
            model_id = getattr(self, f"model_{model_name}_id")
            if not model_id or not model_id.strip():
                raise ValueError(f"Model ID for '{model_name}' cannot be empty")
        return self

    def get_model_id(self, model_name: str | None = None) -> str:
        """
        Get the full Bedrock model ID for a given model name.

        Args:
            model_name: Model name (opus, sonnet, llama). Defaults to configured default.

        Returns:
            Full Bedrock model ID string.

        Raises:
            ValueError: If model_name is not recognized.

        Example:
            >>> settings.get_model_id("opus")
            'anthropic.claude-opus-4-5-20251101-v1:0'
        """
        model = model_name or self.default_model
        model_map: dict[str, str] = {
            "opus": self.model_opus_id,
            "sonnet": self.model_sonnet_id,
            "llama": self.model_llama_id,
        }
        if model not in model_map:
            valid_options = ", ".join(sorted(model_map.keys()))
            raise ValueError(f"Unknown model: '{model}'. Valid options: {valid_options}")
        return model_map[model]

    @property
    def s3_knowledge_bucket(self) -> str:
        """S3 bucket name for knowledge artifacts."""
        return f"aicippy-knowledge-{self.aws_account_id}-{self.aws_region}"

    @property
    def s3_logs_bucket(self) -> str:
        """S3 bucket name for logs."""
        return f"aicippy-logs-{self.aws_account_id}-{self.aws_region}"

    @property
    def s3_artifacts_bucket(self) -> str:
        """S3 bucket name for artifacts."""
        return f"aicippy-artifacts-{self.aws_account_id}-{self.aws_region}"

    @property
    def dynamodb_sessions_table(self) -> str:
        """DynamoDB table name for sessions."""
        return "aicippy-sessions"

    @property
    def dynamodb_agent_runs_table(self) -> str:
        """DynamoDB table name for agent runs."""
        return "aicippy-agent-runs"

    @property
    def dynamodb_token_usage_table(self) -> str:
        """DynamoDB table name for token usage."""
        return "aicippy-token-usage"

    @property
    def dynamodb_websocket_connections_table(self) -> str:
        """DynamoDB table name for WebSocket connections."""
        return "aicippy-websocket-connections"

    @property
    def dynamodb_knowledge_metadata_table(self) -> str:
        """DynamoDB table name for knowledge metadata."""
        return "aicippy-knowledge-metadata"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to ensure settings are loaded only once.
    Clear cache by calling get_settings.cache_clear() if needed.
    """
    return Settings()
