"""Bulk upload client mixin - orchestrator for upload strategies.

This module provides the BulkUploadClientMixin that delegates upload
operations to strategy implementations based on storage provider capabilities.
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.bulk_upload.base import BulkUploadStrategy
from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig
from synapse_sdk.clients.backend.bulk_upload.models import (
    ConfirmUploadResponse,
    PresignedUploadResponse,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from synapse_sdk.clients.backend.bulk_upload.strategies.presigned import (
        PresignedUploadResult,
    )
    from synapse_sdk.clients.protocols import ClientProtocol


class BulkUploadClientMixin:
    """Mixin providing bulk upload operations with pluggable strategies.

    This mixin serves as an orchestrator, delegating actual uploads to
    strategy implementations based on storage provider capabilities.

    Strategies are discovered via UploadStrategyRegistry, allowing easy
    addition of new upload methods without modifying this class.

    Available strategies:
        - presigned: Direct-to-storage via presigned URLs (S3, GCS, Azure)
        - (future) direct: Traditional API server upload

    The upload flow:
        1. Get default storage configuration
        2. Select appropriate strategy for storage provider (via registry)
        3. Delegate upload to selected strategy
        4. Return results to caller

    Example:
        >>> client = BackendClient(...)
        >>> result = client.upload_files_bulk(files)  # Auto-selects strategy
        >>> result = client.upload_files_bulk(files, strategy='presigned')  # Explicit
    """

    # Cache for strategy instances (per client)
    _strategy_instances: dict[str, BulkUploadStrategy] | None = None

    def _get_strategy_instance(
        self: 'ClientProtocol',
        name: str,
    ) -> BulkUploadStrategy:
        """Get or create a strategy instance by name.

        Uses lazy initialization and caching for strategy instances.

        Args:
            name: Strategy name (e.g., 'presigned').

        Returns:
            Strategy instance.

        Raises:
            ValueError: If strategy not found in registry.
        """
        from synapse_sdk.clients.backend.bulk_upload.registry import get_strategy_registry

        if self._strategy_instances is None:
            self._strategy_instances = {}

        if name not in self._strategy_instances:
            registry = get_strategy_registry()
            self._strategy_instances[name] = registry.create(name, self)

        return self._strategy_instances[name]

    def _select_upload_strategy(
        self: 'ClientProtocol',
        storage: dict[str, Any],
        preferred: str | None = None,
    ) -> BulkUploadStrategy:
        """Select appropriate upload strategy for storage.

        Uses the registry to find a strategy that supports the storage provider.

        Args:
            storage: Storage configuration dictionary.
            preferred: Preferred strategy name (optional).

        Returns:
            Selected BulkUploadStrategy instance.

        Raises:
            ValueError: If no suitable strategy found.
        """
        from synapse_sdk.clients.backend.bulk_upload.registry import get_strategy_registry

        registry = get_strategy_registry()
        strategy_cls = registry.select_for_storage_or_raise(storage, preferred)

        # Get cached instance
        return self._get_strategy_instance(strategy_cls.strategy_name)

    def get_default_storage(self: 'ClientProtocol') -> dict[str, Any]:
        """Get the default storage configuration for the current tenant.

        Returns:
            Storage configuration dictionary containing provider, ID, and settings.

        Raises:
            ValueError: If no default storage is configured for the tenant.

        Example:
            >>> storage = client.get_default_storage()
            >>> print(storage['provider'])
            amazon_s3
        """
        response = self._get('storages/', params={'is_default': 'true'})

        if isinstance(response, list):
            results = response
        else:
            results = response.get('results', [])

        if not results:
            msg = 'No default storage configured for tenant'
            raise ValueError(msg)

        return results[0]

    # --- Public API ---

    def upload_files_bulk(
        self: 'ClientProtocol',
        file_paths: list[Path],
        *,
        max_workers: int = 32,
        on_progress: 'Callable[[int, int], None] | None' = None,
        batch_size: int = 200,
        strategy: str | None = None,
    ) -> ConfirmUploadResponse:
        """Upload multiple files using optimal strategy.

        Automatically selects the best upload strategy based on storage
        provider, or uses explicitly specified strategy.

        Args:
            file_paths: List of local file paths to upload.
            max_workers: Maximum number of concurrent upload threads.
                Default is 32. Valid range: 1 to 100.
            on_progress: Optional callback function called after each file completes.
                Signature: (completed: int, total: int) -> None
            batch_size: Number of files to process per batch. Default is 200.
            strategy: Strategy name ('presigned', etc.) or None for auto-select.

        Returns:
            ConfirmUploadResponse with created DataFile information.

        Raises:
            ValueError: If no suitable strategy found for storage provider.

        Example:
            >>> from pathlib import Path
            >>> files = list(Path('/data/images').glob('*.jpg'))
            >>> result = client.upload_files_bulk(files, max_workers=16)
            >>> print(f"Uploaded {result.created_count} files")
        """
        if not file_paths:
            return ConfirmUploadResponse(results=[], created_count=0, failed_count=0)

        config = BulkUploadConfig(
            max_workers=max_workers,
            batch_size=batch_size,
            preferred_strategy=strategy,
        )

        storage = self.get_default_storage()
        selected_strategy = self._select_upload_strategy(storage, strategy)

        return selected_strategy.upload_files(
            file_paths,
            config,
            on_progress=on_progress,
        )

    # --- Deprecated backward compatibility methods ---
    # These methods are deprecated and will be removed in a future version.
    # Use upload_files_bulk() or access the strategy directly via registry.

    def _storage_supports_presigned_upload(
        self: 'ClientProtocol',
        storage: dict[str, Any],
    ) -> bool:
        """Check if storage provider supports presigned uploads.

        .. deprecated::
            Use ``get_strategy_registry().select_for_storage()`` instead.

        Args:
            storage: Storage configuration dictionary with 'provider' key.

        Returns:
            True if the provider supports presigned uploads, False otherwise.
        """
        warnings.warn(
            '_storage_supports_presigned_upload is deprecated. '
            'Use get_strategy_registry().select_for_storage() instead.',
            DeprecationWarning,
            stacklevel=2,
        )
        from synapse_sdk.clients.backend.bulk_upload.registry import get_strategy_registry

        registry = get_strategy_registry()
        strategy_cls = registry.select_for_storage(storage, preferred='presigned')
        return strategy_cls is not None

    def request_presigned_upload(
        self: 'ClientProtocol',
        files: list[dict[str, Any]],
        *,
        expiration: int = 3600,
    ) -> PresignedUploadResponse:
        """Request presigned URLs for direct-to-storage uploads.

        .. deprecated::
            Use ``upload_files_bulk()`` for full upload workflow, or access
            the presigned strategy directly via registry if needed.

        Args:
            files: List of file information dictionaries. Each dict should contain:
                - filename (str): Original filename
                - size (int): File size in bytes
                - content_type (str, optional): MIME type
            expiration: URL expiration time in seconds. Default is 3600 (1 hour).

        Returns:
            PresignedUploadResponse containing presigned URLs and file keys.
        """
        warnings.warn(
            'request_presigned_upload is deprecated. Use upload_files_bulk() for the full upload workflow.',
            DeprecationWarning,
            stacklevel=2,
        )
        strategy = self._get_strategy_instance('presigned')
        return strategy.request_presigned_upload(files, expiration)

    def confirm_presigned_upload(
        self: 'ClientProtocol',
        files: list[dict[str, Any]],
    ) -> ConfirmUploadResponse:
        """Confirm uploaded files and create DataFile records.

        .. deprecated::
            Use ``upload_files_bulk()`` for full upload workflow, or access
            the presigned strategy directly via registry if needed.

        Args:
            files: List of uploaded file information. Each dict should contain:
                - file_key (str): Storage key from presigned response
                - checksum (str): SHA1 checksum of uploaded file
                - size (int): File size in bytes
                - multipart (dict, optional): Multipart upload details

        Returns:
            ConfirmUploadResponse with created DataFile IDs and any errors.
        """
        warnings.warn(
            'confirm_presigned_upload is deprecated. Use upload_files_bulk() for the full upload workflow.',
            DeprecationWarning,
            stacklevel=2,
        )
        strategy = self._get_strategy_instance('presigned')
        return strategy.confirm_presigned_upload(files)

    def upload_file_to_presigned_url(
        self: 'ClientProtocol',
        presigned_url: str,
        file_path: Path,
        content_type: str | None = None,
    ) -> 'PresignedUploadResult':
        """Upload a file directly to storage using a presigned URL.

        .. deprecated::
            Use ``upload_files_bulk()`` for full upload workflow, or access
            the presigned strategy directly via registry if needed.

        Args:
            presigned_url: The presigned URL to upload to.
            file_path: Local path to the file to upload.
            content_type: Optional Content-Type header value.

        Returns:
            PresignedUploadResult with checksum and size.
        """
        warnings.warn(
            'upload_file_to_presigned_url is deprecated. Use upload_files_bulk() for the full upload workflow.',
            DeprecationWarning,
            stacklevel=2,
        )
        strategy = self._get_strategy_instance('presigned')
        return strategy.upload_file_to_presigned_url(presigned_url, file_path, content_type)


__all__ = ['BulkUploadClientMixin']
