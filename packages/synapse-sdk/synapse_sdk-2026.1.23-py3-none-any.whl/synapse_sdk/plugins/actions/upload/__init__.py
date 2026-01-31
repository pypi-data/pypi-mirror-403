"""Upload action module with workflow step support.

Provides a full step-based workflow system for upload actions:
    - BaseUploadAction: Base class for upload workflows
    - UploadContext: Upload-specific context extending BaseStepContext
    - ValidationErrorCode: Error codes for parameter validation
    - VALIDATION_ERROR_MESSAGES: Human-readable error messages
    - UploadStatus: Status codes for upload operations
    - LogCode: Logging codes for upload workflow events
    - LogLevel: Log level enumeration for message categorization
    - LOG_MESSAGES: Log message templates and levels
    - UploadParams: Main parameter model with validation
    - AssetConfig: Per-asset path configuration for multi-path mode
    - ExcelSecurityConfig: Security limits for Excel file processing
    - Exceptions: UploadError, ExcelSecurityError, ExcelParsingError, etc.

For step infrastructure (BaseStep, StepRegistry, Orchestrator),
use the steps module:
    from synapse_sdk.plugins.steps import BaseStep, StepRegistry

The upload action supports two operational modes:

Single Path Mode (use_single_path=True, DEFAULT):
    Traditional mode where all file specifications share one base path.
    Requires 'path' parameter.

Multi-Path Mode (use_single_path=False):
    Advanced mode where each file specification has its own path.
    Requires 'assets' parameter with AssetConfig for each asset.

Example:
    >>> from synapse_sdk.plugins.steps import BaseStep, StepResult
    >>> from synapse_sdk.plugins.actions.upload import (
    ...     BaseUploadAction,
    ...     UploadContext,
    ...     UploadParams,
    ... )
    >>>
    >>> class InitStep(BaseStep[UploadContext]):
    ...     @property
    ...     def name(self) -> str:
    ...         return 'initialize'
    ...
    ...     @property
    ...     def progress_weight(self) -> float:
    ...         return 0.1
    ...
    ...     def execute(self, context: UploadContext) -> StepResult:
    ...         # Initialize storage, validate params
    ...         return StepResult(success=True)
    >>>
    >>> class MyUploadAction(BaseUploadAction[UploadParams]):
    ...     def setup_steps(self, registry) -> None:
    ...         registry.register(InitStep())
"""

from synapse_sdk.plugins.actions.upload.action import (
    BaseUploadAction,
    DefaultUploadAction,
)
from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import (
    LOG_MESSAGES,
    VALIDATION_ERROR_MESSAGES,
    LogCode,
    LogLevel,
    UploadStatus,
    ValidationErrorCode,
)
from synapse_sdk.plugins.actions.upload.exceptions import (
    ExcelParsingError,
    ExcelSecurityError,
    FileProcessingError,
    FileUploadError,
    FileValidationError,
    UploadError,
)
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.models import (
    AssetConfig,
    ExcelSecurityConfig,
    UploadParams,
)
from synapse_sdk.plugins.actions.upload.steps import (
    AnalyzeCollectionStep,
    CleanupStep,
    GenerateDataUnitsStep,
    InitializeStep,
    OrganizeFilesStep,
    ProcessMetadataStep,
    UploadFilesStep,
    ValidateFilesStep,
)
from synapse_sdk.plugins.actions.upload.strategies import (
    BatchDataUnitStrategy,
    DataUnitStrategy,
    DefaultValidationStrategy,
    ExcelMetadataStrategy,
    FileDiscoveryStrategy,
    FlatFileDiscoveryStrategy,
    MetadataStrategy,
    NoneMetadataStrategy,
    RecursiveFileDiscoveryStrategy,
    SingleDataUnitStrategy,
    SyncUploadStrategy,
    UploadConfig,
    UploadStrategy,
    ValidationResult,
    ValidationStrategy,
)

__all__ = [
    # Action
    'BaseUploadAction',
    'DefaultUploadAction',
    # Steps
    'InitializeStep',
    'ProcessMetadataStep',
    'AnalyzeCollectionStep',
    'OrganizeFilesStep',
    'ValidateFilesStep',
    'UploadFilesStep',
    'GenerateDataUnitsStep',
    'CleanupStep',
    # Context
    'UploadContext',
    # Log Messages
    'UploadLogMessageCode',
    # Enums
    'ValidationErrorCode',
    'VALIDATION_ERROR_MESSAGES',
    'UploadStatus',
    'LogCode',
    'LogLevel',
    'LOG_MESSAGES',
    # Models
    'UploadParams',
    'AssetConfig',
    'ExcelSecurityConfig',
    # Exceptions
    'UploadError',
    'ExcelSecurityError',
    'ExcelParsingError',
    'FileUploadError',
    'FileValidationError',
    'FileProcessingError',
    # Strategies - Base
    'ValidationResult',
    'UploadConfig',
    'ValidationStrategy',
    'FileDiscoveryStrategy',
    'MetadataStrategy',
    'UploadStrategy',
    'DataUnitStrategy',
    # Strategies - Validation
    'DefaultValidationStrategy',
    # Strategies - File Discovery
    'FlatFileDiscoveryStrategy',
    'RecursiveFileDiscoveryStrategy',
    # Strategies - Metadata
    'ExcelMetadataStrategy',
    'NoneMetadataStrategy',
    # Strategies - Upload
    'SyncUploadStrategy',
    # Strategies - Data Unit
    'SingleDataUnitStrategy',
    'BatchDataUnitStrategy',
]
