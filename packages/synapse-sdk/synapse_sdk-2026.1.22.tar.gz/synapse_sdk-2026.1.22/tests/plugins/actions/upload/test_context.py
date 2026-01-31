"""Tests for UploadContext."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from synapse_sdk.plugins.actions.upload import UploadContext
from synapse_sdk.plugins.context import RuntimeContext


class TestUploadContext:
    """Test UploadContext initialization and properties."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create a mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def single_path_params(self):
        """Single path mode parameters."""
        return {
            'name': 'Test Upload',
            'description': 'Test description',
            'use_single_path': True,
            'path': '/data/images',
            'is_recursive': True,
            'storage': 1,
            'data_collection': 5,
            'max_file_size_mb': 100,
            'creating_data_unit_batch_size': 10,
            'use_async_upload': True,
        }

    @pytest.fixture
    def multi_path_params(self):
        """Multi-path mode parameters."""
        return {
            'name': 'Multi Upload',
            'use_single_path': False,
            'assets': {
                'image_1': {'path': '/sensors/camera', 'is_recursive': True},
                'pcd_1': {'path': '/sensors/lidar', 'is_recursive': False},
            },
            'storage': 1,
            'data_collection': 5,
        }

    def test_init_with_params(self, mock_runtime_ctx, single_path_params):
        """Test context initialization with parameters."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.params == single_path_params
        assert context.runtime_ctx == mock_runtime_ctx

    def test_init_default_state(self, mock_runtime_ctx, single_path_params):
        """Test that context initializes with default state."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.storage is None
        assert context.data_collection is None
        assert context.project is None
        assert context.pathlib_cwd is None
        assert context.organized_files == []
        assert context.uploaded_files == []
        assert context.data_units == []
        assert context.excel_metadata is None

    def test_use_single_path_true(self, mock_runtime_ctx, single_path_params):
        """Test use_single_path property returns True for single path mode."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.use_single_path is True

    def test_use_single_path_false(self, mock_runtime_ctx, multi_path_params):
        """Test use_single_path property returns False for multi-path mode."""
        context = UploadContext(
            params=multi_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.use_single_path is False

    def test_use_single_path_default(self, mock_runtime_ctx):
        """Test use_single_path defaults to True."""
        context = UploadContext(
            params={},
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.use_single_path is True

    def test_upload_name(self, mock_runtime_ctx, single_path_params):
        """Test upload_name property returns name from params."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.upload_name == 'Test Upload'

    def test_upload_name_default(self, mock_runtime_ctx):
        """Test upload_name defaults to 'Unnamed Upload'."""
        context = UploadContext(
            params={},
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.upload_name == 'Unnamed Upload'

    def test_max_file_size_bytes(self, mock_runtime_ctx, single_path_params):
        """Test max_file_size_bytes conversion."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        # 100 MB = 100 * 1024 * 1024 bytes
        assert context.max_file_size_bytes == 100 * 1024 * 1024

    def test_max_file_size_bytes_default(self, mock_runtime_ctx):
        """Test max_file_size_bytes default value."""
        context = UploadContext(
            params={},
            runtime_ctx=mock_runtime_ctx,
        )

        # Default 50 MB
        assert context.max_file_size_bytes == 50 * 1024 * 1024

    def test_batch_size(self, mock_runtime_ctx, single_path_params):
        """Test batch_size property."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.batch_size == 10

    def test_batch_size_default(self, mock_runtime_ctx):
        """Test batch_size default value."""
        context = UploadContext(
            params={},
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.batch_size == 1

    def test_use_async_upload(self, mock_runtime_ctx, single_path_params):
        """Test use_async_upload property."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.use_async_upload is True

    def test_use_async_upload_default(self, mock_runtime_ctx):
        """Test use_async_upload default value."""
        context = UploadContext(
            params={},
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.use_async_upload is True

    def test_client_property(self, mock_runtime_ctx, single_path_params):
        """Test client property returns client from runtime context."""
        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_runtime_ctx,
        )

        assert context.client == mock_runtime_ctx.client

    def test_client_property_raises_without_client(self, single_path_params):
        """Test client property raises RuntimeError when no client."""
        mock_ctx = MagicMock(spec=RuntimeContext)
        mock_ctx.client = None

        context = UploadContext(
            params=single_path_params,
            runtime_ctx=mock_ctx,
        )

        with pytest.raises(RuntimeError, match='No client in runtime context'):
            _ = context.client


class TestUploadContextStateMutation:
    """Test UploadContext state mutation during workflow."""

    @pytest.fixture
    def context(self):
        """Create a context for testing."""
        mock_ctx = MagicMock(spec=RuntimeContext)
        mock_ctx.client = MagicMock()
        return UploadContext(
            params={'name': 'Test'},
            runtime_ctx=mock_ctx,
        )

    def test_storage_can_be_set(self, context):
        """Test storage can be set."""
        context.storage = {'id': 1, 'name': 'Test Storage'}
        assert context.storage == {'id': 1, 'name': 'Test Storage'}

    def test_pathlib_cwd_can_be_set(self, context):
        """Test pathlib_cwd can be set."""
        context.pathlib_cwd = Path('/data/images')
        assert context.pathlib_cwd == Path('/data/images')

    def test_organized_files_can_be_appended(self, context):
        """Test organized_files list can be modified."""
        file_entry = {'files': {'image_1': Path('/test.jpg')}, 'meta': {}}
        context.organized_files.append(file_entry)

        assert len(context.organized_files) == 1
        assert context.organized_files[0] == file_entry

    def test_uploaded_files_can_be_extended(self, context):
        """Test uploaded_files list can be extended."""
        files = [
            {'file_key': 'key1', 'data_file_id': 1},
            {'file_key': 'key2', 'data_file_id': 2},
        ]
        context.uploaded_files.extend(files)

        assert len(context.uploaded_files) == 2

    def test_data_units_can_be_modified(self, context):
        """Test data_units list can be modified."""
        context.data_units = [{'id': 1}, {'id': 2}]

        assert len(context.data_units) == 2

    def test_excel_metadata_can_be_set(self, context):
        """Test excel_metadata can be set."""
        metadata = {
            'file1.jpg': {'label': 'cat'},
            'file2.jpg': {'label': 'dog'},
        }
        context.excel_metadata = metadata

        assert context.excel_metadata == metadata
