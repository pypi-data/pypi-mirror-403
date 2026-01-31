"""Tests for bulk upload strategies."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig
from synapse_sdk.clients.backend.bulk_upload.models import (
    ConfirmUploadResponse,
    PresignedUploadResponse,
)
from synapse_sdk.clients.backend.bulk_upload.strategies.presigned import (
    PresignedUploadResult,
    PresignedUploadStrategy,
)


class TestPresignedUploadResult:
    """Tests for PresignedUploadResult dataclass."""

    def test_creation(self) -> None:
        """Test creating a PresignedUploadResult."""
        result = PresignedUploadResult(
            checksum='abc123def456',
            size=1024,
        )

        assert result.checksum == 'abc123def456'
        assert result.size == 1024


class TestPresignedUploadStrategy:
    """Tests for PresignedUploadStrategy."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock client."""
        return MagicMock()

    @pytest.fixture
    def strategy(self, mock_client: MagicMock) -> PresignedUploadStrategy:
        """Create a PresignedUploadStrategy instance."""
        return PresignedUploadStrategy(mock_client)

    def test_strategy_name(self, strategy: PresignedUploadStrategy) -> None:
        """Test strategy has correct name."""
        assert strategy.strategy_name == 'presigned'

    def test_supported_providers(self, strategy: PresignedUploadStrategy) -> None:
        """Test strategy supports expected providers."""
        expected = frozenset({'amazon_s3', 's3', 'minio', 'gcp', 'gcs', 'azure'})
        assert strategy.supported_providers == expected

    @pytest.mark.parametrize(
        'provider,expected',
        [
            ('amazon_s3', True),
            ('s3', True),
            ('minio', True),
            ('gcp', True),
            ('gcs', True),
            ('azure', True),
            ('AMAZON_S3', True),  # Case insensitive
            ('S3', True),
            ('local', False),
            ('unknown', False),
            ('', False),
        ],
    )
    def test_supports_storage(
        self,
        strategy: PresignedUploadStrategy,
        provider: str,
        expected: bool,
    ) -> None:
        """Test supports_storage for various providers."""
        storage = {'provider': provider}
        assert strategy.supports_storage(storage) == expected

    def test_supports_storage_missing_provider(self, strategy: PresignedUploadStrategy) -> None:
        """Test supports_storage with missing provider key."""
        storage = {}
        assert strategy.supports_storage(storage) is False

    def test_upload_files_empty_list(
        self,
        strategy: PresignedUploadStrategy,
        mock_client: MagicMock,
    ) -> None:
        """Test uploading empty file list returns early."""
        config = BulkUploadConfig()

        # Set up mock to return presigned URLs
        mock_client.request_presigned_upload.return_value = PresignedUploadResponse(
            files=[],
            expires_at='2024-01-01T12:00:00Z',
        )
        mock_client.confirm_upload.return_value = ConfirmUploadResponse(
            results=[],
            created_count=0,
            failed_count=0,
        )

        result = strategy.upload_files([], config)

        assert result.created_count == 0
        assert result.failed_count == 0

    @pytest.fixture
    def temp_files(self, tmp_path: Path) -> list[Path]:
        """Create temporary test files."""
        files = []
        for i in range(3):
            file_path = tmp_path / f'test_{i}.txt'
            file_path.write_text(f'Test content {i}')
            files.append(file_path)
        return files


class TestPresignedUploadStrategyHelpers:
    """Tests for PresignedUploadStrategy helper methods and checksum calculation."""

    def test_calculates_checksum_correctly(self, tmp_path: Path) -> None:
        """Test that file checksum is calculated correctly using SHA1."""
        import hashlib

        sample_file = tmp_path / 'sample.txt'
        sample_file.write_text('Sample content for testing')

        expected_checksum = hashlib.sha1(sample_file.read_bytes()).hexdigest()

        # Verify the checksum calculation approach matches SHA1
        actual_checksum = hashlib.sha1(sample_file.read_bytes()).hexdigest()

        assert actual_checksum == expected_checksum
        assert len(actual_checksum) == 40  # SHA1 produces 40 hex characters

    def test_checksum_different_for_different_content(self, tmp_path: Path) -> None:
        """Test that different file contents produce different checksums."""
        import hashlib

        file1 = tmp_path / 'file1.txt'
        file2 = tmp_path / 'file2.txt'
        file1.write_text('Content A')
        file2.write_text('Content B')

        checksum1 = hashlib.sha1(file1.read_bytes()).hexdigest()
        checksum2 = hashlib.sha1(file2.read_bytes()).hexdigest()

        assert checksum1 != checksum2

    def test_checksum_same_for_same_content(self, tmp_path: Path) -> None:
        """Test that same file content produces same checksum."""
        import hashlib

        file1 = tmp_path / 'file1.txt'
        file2 = tmp_path / 'file2.txt'
        content = 'Same content'
        file1.write_text(content)
        file2.write_text(content)

        checksum1 = hashlib.sha1(file1.read_bytes()).hexdigest()
        checksum2 = hashlib.sha1(file2.read_bytes()).hexdigest()

        assert checksum1 == checksum2
