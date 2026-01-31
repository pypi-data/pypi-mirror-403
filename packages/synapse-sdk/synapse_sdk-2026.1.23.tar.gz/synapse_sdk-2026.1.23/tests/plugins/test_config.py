"""Tests for plugins/config.py module."""

import pytest
from pydantic import ValidationError

from synapse_sdk.plugins.config import PluginConfig
from synapse_sdk.plugins.enums import DataType, PluginCategory


class TestPluginConfigValidation:
    """Tests for PluginConfig validation."""

    def test_neural_net_requires_data_type(self):
        """Neural net plugins must have data_type set."""
        with pytest.raises(ValidationError) as exc_info:
            PluginConfig(
                name='Test Plugin',
                code='test-plugin',
                category=PluginCategory.NEURAL_NET,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert 'data_type is required for neural_net plugins' in str(errors[0]['msg'])

    def test_neural_net_with_data_type_succeeds(self):
        """Neural net plugins with data_type should validate successfully."""
        config = PluginConfig(
            name='Test Plugin',
            code='test-plugin',
            category=PluginCategory.NEURAL_NET,
            data_type=DataType.IMAGE,
        )

        assert config.category == PluginCategory.NEURAL_NET
        assert config.data_type == DataType.IMAGE

    def test_other_categories_dont_require_data_type(self):
        """Non-neural_net plugins don't require data_type."""
        # Test custom category (default)
        config = PluginConfig(
            name='Test Plugin',
            code='test-plugin',
        )
        assert config.category == PluginCategory.CUSTOM
        assert config.data_type is None

        # Test export category
        config = PluginConfig(
            name='Export Plugin',
            code='export-plugin',
            category=PluginCategory.EXPORT,
        )
        assert config.category == PluginCategory.EXPORT
        assert config.data_type is None

        # Test upload category
        config = PluginConfig(
            name='Upload Plugin',
            code='upload-plugin',
            category=PluginCategory.UPLOAD,
        )
        assert config.category == PluginCategory.UPLOAD
        assert config.data_type is None

    def test_all_data_types_valid_for_neural_net(self):
        """All DataType values should work for neural_net plugins."""
        for data_type in DataType:
            config = PluginConfig(
                name='Test Plugin',
                code='test-plugin',
                category=PluginCategory.NEURAL_NET,
                data_type=data_type,
            )
            assert config.data_type == data_type
