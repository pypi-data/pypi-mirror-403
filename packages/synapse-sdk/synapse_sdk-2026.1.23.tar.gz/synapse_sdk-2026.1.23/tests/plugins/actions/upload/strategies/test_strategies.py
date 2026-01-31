"""Tests for upload strategies."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from synapse_sdk.plugins.actions.upload import (
    DataUnitStrategy,
    FileDiscoveryStrategy,
    FlatFileDiscoveryStrategy,
    MetadataStrategy,
    RecursiveFileDiscoveryStrategy,
    UploadConfig,
    UploadStrategy,
    ValidationResult,
    ValidationStrategy,
)


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_default_is_valid(self):
        """Test default ValidationResult is valid."""
        result = ValidationResult()

        assert result.valid is True
        assert result.errors == []
        assert bool(result) is True

    def test_invalid_result(self):
        """Test invalid ValidationResult."""
        result = ValidationResult(valid=False, errors=['Error 1', 'Error 2'])

        assert result.valid is False
        assert len(result.errors) == 2
        assert bool(result) is False

    def test_bool_conversion(self):
        """Test boolean conversion."""
        valid = ValidationResult(valid=True)
        invalid = ValidationResult(valid=False)

        assert valid  # truthy
        assert not invalid  # falsy

    def test_use_in_if_statement(self):
        """Test usage in if statement."""
        result = ValidationResult(valid=True)

        if result:
            passed = True
        else:
            passed = False

        assert passed is True


class TestUploadConfig:
    """Test UploadConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = UploadConfig()

        assert config.chunked_threshold_mb == 50
        assert config.batch_size == 1
        assert config.max_workers == 32
        assert config.use_presigned is True

    def test_custom_values(self):
        """Test custom configuration values."""
        config = UploadConfig(
            chunked_threshold_mb=100,
            batch_size=10,
            max_workers=16,
            use_presigned=False,
        )

        assert config.chunked_threshold_mb == 100
        assert config.batch_size == 10
        assert config.max_workers == 16
        assert config.use_presigned is False


class TestFlatFileDiscoveryStrategy:
    """Test FlatFileDiscoveryStrategy."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create flat files
            (root / 'file1.jpg').touch()
            (root / 'file2.jpg').touch()
            (root / 'file3.png').touch()

            # Create subdirectory with files
            subdir = root / 'subdir'
            subdir.mkdir()
            (subdir / 'nested1.jpg').touch()
            (subdir / 'nested2.jpg').touch()

            # Create excluded files
            (root / '.DS_Store').touch()
            (root / 'Thumbs.db').touch()

            yield root

    def test_discover_flat_files_only(self, temp_dir):
        """Test flat discovery returns only immediate files."""
        strategy = FlatFileDiscoveryStrategy()
        files = strategy.discover(temp_dir, recursive=False)

        file_names = {f.name for f in files}

        # Should find flat files but not nested or excluded
        assert 'file1.jpg' in file_names
        assert 'file2.jpg' in file_names
        assert 'file3.png' in file_names
        assert 'nested1.jpg' not in file_names
        assert '.DS_Store' not in file_names
        assert 'Thumbs.db' not in file_names

    def test_discover_recursive(self, temp_dir):
        """Test recursive discovery includes nested files."""
        strategy = FlatFileDiscoveryStrategy()
        files = strategy.discover(temp_dir, recursive=True)

        file_names = {f.name for f in files}

        # Should find all files including nested
        assert 'file1.jpg' in file_names
        assert 'nested1.jpg' in file_names
        assert 'nested2.jpg' in file_names

    def test_discover_excludes_system_files(self, temp_dir):
        """Test that system files are excluded."""
        strategy = FlatFileDiscoveryStrategy()
        files = strategy.discover(temp_dir, recursive=True)

        file_names = {f.name for f in files}

        assert '.DS_Store' not in file_names
        assert 'Thumbs.db' not in file_names

    def test_discover_non_existent_path(self):
        """Test discovery of non-existent path returns empty."""
        strategy = FlatFileDiscoveryStrategy()
        files = strategy.discover(Path('/non/existent/path'))

        assert files == []

    def test_discover_file_path_not_directory(self, temp_dir):
        """Test discovery of file (not directory) returns empty."""
        strategy = FlatFileDiscoveryStrategy()
        file_path = temp_dir / 'file1.jpg'
        files = strategy.discover(file_path)

        assert files == []


class TestRecursiveFileDiscoveryStrategy:
    """Test RecursiveFileDiscoveryStrategy."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create nested structure
            (root / 'file1.jpg').touch()

            level1 = root / 'level1'
            level1.mkdir()
            (level1 / 'file2.jpg').touch()

            level2 = level1 / 'level2'
            level2.mkdir()
            (level2 / 'file3.jpg').touch()

            yield root

    def test_default_is_recursive(self, temp_dir):
        """Test that default discovery is recursive."""
        strategy = RecursiveFileDiscoveryStrategy()
        files = strategy.discover(temp_dir)  # no recursive param

        file_names = {f.name for f in files}

        assert 'file1.jpg' in file_names
        assert 'file2.jpg' in file_names
        assert 'file3.jpg' in file_names

    def test_can_override_to_flat(self, temp_dir):
        """Test that recursive=False works."""
        strategy = RecursiveFileDiscoveryStrategy()
        files = strategy.discover(temp_dir, recursive=False)

        file_names = {f.name for f in files}

        assert 'file1.jpg' in file_names
        assert 'file2.jpg' not in file_names


