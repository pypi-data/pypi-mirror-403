"""Upload strategy registry for dynamic strategy discovery.

Provides centralized registration and lookup for bulk upload strategies,
enabling easy addition of new upload methods without modifying the mixin.

Example:
    >>> from synapse_sdk.clients.backend.bulk_upload.registry import get_strategy_registry
    >>>
    >>> registry = get_strategy_registry()
    >>> strategy_cls = registry.get('presigned')
    >>> strategy = strategy_cls(client)
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.clients.backend.bulk_upload.base import BulkUploadStrategy
    from synapse_sdk.clients.protocols import ClientProtocol


class UploadStrategyRegistry:
    """Registry for bulk upload strategy classes.

    Manages strategy registration and provides lookup methods for
    strategy selection based on name or storage provider.

    This registry holds strategy *classes*, not instances. Strategies
    are instantiated with a client when needed.

    Example:
        >>> from synapse_sdk.clients.backend.bulk_upload.strategies import PresignedUploadStrategy
        >>>
        >>> registry = UploadStrategyRegistry()
        >>> registry.register(PresignedUploadStrategy)
        >>>
        >>> # Get by name
        >>> cls = registry.get('presigned')
        >>> strategy = cls(client)
        >>>
        >>> # Auto-select by storage
        >>> cls = registry.select_for_storage(storage_config)
    """

    _instance: UploadStrategyRegistry | None = None

    def __new__(cls) -> UploadStrategyRegistry:
        """Singleton pattern for global registry access."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """Initialize the registry (only runs once due to singleton)."""
        if self._initialized:
            return

        self._strategies: dict[str, type[BulkUploadStrategy]] = {}
        self._initialized = True

    def register(self, strategy_cls: type['BulkUploadStrategy']) -> None:
        """Register a strategy class.

        The strategy class must have a `strategy_name` class attribute.

        Args:
            strategy_cls: Strategy class to register.

        Raises:
            ValueError: If strategy_name is not defined.

        Example:
            >>> registry.register(PresignedUploadStrategy)
        """
        name = getattr(strategy_cls, 'strategy_name', None)
        if not name:
            msg = f'{strategy_cls.__name__} must define strategy_name class attribute'
            raise ValueError(msg)

        self._strategies[name] = strategy_cls

    def unregister(self, name: str) -> bool:
        """Unregister a strategy by name.

        Args:
            name: Strategy name to remove.

        Returns:
            True if strategy was removed, False if not found.
        """
        if name in self._strategies:
            del self._strategies[name]
            return True
        return False

    def get(self, name: str) -> type['BulkUploadStrategy'] | None:
        """Get a strategy class by name.

        Args:
            name: Strategy name (e.g., 'presigned').

        Returns:
            Strategy class if found, None otherwise.
        """
        return self._strategies.get(name)

    def get_or_raise(self, name: str) -> type['BulkUploadStrategy']:
        """Get a strategy class by name, raising if not found.

        Args:
            name: Strategy name.

        Returns:
            Strategy class.

        Raises:
            ValueError: If strategy not found.
        """
        cls = self.get(name)
        if cls is None:
            available = list(self._strategies.keys())
            msg = f"Strategy '{name}' not found. Available: {available}"
            raise ValueError(msg)
        return cls

    def create(
        self,
        name: str,
        client: 'ClientProtocol',
    ) -> 'BulkUploadStrategy':
        """Create a strategy instance by name.

        Convenience method that gets the class and instantiates it.

        Args:
            name: Strategy name.
            client: Client for API calls.

        Returns:
            Strategy instance.

        Raises:
            ValueError: If strategy not found.
        """
        cls = self.get_or_raise(name)
        return cls(client)

    def select_for_storage(
        self,
        storage: dict[str, Any],
        preferred: str | None = None,
    ) -> type['BulkUploadStrategy'] | None:
        """Select a strategy class that supports the given storage.

        Args:
            storage: Storage configuration with 'provider' key.
            preferred: Preferred strategy name (checked first).

        Returns:
            Strategy class if found, None if no strategy supports the storage.
        """
        provider = storage.get('provider', '').lower()

        # Try preferred strategy first
        if preferred:
            cls = self.get(preferred)
            if cls and self._supports_provider(cls, provider):
                return cls

        # Auto-select based on provider support
        for cls in self._strategies.values():
            if self._supports_provider(cls, provider):
                return cls

        return None

    def select_for_storage_or_raise(
        self,
        storage: dict[str, Any],
        preferred: str | None = None,
    ) -> type['BulkUploadStrategy']:
        """Select a strategy class, raising if none found.

        Args:
            storage: Storage configuration.
            preferred: Preferred strategy name.

        Returns:
            Strategy class.

        Raises:
            ValueError: If no strategy supports the storage provider.
        """
        cls = self.select_for_storage(storage, preferred)
        if cls is None:
            provider = storage.get('provider', 'unknown')
            available = list(self._strategies.keys())
            msg = f"No strategy supports provider '{provider}'. Available strategies: {available}"
            raise ValueError(msg)
        return cls

    @staticmethod
    def _supports_provider(cls: type['BulkUploadStrategy'], provider: str) -> bool:
        """Check if a strategy class supports a provider.

        Args:
            cls: Strategy class.
            provider: Provider name (lowercase).

        Returns:
            True if supported.
        """
        supported = getattr(cls, 'supported_providers', frozenset())
        return provider in supported

    def list_strategies(self) -> list[str]:
        """List all registered strategy names.

        Returns:
            List of strategy names.
        """
        return list(self._strategies.keys())

    def list_strategy_classes(self) -> list[type['BulkUploadStrategy']]:
        """List all registered strategy classes.

        Returns:
            List of strategy classes.
        """
        return list(self._strategies.values())

    def clear(self) -> None:
        """Clear all registered strategies.

        Useful for testing.
        """
        self._strategies.clear()


@functools.lru_cache(maxsize=1)
def get_strategy_registry() -> UploadStrategyRegistry:
    """Get the global UploadStrategyRegistry instance.

    Uses LRU cache to ensure singleton behavior.

    Returns:
        Global UploadStrategyRegistry instance.

    Example:
        >>> from synapse_sdk.clients.backend.bulk_upload.registry import get_strategy_registry
        >>> registry = get_strategy_registry()
        >>> registry.register(PresignedUploadStrategy)
    """
    return UploadStrategyRegistry()


def _register_default_strategies() -> None:
    """Register built-in strategies.

    Called during module initialization to ensure default strategies
    are always available.
    """
    from synapse_sdk.clients.backend.bulk_upload.strategies.presigned import (
        PresignedUploadStrategy,
    )

    registry = get_strategy_registry()
    registry.register(PresignedUploadStrategy)


# Auto-register built-in strategies on module load
_register_default_strategies()


__all__ = [
    'UploadStrategyRegistry',
    'get_strategy_registry',
]
