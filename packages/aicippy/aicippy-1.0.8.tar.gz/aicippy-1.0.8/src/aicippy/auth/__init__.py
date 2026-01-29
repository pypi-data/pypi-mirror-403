"""
Authentication module for AiCippy.

Provides secure authentication via AWS Cognito with device flow,
token management, and OS keychain storage.
"""

from __future__ import annotations

from aicippy.auth.cognito import CognitoAuth
from aicippy.auth.keychain import KeychainStorage
from aicippy.auth.models import AuthResult, TokenInfo

__all__ = [
    "CognitoAuth",
    "KeychainStorage",
    "AuthResult",
    "TokenInfo",
]
