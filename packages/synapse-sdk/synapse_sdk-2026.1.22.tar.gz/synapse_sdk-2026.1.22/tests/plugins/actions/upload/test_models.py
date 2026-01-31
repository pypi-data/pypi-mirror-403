"""Tests for upload models."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from synapse_sdk.plugins.actions.upload import (
    AssetConfig,
    ExcelSecurityConfig,
    UploadParams,
    ValidationErrorCode,
)


class TestAssetConfig:
    """Test AssetConfig model."""

    def test_basic_creation(self):
        """Test basic AssetConfig creation."""
        config = AssetConfig(path='/sensors/camera')

        assert config.path == '/sensors/camera'
        assert config.is_recursive is True  # default

    def test_with_is_recursive_false(self):
        """Test AssetConfig with is_recursive=False."""
        config = AssetConfig(path='/sensors/lidar', is_recursive=False)

        assert config.path == '/sensors/lidar'
        assert config.is_recursive is False

    def test_path_is_required(self):
        """Test that path is required."""
        with pytest.raises(ValidationError) as exc_info:
            AssetConfig()

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('path',) for e in errors)

    def test_model_dump(self):
        """Test model serialization."""
        config = AssetConfig(path='/data/images', is_recursive=True)
        data = config.model_dump()

        assert data == {'path': '/data/images', 'is_recursive': True}


class TestExcelSecurityConfig:
    """Test ExcelSecurityConfig model."""

    def test_default_values(self):
        """Test ExcelSecurityConfig default values."""
        config = ExcelSecurityConfig()

        assert config.max_file_size_mb == 10
        assert config.max_rows == 100000
        assert config.max_columns == 50
        assert config.max_memory_usage_mb == 30
        assert config.max_filename_length == 255
        assert config.max_column_name_length == 100
        assert config.max_metadata_value_length == 1000
        assert config.validation_check_interval == 1000

    def test_custom_values(self):
        """Test ExcelSecurityConfig with custom values."""
        config = ExcelSecurityConfig(
            max_file_size_mb=50,
            max_rows=50000,
            max_columns=100,
        )

        assert config.max_file_size_mb == 50
        assert config.max_rows == 50000
        assert config.max_columns == 100

    def test_max_file_size_bytes_property(self):
        """Test max_file_size_bytes calculated property."""
        config = ExcelSecurityConfig(max_file_size_mb=10)

        assert config.max_file_size_bytes == 10 * 1024 * 1024

    def test_max_memory_usage_bytes_property(self):
        """Test max_memory_usage_bytes calculated property."""
        config = ExcelSecurityConfig(max_memory_usage_mb=30)

        assert config.max_memory_usage_bytes == 30 * 1024 * 1024

    def test_from_action_config(self):
        """Test creating from action config dict."""
        action_config = {
            'excel_config': {
                'max_file_size_mb': 25,
                'max_rows': 10000,
            }
        }

        config = ExcelSecurityConfig.from_action_config(action_config)

        assert config.max_file_size_mb == 25
        assert config.max_rows == 10000

    def test_from_action_config_empty(self):
        """Test creating from empty action config returns defaults."""
        config = ExcelSecurityConfig.from_action_config(None)

        assert config.max_file_size_mb == 10  # default

    def test_resource_limits_validation(self):
        """Test that extreme resource limits are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ExcelSecurityConfig(
                max_rows=100000,
                max_columns=16384,  # Would allow 1.6 billion cells
            )

        assert 'too many cells' in str(exc_info.value).lower()

    def test_min_values(self):
        """Test minimum value constraints."""
        with pytest.raises(ValidationError):
            ExcelSecurityConfig(max_file_size_mb=0)

    def test_max_values(self):
        """Test maximum value constraints."""
        with pytest.raises(ValidationError):
            ExcelSecurityConfig(max_file_size_mb=10000)


