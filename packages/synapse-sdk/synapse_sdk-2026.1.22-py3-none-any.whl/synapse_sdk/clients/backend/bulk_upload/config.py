"""Configuration for bulk upload operations.

This module provides the BulkUploadConfig dataclass for configuring
upload strategies with validation.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BulkUploadConfig:
    """Configuration for bulk upload strategies.

    Attributes:
        max_workers: Maximum concurrent upload threads. Default 32.
            Valid range: 1 to 100.
        batch_size: Files per batch for presigned URL requests. Default 200.
            Valid range: 1 to 1000.
        url_expiration: Presigned URL expiration in seconds. Default 3600.
            Valid range: 60 to 86400 (1 minute to 24 hours).
        timeout: Single file upload timeout in seconds. Default 300.
        preferred_strategy: Preferred strategy name or None for auto-select.

    Example:
        >>> config = BulkUploadConfig(max_workers=16, batch_size=100)
        >>> config = BulkUploadConfig(preferred_strategy='presigned')
    """

    max_workers: int = 32
    batch_size: int = 200
    url_expiration: int = 3600
    timeout: float = 300.0
    preferred_strategy: str | None = None

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 1 <= self.max_workers <= 100:
            msg = f'max_workers must be 1-100, got {self.max_workers}'
            raise ValueError(msg)
        if not 1 <= self.batch_size <= 1000:
            msg = f'batch_size must be 1-1000, got {self.batch_size}'
            raise ValueError(msg)
        if not 60 <= self.url_expiration <= 86400:
            msg = f'url_expiration must be 60-86400, got {self.url_expiration}'
            raise ValueError(msg)


__all__ = ['BulkUploadConfig']
