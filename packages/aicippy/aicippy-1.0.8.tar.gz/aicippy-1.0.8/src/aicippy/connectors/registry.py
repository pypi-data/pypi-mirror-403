"""
Connector registry for managing available tool connectors.
"""

from __future__ import annotations

from typing import Any

from aicippy.connectors.base import BaseConnector, ConnectorConfig, ConnectorStatus
from aicippy.utils.logging import get_logger

logger = get_logger(__name__)


class ConnectorRegistry:
    """
    Registry for managing tool connectors.

    Provides discovery, initialization, and access to
    all available connectors.
    """

    _instance: "ConnectorRegistry | None" = None
    _connectors: dict[str, BaseConnector]

    def __new__(cls) -> "ConnectorRegistry":
        """Singleton pattern for registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connectors = {}
        return cls._instance

    def register(
        self,
        connector: BaseConnector,
        name: str | None = None,
    ) -> None:
        """
        Register a connector.

        Args:
            connector: Connector instance to register.
            name: Optional name override.
        """
        connector_name = name or connector.name
        self._connectors[connector_name] = connector
        logger.info("connector_registered", name=connector_name)

    def unregister(self, name: str) -> bool:
        """
        Unregister a connector.

        Args:
            name: Connector name.

        Returns:
            True if connector was removed, False if not found.
        """
        if name in self._connectors:
            del self._connectors[name]
            logger.info("connector_unregistered", name=name)
            return True
        return False

    def get(self, name: str) -> BaseConnector | None:
        """
        Get a connector by name.

        Args:
            name: Connector name.

        Returns:
            Connector instance or None if not found.
        """
        return self._connectors.get(name)

    def get_available(self) -> list[BaseConnector]:
        """
        Get all available connectors.

        Returns:
            List of available connector instances.
        """
        return [c for c in self._connectors.values() if c.is_available]

    def get_all(self) -> dict[str, BaseConnector]:
        """
        Get all registered connectors.

        Returns:
            Dictionary of all connectors.
        """
        return self._connectors.copy()

    def list_connectors(self) -> list[dict[str, Any]]:
        """
        List all connectors with their info.

        Returns:
            List of connector information dictionaries.
        """
        return [connector.get_info() for connector in self._connectors.values()]

    async def check_all_availability(self) -> dict[str, bool]:
        """
        Check availability of all connectors.

        Returns:
            Dictionary mapping connector names to availability.
        """
        results = {}
        for name, connector in self._connectors.items():
            try:
                results[name] = await connector.check_availability()
            except Exception as e:
                logger.warning(
                    "connector_availability_check_failed",
                    name=name,
                    error=str(e),
                )
                results[name] = False
        return results

    def enable(self, name: str) -> bool:
        """
        Enable a connector.

        Args:
            name: Connector name.

        Returns:
            True if connector was enabled, False if not found.
        """
        connector = self._connectors.get(name)
        if connector:
            connector.config.enabled = True
            connector._status = ConnectorStatus.AVAILABLE
            logger.info("connector_enabled", name=name)
            return True
        return False

    def disable(self, name: str) -> bool:
        """
        Disable a connector.

        Args:
            name: Connector name.

        Returns:
            True if connector was disabled, False if not found.
        """
        connector = self._connectors.get(name)
        if connector:
            connector.config.enabled = False
            connector._status = ConnectorStatus.DISABLED
            logger.info("connector_disabled", name=name)
            return True
        return False

    @classmethod
    def initialize_default_connectors(cls) -> "ConnectorRegistry":
        """
        Initialize registry with default connectors.

        Returns:
            Initialized registry instance.
        """
        from aicippy.connectors.aws import AWSConnector
        from aicippy.connectors.github import GitHubConnector
        from aicippy.connectors.firebase import FirebaseConnector
        from aicippy.connectors.shell import ShellConnector

        registry = cls()

        # Register default connectors
        registry.register(AWSConnector())
        registry.register(GitHubConnector())
        registry.register(FirebaseConnector())
        registry.register(ShellConnector())

        logger.info(
            "default_connectors_initialized",
            count=len(registry._connectors),
        )

        return registry
