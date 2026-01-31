"""Base class for bulk upload strategies.

This module defines the BulkUploadStrategy abstract base class that all
upload strategies must implement.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig
    from synapse_sdk.clients.backend.bulk_upload.models import ConfirmUploadResponse
    from synapse_sdk.clients.protocols import ClientProtocol


class BulkUploadStrategy(ABC):
    """Abstract base class for bulk upload strategies.

    Defines the interface for different upload mechanisms:
    - PresignedUploadStrategy: Direct-to-storage via presigned URLs
    - (future) DirectUploadStrategy: Traditional API server upload
    - (future) StreamingUploadStrategy: Streaming upload for real-time data

    Strategies handle the actual file transfer but delegate API calls
    to the client through dependency injection.

    Attributes:
        strategy_name: Unique identifier for this strategy (e.g., 'presigned').
        supported_providers: Set of storage provider names this strategy supports.

    Example:
        >>> class MyUploadStrategy(BulkUploadStrategy):
        ...     strategy_name = 'my_upload'
        ...     supported_providers = frozenset({'s3', 'gcs'})
        ...
        ...     def supports_storage(self, storage):
        ...         return storage.get('provider', '').lower() in self.supported_providers
        ...
        ...     def upload_files(self, file_paths, config, *, on_progress=None):
        ...         # Implementation here
        ...         pass
    """

    # Strategy identifier for configuration and logging
    strategy_name: ClassVar[str]

    # Set of supported storage providers (e.g., {'amazon_s3', 'minio', 'gcs'})
    supported_providers: ClassVar[frozenset[str]]

    def __init__(self, client: 'ClientProtocol') -> None:
        """Initialize with client for API calls.

        Args:
            client: HTTP client implementing ClientProtocol.
        """
        self.client = client

    @abstractmethod
    def supports_storage(self, storage: dict[str, Any]) -> bool:
        """Check if this strategy supports the given storage provider.

        Args:
            storage: Storage configuration dict with 'provider' key.

        Returns:
            True if this strategy can handle the storage provider.
        """

    @abstractmethod
    def upload_files(
        self,
        file_paths: list[Path],
        config: 'BulkUploadConfig',
        *,
        on_progress: 'Callable[[int, int], None] | None' = None,
    ) -> 'ConfirmUploadResponse':
        """Upload files using this strategy.

        Args:
            file_paths: List of local file paths to upload.
            config: Upload configuration.
            on_progress: Optional progress callback(completed, total).

        Returns:
            ConfirmUploadResponse with success/failure information.
        """


__all__ = ['BulkUploadStrategy']
