"""
Secure credential storage using OS keychain.

Uses the keyring library to store tokens securely in:
- macOS: Keychain
- Windows: Credential Manager
- Linux: Secret Service (GNOME Keyring, KWallet)
"""

from __future__ import annotations

import json
from typing import Any

import keyring
from keyring.errors import KeyringError

from aicippy.auth.models import TokenInfo
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)

# Service name for keyring
SERVICE_NAME = "aicippy"

# Key names
KEY_TOKENS = "tokens"
KEY_USER_ID = "user_id"
KEY_USER_EMAIL = "user_email"


class KeychainStorage:
    """
    Secure storage for authentication credentials.

    Uses the OS-native keychain for secure token storage.
    NEVER logs or prints sensitive values.
    """

    def __init__(self, service_name: str = SERVICE_NAME) -> None:
        """
        Initialize keychain storage.

        Args:
            service_name: Service identifier for keychain entries.
        """
        self._service = service_name
        self._verify_keychain_available()

    def _verify_keychain_available(self) -> None:
        """Verify that keychain is available and working."""
        try:
            # Test keychain access
            keyring.get_keyring()
            logger.debug("keychain_available", backend=str(keyring.get_keyring()))
        except Exception as e:
            logger.warning("keychain_unavailable", error=str(e))

    def store_tokens(self, tokens: TokenInfo) -> None:
        """
        Store tokens securely in the keychain.

        Args:
            tokens: Token information to store.
        """
        try:
            token_data = json.dumps(tokens.to_dict())
            keyring.set_password(self._service, KEY_TOKENS, token_data)
            logger.info("tokens_stored")
        except KeyringError as e:
            logger.error("token_storage_failed", error=str(e))
            raise StorageError(f"Failed to store tokens: {e}") from e

    def get_tokens(self) -> TokenInfo | None:
        """
        Retrieve tokens from the keychain.

        Returns:
            TokenInfo if found and valid, None otherwise.
        """
        try:
            token_data = keyring.get_password(self._service, KEY_TOKENS)
            if token_data:
                data = json.loads(token_data)
                return TokenInfo.from_dict(data)
            return None
        except KeyringError as e:
            logger.error("token_retrieval_failed", error=str(e))
            return None
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning("token_data_corrupted", error=str(e))
            self.clear_tokens()
            return None

    def clear_tokens(self) -> None:
        """Remove all stored tokens from the keychain."""
        try:
            keyring.delete_password(self._service, KEY_TOKENS)
            logger.info("tokens_cleared")
        except KeyringError:
            # Ignore errors when deleting non-existent entries
            pass

    def store_user_info(self, user_id: str, email: str) -> None:
        """
        Store user information in the keychain.

        Args:
            user_id: User's Cognito sub identifier.
            email: User's email address.
        """
        try:
            keyring.set_password(self._service, KEY_USER_ID, user_id)
            keyring.set_password(self._service, KEY_USER_EMAIL, email)
            logger.info("user_info_stored")
        except KeyringError as e:
            logger.error("user_info_storage_failed", error=str(e))
            raise StorageError(f"Failed to store user info: {e}") from e

    def get_user_info(self) -> tuple[str | None, str | None]:
        """
        Retrieve user information from the keychain.

        Returns:
            Tuple of (user_id, email), with None for missing values.
        """
        try:
            user_id = keyring.get_password(self._service, KEY_USER_ID)
            email = keyring.get_password(self._service, KEY_USER_EMAIL)
            return user_id, email
        except KeyringError as e:
            logger.error("user_info_retrieval_failed", error=str(e))
            return None, None

    def clear_user_info(self) -> None:
        """Remove all stored user information from the keychain."""
        try:
            keyring.delete_password(self._service, KEY_USER_ID)
            keyring.delete_password(self._service, KEY_USER_EMAIL)
            logger.info("user_info_cleared")
        except KeyringError:
            # Ignore errors when deleting non-existent entries
            pass

    def clear_all(self) -> None:
        """Remove all stored credentials from the keychain."""
        self.clear_tokens()
        self.clear_user_info()
        logger.info("all_credentials_cleared")

    def has_valid_tokens(self) -> bool:
        """
        Check if valid (non-expired) tokens exist.

        Returns:
            True if valid tokens are stored, False otherwise.
        """
        tokens = self.get_tokens()
        if tokens is None:
            return False
        return not tokens.is_expired()


class StorageError(Exception):
    """Raised when credential storage operations fail."""

    pass
