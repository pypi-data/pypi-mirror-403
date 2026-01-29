"""
MCP-style tool connectors for AiCippy.

Provides bridges to external tools and services including:
- AWS CLI
- Google Cloud CLI
- GitHub CLI
- Firebase CLI
- Figma API
- Google Drive API
- Gmail API
- Razorpay API
- PayPal API
- Stripe CLI
- And more...
"""

from __future__ import annotations

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ToolResult
from aicippy.connectors.registry import ConnectorRegistry
from aicippy.connectors.aws import AWSConnector
from aicippy.connectors.github import GitHubConnector
from aicippy.connectors.firebase import FirebaseConnector
from aicippy.connectors.shell import ShellConnector

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ToolResult",
    "ConnectorRegistry",
    "AWSConnector",
    "GitHubConnector",
    "FirebaseConnector",
    "ShellConnector",
]
