"""Bulk upload client with pluggable strategies.

This package provides high-performance file upload capabilities using
different strategies based on storage provider capabilities.

Strategies are managed via UploadStrategyRegistry, allowing easy
addition of new upload methods without modifying the mixin.

Example:
    >>> from synapse_sdk.clients.backend import BackendClient
    >>> client = BackendClient(...)
    >>> result = client.upload_files_bulk(files)

    # Custom strategy registration
    >>> from synapse_sdk.clients.backend.bulk_upload import get_strategy_registry
    >>> registry = get_strategy_registry()
    >>> registry.register(MyCustomStrategy)

Strategies:
    - presigned: Direct-to-storage uploads using presigned URLs
    - (future) direct: Traditional API server uploads
"""

from synapse_sdk.clients.backend.bulk_upload.base import BulkUploadStrategy
from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig
from synapse_sdk.clients.backend.bulk_upload.mixin import BulkUploadClientMixin
from synapse_sdk.clients.backend.bulk_upload.models import (
    DEFAULT_PART_SIZE,
    PRESIGNED_UPLOAD_PROVIDERS,
    ConfirmFileResult,
    ConfirmUploadResponse,
    MultipartUploadInfo,
    PresignedFileInfo,
    PresignedUploadPart,
    PresignedUploadResponse,
)
from synapse_sdk.clients.backend.bulk_upload.registry import (
    UploadStrategyRegistry,
    get_strategy_registry,
)
from synapse_sdk.clients.backend.bulk_upload.strategies import (
    PresignedUploadResult,
    PresignedUploadStrategy,
)

__all__ = [
    # Mixin
    'BulkUploadClientMixin',
    # Strategy base
    'BulkUploadStrategy',
    # Registry
    'UploadStrategyRegistry',
    'get_strategy_registry',
    # Configuration
    'BulkUploadConfig',
    # Strategies
    'PresignedUploadStrategy',
    # Models
    'PresignedUploadResult',
    'PresignedUploadPart',
    'MultipartUploadInfo',
    'PresignedFileInfo',
    'PresignedUploadResponse',
    'ConfirmFileResult',
    'ConfirmUploadResponse',
    # Constants
    'PRESIGNED_UPLOAD_PROVIDERS',
    'DEFAULT_PART_SIZE',
]
