"""Strategy pattern implementations for upload operations.

Provides pluggable strategies for:
    - File Discovery: FlatFileDiscoveryStrategy, RecursiveFileDiscoveryStrategy
    - Metadata Extraction: ExcelMetadataStrategy, NoneMetadataStrategy
    - File Upload: SyncUploadStrategy
    - Data Unit Generation: SingleDataUnitStrategy, BatchDataUnitStrategy

Example:
    >>> from synapse_sdk.plugins.actions.upload.strategies import (
    ...     RecursiveFileDiscoveryStrategy,
    ...     ExcelMetadataStrategy,
    ...     SyncUploadStrategy,
    ...     BatchDataUnitStrategy,
    ... )
    >>>
    >>> # Use strategies in upload workflow
    >>> discovery = RecursiveFileDiscoveryStrategy()
    >>> files = discovery.discover(Path("/data"))
    >>>
    >>> metadata_strategy = ExcelMetadataStrategy()
    >>> metadata = metadata_strategy.extract(Path("metadata.xlsx"))
"""

from synapse_sdk.plugins.actions.upload.strategies.base import (
    DataUnitStrategy,
    FileDiscoveryStrategy,
    MetadataStrategy,
    UploadConfig,
    UploadStrategy,
    ValidationResult,
    ValidationStrategy,
)
from synapse_sdk.plugins.actions.upload.strategies.data_unit import (
    BatchDataUnitStrategy,
    SingleDataUnitStrategy,
    get_batched_list,
)
from synapse_sdk.plugins.actions.upload.strategies.file_discovery import (
    EXCLUDED_DIRS,
    EXCLUDED_FILES,
    FlatFileDiscoveryStrategy,
    RecursiveFileDiscoveryStrategy,
)
from synapse_sdk.plugins.actions.upload.strategies.metadata import (
    ExcelMetadataStrategy,
    NoneMetadataStrategy,
)
from synapse_sdk.plugins.actions.upload.strategies.upload_strategy import (
    SyncUploadStrategy,
)
from synapse_sdk.plugins.actions.upload.strategies.validation import (
    DefaultValidationStrategy,
)

__all__ = [
    # Base classes
    'ValidationResult',
    'UploadConfig',
    'ValidationStrategy',
    'FileDiscoveryStrategy',
    'MetadataStrategy',
    'UploadStrategy',
    'DataUnitStrategy',
    # Validation
    'DefaultValidationStrategy',
    # File Discovery
    'EXCLUDED_DIRS',
    'EXCLUDED_FILES',
    'FlatFileDiscoveryStrategy',
    'RecursiveFileDiscoveryStrategy',
    # Metadata
    'ExcelMetadataStrategy',
    'NoneMetadataStrategy',
    # Upload
    'SyncUploadStrategy',
    # Data Unit
    'get_batched_list',
    'SingleDataUnitStrategy',
    'BatchDataUnitStrategy',
]
