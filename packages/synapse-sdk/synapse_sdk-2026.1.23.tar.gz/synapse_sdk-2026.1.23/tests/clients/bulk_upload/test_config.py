"""Tests for BulkUploadConfig dataclass."""

from __future__ import annotations

import pytest

from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig


class TestBulkUploadConfig:
    """Tests for BulkUploadConfig dataclass."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = BulkUploadConfig()

        assert config.max_workers == 32
        assert config.batch_size == 200
        assert config.url_expiration == 3600
        assert config.timeout == 300.0
        assert config.preferred_strategy is None

    def test_custom_values(self) -> None:
        """Test custom configuration values."""
        config = BulkUploadConfig(
            max_workers=16,
            batch_size=100,
            url_expiration=7200,
            timeout=600.0,
            preferred_strategy='presigned',
        )

        assert config.max_workers == 16
        assert config.batch_size == 100
        assert config.url_expiration == 7200
        assert config.timeout == 600.0
        assert config.preferred_strategy == 'presigned'

    def test_max_workers_validation_lower_bound(self) -> None:
        """Test max_workers must be at least 1."""
        with pytest.raises(ValueError, match='max_workers must be 1-100'):
            BulkUploadConfig(max_workers=0)

    def test_max_workers_validation_upper_bound(self) -> None:
        """Test max_workers must be at most 100."""
        with pytest.raises(ValueError, match='max_workers must be 1-100'):
            BulkUploadConfig(max_workers=101)

    def test_max_workers_boundary_values(self) -> None:
        """Test max_workers at boundary values."""
        config_min = BulkUploadConfig(max_workers=1)
        assert config_min.max_workers == 1

        config_max = BulkUploadConfig(max_workers=100)
        assert config_max.max_workers == 100

    def test_batch_size_validation_lower_bound(self) -> None:
        """Test batch_size must be at least 1."""
        with pytest.raises(ValueError, match='batch_size must be 1-1000'):
            BulkUploadConfig(batch_size=0)

    def test_batch_size_validation_upper_bound(self) -> None:
        """Test batch_size must be at most 1000."""
        with pytest.raises(ValueError, match='batch_size must be 1-1000'):
            BulkUploadConfig(batch_size=1001)

    def test_batch_size_boundary_values(self) -> None:
        """Test batch_size at boundary values."""
        config_min = BulkUploadConfig(batch_size=1)
        assert config_min.batch_size == 1

        config_max = BulkUploadConfig(batch_size=1000)
        assert config_max.batch_size == 1000

    def test_url_expiration_validation_lower_bound(self) -> None:
        """Test url_expiration must be at least 60 seconds."""
        with pytest.raises(ValueError, match='url_expiration must be 60-86400'):
            BulkUploadConfig(url_expiration=59)

    def test_url_expiration_validation_upper_bound(self) -> None:
        """Test url_expiration must be at most 24 hours."""
        with pytest.raises(ValueError, match='url_expiration must be 60-86400'):
            BulkUploadConfig(url_expiration=86401)

    def test_url_expiration_boundary_values(self) -> None:
        """Test url_expiration at boundary values."""
        config_min = BulkUploadConfig(url_expiration=60)
        assert config_min.url_expiration == 60

        config_max = BulkUploadConfig(url_expiration=86400)
        assert config_max.url_expiration == 86400
