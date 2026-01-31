"""Tests for UploadStrategyRegistry."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock

import pytest

from synapse_sdk.clients.backend.bulk_upload.base import BulkUploadStrategy
from synapse_sdk.clients.backend.bulk_upload.registry import (
    UploadStrategyRegistry,
    get_strategy_registry,
)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig
    from synapse_sdk.clients.backend.bulk_upload.models import ConfirmUploadResponse


class MockStrategy(BulkUploadStrategy):
    """Mock strategy for testing."""

    strategy_name = 'mock'
    supported_providers = frozenset({'mock_provider', 's3'})

    def supports_storage(self, storage: dict[str, Any]) -> bool:
        provider = storage.get('provider', '').lower()
        return provider in self.supported_providers

    def upload_files(
        self,
        file_paths: list[Path],
        config: 'BulkUploadConfig',
        *,
        on_progress=None,
    ) -> 'ConfirmUploadResponse':
        raise NotImplementedError


class AnotherMockStrategy(BulkUploadStrategy):
    """Another mock strategy for testing."""

    strategy_name = 'another_mock'
    supported_providers = frozenset({'gcs', 'azure'})

    def supports_storage(self, storage: dict[str, Any]) -> bool:
        provider = storage.get('provider', '').lower()
        return provider in self.supported_providers

    def upload_files(
        self,
        file_paths: list[Path],
        config: 'BulkUploadConfig',
        *,
        on_progress=None,
    ) -> 'ConfirmUploadResponse':
        raise NotImplementedError


class NoNameStrategy(BulkUploadStrategy):
    """Strategy without strategy_name for testing."""

    supported_providers = frozenset()

    def supports_storage(self, storage: dict[str, Any]) -> bool:
        return False

    def upload_files(
        self,
        file_paths: list[Path],
        config: 'BulkUploadConfig',
        *,
        on_progress=None,
    ) -> 'ConfirmUploadResponse':
        raise NotImplementedError


@pytest.fixture
def fresh_registry() -> UploadStrategyRegistry:
    """Create a fresh registry instance for testing."""
    # Reset singleton
    UploadStrategyRegistry._instance = None
    registry = UploadStrategyRegistry()
    registry.clear()
    return registry


class TestUploadStrategyRegistry:
    """Tests for UploadStrategyRegistry."""

    def test_singleton_pattern(self) -> None:
        """Test registry uses singleton pattern."""
        UploadStrategyRegistry._instance = None
        registry1 = UploadStrategyRegistry()
        registry2 = UploadStrategyRegistry()

        assert registry1 is registry2

    def test_register_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test registering a strategy."""
        fresh_registry.register(MockStrategy)

        assert 'mock' in fresh_registry.list_strategies()
        assert fresh_registry.get('mock') is MockStrategy

    def test_register_strategy_without_name_raises(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test registering a strategy without strategy_name raises ValueError."""
        with pytest.raises(ValueError, match='must define strategy_name'):
            fresh_registry.register(NoNameStrategy)

    def test_unregister_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test unregistering a strategy."""
        fresh_registry.register(MockStrategy)

        result = fresh_registry.unregister('mock')

        assert result is True
        assert 'mock' not in fresh_registry.list_strategies()

    def test_unregister_nonexistent_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test unregistering a nonexistent strategy returns False."""
        result = fresh_registry.unregister('nonexistent')

        assert result is False

    def test_get_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test getting a strategy by name."""
        fresh_registry.register(MockStrategy)

        cls = fresh_registry.get('mock')

        assert cls is MockStrategy

    def test_get_nonexistent_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test getting a nonexistent strategy returns None."""
        cls = fresh_registry.get('nonexistent')

        assert cls is None

    def test_get_or_raise_strategy(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test get_or_raise returns strategy class."""
        fresh_registry.register(MockStrategy)

        cls = fresh_registry.get_or_raise('mock')

        assert cls is MockStrategy

    def test_get_or_raise_nonexistent_raises(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test get_or_raise raises for nonexistent strategy."""
        with pytest.raises(ValueError, match="Strategy 'nonexistent' not found"):
            fresh_registry.get_or_raise('nonexistent')

    def test_create_strategy_instance(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test creating a strategy instance."""
        fresh_registry.register(MockStrategy)
        mock_client = MagicMock()

        strategy = fresh_registry.create('mock', mock_client)

        assert isinstance(strategy, MockStrategy)
        assert strategy.client is mock_client

    def test_select_for_storage(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test selecting strategy by storage provider."""
        fresh_registry.register(MockStrategy)
        fresh_registry.register(AnotherMockStrategy)

        # MockStrategy supports s3
        storage = {'provider': 's3'}
        cls = fresh_registry.select_for_storage(storage)
        assert cls is MockStrategy

        # AnotherMockStrategy supports gcs
        storage = {'provider': 'gcs'}
        cls = fresh_registry.select_for_storage(storage)
        assert cls is AnotherMockStrategy

    def test_select_for_storage_with_preferred(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test selecting strategy with preferred option."""
        fresh_registry.register(MockStrategy)
        fresh_registry.register(AnotherMockStrategy)

        # Both strategies support different providers, but s3 is in MockStrategy
        storage = {'provider': 's3'}
        cls = fresh_registry.select_for_storage(storage, preferred='mock')
        assert cls is MockStrategy

    def test_select_for_storage_no_match(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test selecting strategy for unsupported provider returns None."""
        fresh_registry.register(MockStrategy)

        storage = {'provider': 'unsupported_provider'}
        cls = fresh_registry.select_for_storage(storage)

        assert cls is None

    def test_select_for_storage_or_raise(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test select_for_storage_or_raise returns strategy class."""
        fresh_registry.register(MockStrategy)

        storage = {'provider': 's3'}
        cls = fresh_registry.select_for_storage_or_raise(storage)

        assert cls is MockStrategy

    def test_select_for_storage_or_raise_no_match_raises(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test select_for_storage_or_raise raises for unsupported provider."""
        fresh_registry.register(MockStrategy)

        storage = {'provider': 'unsupported'}
        with pytest.raises(ValueError, match='No strategy supports provider'):
            fresh_registry.select_for_storage_or_raise(storage)

    def test_list_strategies(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test listing all registered strategy names."""
        fresh_registry.register(MockStrategy)
        fresh_registry.register(AnotherMockStrategy)

        names = fresh_registry.list_strategies()

        assert set(names) == {'mock', 'another_mock'}

    def test_list_strategy_classes(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test listing all registered strategy classes."""
        fresh_registry.register(MockStrategy)
        fresh_registry.register(AnotherMockStrategy)

        classes = fresh_registry.list_strategy_classes()

        assert set(classes) == {MockStrategy, AnotherMockStrategy}

    def test_clear(self, fresh_registry: UploadStrategyRegistry) -> None:
        """Test clearing all registered strategies."""
        fresh_registry.register(MockStrategy)
        fresh_registry.register(AnotherMockStrategy)

        fresh_registry.clear()

        assert fresh_registry.list_strategies() == []


class TestGetStrategyRegistry:
    """Tests for get_strategy_registry function."""

    def test_returns_registry_instance(self) -> None:
        """Test get_strategy_registry returns a registry instance."""
        # Clear cache for clean test
        get_strategy_registry.cache_clear()
        UploadStrategyRegistry._instance = None

        registry = get_strategy_registry()

        assert isinstance(registry, UploadStrategyRegistry)

    def test_returns_same_instance(self) -> None:
        """Test get_strategy_registry returns the same instance."""
        get_strategy_registry.cache_clear()
        UploadStrategyRegistry._instance = None

        registry1 = get_strategy_registry()
        registry2 = get_strategy_registry()

        assert registry1 is registry2

    def test_default_strategies_registered(self) -> None:
        """Test that default strategies are registered on module load."""
        get_strategy_registry.cache_clear()
        UploadStrategyRegistry._instance = None

        # Re-import to trigger _register_default_strategies
        from synapse_sdk.clients.backend.bulk_upload import registry as reg_module

        # Force re-registration
        reg_module._register_default_strategies()

        registry = get_strategy_registry()
        assert 'presigned' in registry.list_strategies()