class TestUploadParamsBasic:
    """Test UploadParams basic functionality without validation context."""

    def test_name_is_required(self):
        """Test that name is required."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams(
                storage=1,
                data_collection=1,
                path='/data',
            )

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('name',) for e in errors)

    def test_name_cannot_be_blank(self):
        """Test that name cannot be blank."""
        with pytest.raises(ValidationError):
            UploadParams(
                name='   ',  # blank
                storage=1,
                data_collection=1,
                path='/data',
            )

    def test_storage_is_required(self):
        """Test that storage is required."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams(
                name='Test',
                data_collection=1,
                path='/data',
            )

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('storage',) for e in errors)

    def test_data_collection_is_required(self):
        """Test that data_collection is required."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams(
                name='Test',
                storage=1,
                path='/data',
            )

        errors = exc_info.value.errors()
        assert any(e['loc'] == ('data_collection',) for e in errors)


class TestUploadParamsPathModes:
    """Test UploadParams single-path and multi-path mode validation."""

    @pytest.fixture
    def mock_action(self):
        """Create mock action with client."""
        action = MagicMock()
        action.client = MagicMock()
        action.client.get_storage.return_value = {'id': 1}
        action.client.get_data_collection.return_value = {'id': 1}
        action.client.get_project.return_value = {'id': 1}
        return action

    @pytest.fixture
    def validation_context(self, mock_action):
        """Validation context with mocked action."""
        return {'action': mock_action}

    def test_single_path_mode_requires_path(self, validation_context):
        """Test that single path mode requires path parameter."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate(
                {
                    'name': 'Test Upload',
                    'use_single_path': True,
                    'storage': 1,
                    'data_collection': 1,
                    # path is missing
                },
                context=validation_context,
            )

        # Should have MISSING_PATH error
        assert ValidationErrorCode.MISSING_PATH.value in str(exc_info.value)

    def test_single_path_mode_with_path(self, validation_context):
        """Test single path mode with path succeeds."""
        params = UploadParams.model_validate(
            {
                'name': 'Test Upload',
                'use_single_path': True,
                'path': '/data/images',
                'storage': 1,
                'data_collection': 1,
            },
            context=validation_context,
        )

        assert params.use_single_path is True
        assert params.path == '/data/images'

    def test_multi_path_mode_requires_assets(self, validation_context):
        """Test that multi-path mode requires assets parameter."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate(
                {
                    'name': 'Test Upload',
                    'use_single_path': False,
                    'storage': 1,
                    'data_collection': 1,
                    # assets is missing
                },
                context=validation_context,
            )

        assert ValidationErrorCode.MISSING_ASSETS.value in str(exc_info.value)

    def test_multi_path_mode_with_assets(self, validation_context):
        """Test multi-path mode with assets succeeds."""
        params = UploadParams.model_validate(
            {
                'name': 'Test Upload',
                'use_single_path': False,
                'assets': {
                    'image_1': {'path': '/camera', 'is_recursive': True},
                    'pcd_1': {'path': '/lidar', 'is_recursive': False},
                },
                'storage': 1,
                'data_collection': 1,
            },
            context=validation_context,
        )

        assert params.use_single_path is False
        assert 'image_1' in params.assets
        assert params.assets['image_1'].path == '/camera'

    def test_default_mode_is_single_path(self, validation_context):
        """Test that default mode is single path."""
        params = UploadParams.model_validate(
            {
                'name': 'Test Upload',
                'path': '/data/images',
                'storage': 1,
                'data_collection': 1,
            },
            context=validation_context,
        )

        assert params.use_single_path is True


class TestUploadParamsDefaults:
    """Test UploadParams default values."""

    @pytest.fixture
    def mock_action(self):
        """Create mock action with client."""
        action = MagicMock()
        action.client = MagicMock()
        action.client.get_storage.return_value = {'id': 1}
        action.client.get_data_collection.return_value = {'id': 1}
        return action

    def test_default_values(self, mock_action):
        """Test default values are applied correctly."""
        params = UploadParams.model_validate(
            {
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'data_collection': 1,
            },
            context={'action': mock_action},
        )

        assert params.description is None
        assert params.use_single_path is True
        assert params.is_recursive is True
        assert params.assets is None
        assert params.project is None
        assert params.excel_metadata_path is None
        assert params.max_file_size_mb == 50
        assert params.creating_data_unit_batch_size == 1
        assert params.use_async_upload is True
        assert params.extra_params is None

    def test_custom_values_override_defaults(self, mock_action):
        """Test custom values override defaults."""
        params = UploadParams.model_validate(
            {
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'data_collection': 1,
                'max_file_size_mb': 100,
                'creating_data_unit_batch_size': 50,
                'use_async_upload': False,
            },
            context={'action': mock_action},
        )

        assert params.max_file_size_mb == 100
        assert params.creating_data_unit_batch_size == 50
        assert params.use_async_upload is False


class TestUploadParamsValidation:
    """Test UploadParams field validators."""

    def test_storage_validation_requires_context(self):
        """Test storage validation requires context."""
        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate({
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'data_collection': 1,
            })

        assert ValidationErrorCode.MISSING_CONTEXT.value in str(exc_info.value)

    def test_storage_not_found_error(self):
        """Test error when storage doesn't exist."""
        mock_action = MagicMock()
        mock_action.client = MagicMock()
        mock_action.client.get_storage.side_effect = Exception('Not found')

        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate(
                {
                    'name': 'Test',
                    'path': '/data',
                    'storage': 999,
                    'data_collection': 1,
                },
                context={'action': mock_action},
            )

        assert ValidationErrorCode.STORAGE_NOT_FOUND.value in str(exc_info.value)

    def test_data_collection_not_found_error(self):
        """Test error when data collection doesn't exist."""
        mock_action = MagicMock()
        mock_action.client = MagicMock()
        mock_action.client.get_storage.return_value = {'id': 1}
        mock_action.client.get_data_collection.side_effect = Exception('Not found')

        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate(
                {
                    'name': 'Test',
                    'path': '/data',
                    'storage': 1,
                    'data_collection': 999,
                },
                context={'action': mock_action},
            )

        assert ValidationErrorCode.DATA_COLLECTION_NOT_FOUND.value in str(exc_info.value)

    def test_project_validation_optional(self):
        """Test project validation is optional (None allowed)."""
        mock_action = MagicMock()
        mock_action.client = MagicMock()
        mock_action.client.get_storage.return_value = {'id': 1}
        mock_action.client.get_data_collection.return_value = {'id': 1}

        params = UploadParams.model_validate(
            {
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'data_collection': 1,
                'project': None,
            },
            context={'action': mock_action},
        )

        assert params.project is None

    def test_project_not_found_error(self):
        """Test error when project doesn't exist."""
        mock_action = MagicMock()
        mock_action.client = MagicMock()
        mock_action.client.get_storage.return_value = {'id': 1}
        mock_action.client.get_data_collection.return_value = {'id': 1}
        mock_action.client.get_project.side_effect = Exception('Not found')

        with pytest.raises(ValidationError) as exc_info:
            UploadParams.model_validate(
                {
                    'name': 'Test',
                    'path': '/data',
                    'storage': 1,
                    'data_collection': 1,
                    'project': 999,
                },
                context={'action': mock_action},
            )

        assert ValidationErrorCode.PROJECT_NOT_FOUND.value in str(exc_info.value)