class TestFileDiscoveryOrganize:
    """Test file organization functionality."""

    @pytest.fixture
    def temp_dir_with_specs(self):
        """Create directory structure matching specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)

            # Create type directories
            image_dir = root / 'image_1'
            image_dir.mkdir()
            (image_dir / 'sample_001.jpg').touch()
            (image_dir / 'sample_002.jpg').touch()

            pcd_dir = root / 'pcd_1'
            pcd_dir.mkdir()
            (pcd_dir / 'sample_001.pcd').touch()
            (pcd_dir / 'sample_002.pcd').touch()

            yield root

    @pytest.fixture
    def specs(self):
        """Sample file specifications."""
        return [
            {'name': 'image_1', 'is_required': True, 'extensions': ['.jpg', '.png']},
            {'name': 'pcd_1', 'is_required': True, 'extensions': ['.pcd']},
        ]

    def test_organize_groups_by_stem(self, temp_dir_with_specs, specs):
        """Test that files are grouped by stem."""
        strategy = RecursiveFileDiscoveryStrategy()
        files = strategy.discover(temp_dir_with_specs)

        organized = strategy.organize(files, specs, metadata={})

        # Should have 2 groups (sample_001 and sample_002)
        assert len(organized) == 2

        # Each group should have both specs
        for entry in organized:
            assert 'image_1' in entry['files']
            assert 'pcd_1' in entry['files']

    def test_organize_with_metadata(self, temp_dir_with_specs, specs):
        """Test that metadata is attached to organized files."""
        strategy = RecursiveFileDiscoveryStrategy()
        files = strategy.discover(temp_dir_with_specs)

        metadata = {
            'sample_001': {'label': 'car'},
            'sample_002': {'label': 'pedestrian'},
        }

        organized = strategy.organize(files, specs, metadata)

        # Check metadata is attached
        labels = {entry['meta'].get('label') for entry in organized}
        assert 'car' in labels or 'pedestrian' in labels

    def test_organize_empty_files(self, specs):
        """Test organizing empty file list."""
        strategy = FlatFileDiscoveryStrategy()
        organized = strategy.organize([], specs, {})

        assert organized == []


class TestStrategyInterfaces:
    """Test that strategy interfaces are properly defined."""

    def test_validation_strategy_is_abstract(self):
        """Test ValidationStrategy is abstract."""
        with pytest.raises(TypeError):
            ValidationStrategy()

    def test_file_discovery_strategy_is_abstract(self):
        """Test FileDiscoveryStrategy is abstract."""
        with pytest.raises(TypeError):
            FileDiscoveryStrategy()

    def test_metadata_strategy_is_abstract(self):
        """Test MetadataStrategy is abstract."""
        with pytest.raises(TypeError):
            MetadataStrategy()

    def test_upload_strategy_is_abstract(self):
        """Test UploadStrategy requires context."""
        mock_context = MagicMock()

        # Should not raise - UploadStrategy takes context in init
        # But calling abstract methods should fail
        class IncompleteUploadStrategy(UploadStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteUploadStrategy(mock_context)

    def test_data_unit_strategy_is_abstract(self):
        """Test DataUnitStrategy is abstract."""
        mock_context = MagicMock()

        class IncompleteDataUnitStrategy(DataUnitStrategy):
            pass

        with pytest.raises(TypeError):
            IncompleteDataUnitStrategy(mock_context)
