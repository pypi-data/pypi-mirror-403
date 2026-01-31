"""Enums and constants for upload actions.

Provides:
    - ValidationErrorCode: Error codes for parameter validation
    - UploadStatus: Status codes for upload operations
    - LogCode: Logging codes for upload workflow events
    - LogLevel: Log level enumeration for message categorization
    - LOG_MESSAGES: Log message templates and levels
"""

from __future__ import annotations

from enum import Enum


class ValidationErrorCode(str, Enum):
    """Error codes for upload parameter validation.

    These codes are used with PydanticCustomError to provide
    machine-readable error identifiers.
    """

    MISSING_CONTEXT = 'missing_context'
    STORAGE_NOT_FOUND = 'storage_not_found'
    DATA_COLLECTION_NOT_FOUND = 'data_collection_not_found'
    PROJECT_NOT_FOUND = 'project_not_found'
    MISSING_PATH = 'missing_path'
    MISSING_ASSETS = 'missing_assets'


VALIDATION_ERROR_MESSAGES: dict[ValidationErrorCode, str] = {
    ValidationErrorCode.MISSING_CONTEXT: (
        'Validation context is required. Provide action context when validating parameters.'
    ),
    ValidationErrorCode.STORAGE_NOT_FOUND: 'Storage with id={} not found: {}',
    ValidationErrorCode.DATA_COLLECTION_NOT_FOUND: 'Data collection with id={} not found: {}',
    ValidationErrorCode.PROJECT_NOT_FOUND: 'Project with id={} not found: {}',
    ValidationErrorCode.MISSING_PATH: ("When use_single_path=True (single path mode), 'path' is required."),
    ValidationErrorCode.MISSING_ASSETS: (
        "When use_single_path=False (multi-path mode), 'assets' must be provided "
        'with path configurations for each file specification.'
    ),
}


class UploadStatus(str, Enum):
    """Upload processing status enumeration.

    Defines the possible states for upload operations, data files, and data units
    throughout the upload process.

    Attributes:
        SUCCESS: Upload completed successfully
        FAILED: Upload failed with errors
    """

    SUCCESS = 'success'
    FAILED = 'failed'


class LogLevel(str, Enum):
    """Log level enumeration for message categorization.

    Used to categorize log messages by severity and type,
    enabling appropriate UI styling and filtering.

    Attributes:
        INFO: General informational messages (neutral)
        SUCCESS: Success messages and positive outcomes
        WARNING: Warning messages for non-critical issues
        DANGER: Error messages and critical failures
        DEBUG: Debug-level messages for development
    """

    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'
    DEBUG = 'debug'


class LogCode(str, Enum):
    """Type-safe logging codes for upload operations.

    Enumeration of all possible log events during upload processing. Each code
    corresponds to a specific event or error state with predefined message
    templates and log levels.

    The codes are organized by category:
    - Validation codes (VALIDATION_FAILED, STORAGE_VALIDATION_FAILED, etc.)
    - File processing codes (NO_FILES_FOUND, FILES_DISCOVERED, etc.)
    - Excel processing codes (EXCEL_SECURITY_VIOLATION, EXCEL_PARSING_ERROR, etc.)
    - Progress tracking codes (UPLOADING_DATA_FILES, GENERATING_DATA_UNITS, etc.)
    - Step lifecycle codes (STEP_STARTING, STEP_COMPLETED, etc.)
    - Rollback codes (ROLLBACK_STARTING, ROLLBACK_COMPLETED, etc.)

    Each code maps to a configuration in LOG_MESSAGES with message template
    and appropriate log level.
    """

    # Validation codes
    STORAGE_VALIDATION_FAILED = 'STORAGE_VALIDATION_FAILED'
    COLLECTION_VALIDATION_FAILED = 'COLLECTION_VALIDATION_FAILED'
    PROJECT_VALIDATION_FAILED = 'PROJECT_VALIDATION_FAILED'
    VALIDATION_FAILED = 'VALIDATION_FAILED'

    # File discovery codes
    NO_FILES_FOUND = 'NO_FILES_FOUND'
    NO_FILES_UPLOADED = 'NO_FILES_UPLOADED'
    NO_DATA_UNITS_GENERATED = 'NO_DATA_UNITS_GENERATED'
    NO_TYPE_DIRECTORIES = 'NO_TYPE_DIRECTORIES'
    TYPE_DIRECTORIES_FOUND = 'TYPE_DIRECTORIES_FOUND'
    TYPE_STRUCTURE_DETECTED = 'TYPE_STRUCTURE_DETECTED'
    FILES_DISCOVERED = 'FILES_DISCOVERED'
    NO_FILES_FOUND_WARNING = 'NO_FILES_FOUND_WARNING'
    FILES_FILTERED_BY_EXTENSION = 'FILES_FILTERED_BY_EXTENSION'
    FILENAME_TOO_LONG = 'FILENAME_TOO_LONG'
    MISSING_REQUIRED_FILES = 'MISSING_REQUIRED_FILES'
    FILE_ORGANIZATION_STARTED = 'FILE_ORGANIZATION_STARTED'

    # Excel processing codes
    EXCEL_SECURITY_VIOLATION = 'EXCEL_SECURITY_VIOLATION'
    EXCEL_PARSING_ERROR = 'EXCEL_PARSING_ERROR'
    EXCEL_METADATA_LOADED = 'EXCEL_METADATA_LOADED'
    EXCEL_FILE_NOT_FOUND = 'EXCEL_FILE_NOT_FOUND'
    EXCEL_FILE_VALIDATION_STARTED = 'EXCEL_FILE_VALIDATION_STARTED'
    EXCEL_WORKBOOK_LOADED = 'EXCEL_WORKBOOK_LOADED'
    EXCEL_SECURITY_VALIDATION_STARTED = 'EXCEL_SECURITY_VALIDATION_STARTED'
    EXCEL_MEMORY_ESTIMATION = 'EXCEL_MEMORY_ESTIMATION'
    EXCEL_FILE_NOT_FOUND_PATH = 'EXCEL_FILE_NOT_FOUND_PATH'
    EXCEL_SECURITY_VALIDATION_FAILED = 'EXCEL_SECURITY_VALIDATION_FAILED'
    EXCEL_PARSING_FAILED = 'EXCEL_PARSING_FAILED'
    EXCEL_INVALID_FILE_FORMAT = 'EXCEL_INVALID_FILE_FORMAT'
    EXCEL_FILE_TOO_LARGE = 'EXCEL_FILE_TOO_LARGE'
    EXCEL_FILE_ACCESS_ERROR = 'EXCEL_FILE_ACCESS_ERROR'
    EXCEL_UNEXPECTED_ERROR = 'EXCEL_UNEXPECTED_ERROR'
    EXCEL_PATH_RESOLVED_STORAGE = 'EXCEL_PATH_RESOLVED_STORAGE'
    EXCEL_PATH_RESOLUTION_FAILED = 'EXCEL_PATH_RESOLUTION_FAILED'
    EXCEL_PATH_RESOLUTION_ERROR = 'EXCEL_PATH_RESOLUTION_ERROR'

    # Upload progress codes
    DATA_FILE_STATUS = 'DATA_FILE_STATUS'
    DATA_UNIT_STATUS = 'upload_data_unit'
    UPLOADING_DATA_FILES = 'UPLOADING_DATA_FILES'
    GENERATING_DATA_UNITS = 'GENERATING_DATA_UNITS'
    IMPORT_COMPLETED = 'IMPORT_COMPLETED'
    FILE_UPLOAD_FAILED = 'FILE_UPLOAD_FAILED'
    FILE_UPLOADED_SUCCESSFULLY = 'FILE_UPLOADED_SUCCESSFULLY'
    DATA_UNIT_BATCH_FAILED = 'DATA_UNIT_BATCH_FAILED'
    DATA_UNIT_CREATED = 'DATA_UNIT_CREATED'
    BATCH_PROCESSING_STARTED = 'BATCH_PROCESSING_STARTED'
    DATA_UNITS_CREATED_FROM_FILES = 'DATA_UNITS_CREATED_FROM_FILES'

    # Asset path codes
    ASSET_PATH_ACCESS_ERROR = 'ASSET_PATH_ACCESS_ERROR'
    ASSET_PATH_NOT_FOUND = 'ASSET_PATH_NOT_FOUND'

    # Step lifecycle codes
    STEP_STARTING = 'STEP_STARTING'
    STEP_COMPLETED = 'STEP_COMPLETED'
    STEP_SKIPPED = 'STEP_SKIPPED'
    STEP_ERROR = 'STEP_ERROR'
    STEP_FAILED = 'STEP_FAILED'
    STEP_EXCEPTION = 'STEP_EXCEPTION'
    STEP_TRACEBACK = 'STEP_TRACEBACK'

    # Rollback codes
    ROLLBACK_STARTING = 'ROLLBACK_STARTING'
    ROLLBACK_COMPLETED = 'ROLLBACK_COMPLETED'
    STEP_ROLLBACK = 'STEP_ROLLBACK'
    ROLLBACK_ERROR = 'ROLLBACK_ERROR'
    ROLLBACK_INITIALIZATION = 'ROLLBACK_INITIALIZATION'
    ROLLBACK_DATA_UNIT_GENERATION = 'ROLLBACK_DATA_UNIT_GENERATION'
    ROLLBACK_FILE_VALIDATION = 'ROLLBACK_FILE_VALIDATION'
    ROLLBACK_FILE_UPLOADS = 'ROLLBACK_FILE_UPLOADS'
    ROLLBACK_COLLECTION_ANALYSIS = 'ROLLBACK_COLLECTION_ANALYSIS'
    ROLLBACK_FILE_ORGANIZATION = 'ROLLBACK_FILE_ORGANIZATION'
    ROLLBACK_CLEANUP = 'ROLLBACK_CLEANUP'

    # Metadata processing codes
    NO_METADATA_STRATEGY = 'NO_METADATA_STRATEGY'
    METADATA_FILE_ATTRIBUTE_PROCESSING = 'METADATA_FILE_ATTRIBUTE_PROCESSING'
    METADATA_TEMP_FILE_CLEANUP = 'METADATA_TEMP_FILE_CLEANUP'
    METADATA_TEMP_FILE_CLEANUP_FAILED = 'METADATA_TEMP_FILE_CLEANUP_FAILED'
    METADATA_BASE64_DECODED = 'METADATA_BASE64_DECODED'
    METADATA_BASE64_DECODE_FAILED = 'METADATA_BASE64_DECODE_FAILED'

    # Multi-path mode codes
    MULTI_PATH_MODE_ENABLED = 'MULTI_PATH_MODE_ENABLED'
    OPTIONAL_SPEC_SKIPPED = 'OPTIONAL_SPEC_SKIPPED'
    DISCOVERING_FILES_FOR_ASSET = 'DISCOVERING_FILES_FOR_ASSET'
    NO_FILES_FOUND_FOR_ASSET = 'NO_FILES_FOUND_FOR_ASSET'
    FILES_FOUND_FOR_ASSET = 'FILES_FOUND_FOR_ASSET'
    ORGANIZING_FILES_MULTI_PATH = 'ORGANIZING_FILES_MULTI_PATH'
    TYPE_DIRECTORIES_MULTI_PATH = 'TYPE_DIRECTORIES_MULTI_PATH'

    # Cleanup codes
    CLEANUP_WARNING = 'CLEANUP_WARNING'
    CLEANUP_TEMP_DIR_SUCCESS = 'CLEANUP_TEMP_DIR_SUCCESS'
    CLEANUP_TEMP_DIR_FAILED = 'CLEANUP_TEMP_DIR_FAILED'

    # Workflow codes
    WORKFLOW_STARTING = 'WORKFLOW_STARTING'
    WORKFLOW_COMPLETED = 'WORKFLOW_COMPLETED'
    WORKFLOW_FAILED = 'WORKFLOW_FAILED'
    UPLOAD_WORKFLOW_FAILED = 'UPLOAD_WORKFLOW_FAILED'
    UNKNOWN_LOG_CODE = 'UNKNOWN_LOG_CODE'


# Log message templates and levels
LOG_MESSAGES: dict[LogCode, dict[str, str | LogLevel | None]] = {
    # Validation messages
    LogCode.STORAGE_VALIDATION_FAILED: {
        'message': 'Storage validation failed.',
        'level': LogLevel.DANGER,
    },
    LogCode.COLLECTION_VALIDATION_FAILED: {
        'message': 'Collection validation failed.',
        'level': LogLevel.DANGER,
    },
    LogCode.PROJECT_VALIDATION_FAILED: {
        'message': 'Project validation failed.',
        'level': LogLevel.DANGER,
    },
    LogCode.VALIDATION_FAILED: {
        'message': 'Validation failed.',
        'level': LogLevel.DANGER,
    },
    # File discovery messages
    LogCode.NO_FILES_FOUND: {
        'message': 'Files not found on the path.',
        'level': LogLevel.WARNING,
    },
    LogCode.NO_FILES_UPLOADED: {
        'message': 'No files were uploaded.',
        'level': LogLevel.WARNING,
    },
    LogCode.NO_DATA_UNITS_GENERATED: {
        'message': 'No data units were generated.',
        'level': LogLevel.WARNING,
    },
    LogCode.NO_TYPE_DIRECTORIES: {
        'message': 'No type-based directory structure found.',
        'level': LogLevel.INFO,
    },
    LogCode.TYPE_DIRECTORIES_FOUND: {
        'message': 'Found type directories: {}',
        'level': None,
    },
    LogCode.TYPE_STRUCTURE_DETECTED: {
        'message': 'Detected type-based directory structure',
        'level': None,
    },
    LogCode.FILES_DISCOVERED: {
        'message': 'Discovered {} files',
        'level': None,
    },
    LogCode.NO_FILES_FOUND_WARNING: {
        'message': 'No files found.',
        'level': LogLevel.WARNING,
    },
    LogCode.FILES_FILTERED_BY_EXTENSION: {
        'message': 'Filtered {} {} files with unavailable extensions: {} (allowed: {})',
        'level': LogLevel.WARNING,
    },
    LogCode.FILENAME_TOO_LONG: {
        'message': 'Skipping file with overly long name: {}...',
        'level': LogLevel.WARNING,
    },
    LogCode.MISSING_REQUIRED_FILES: {
        'message': '{} missing required files: {}',
        'level': LogLevel.WARNING,
    },
    LogCode.FILE_ORGANIZATION_STARTED: {
        'message': 'File organization started',
        'level': LogLevel.INFO,
    },
    # Excel processing messages
    LogCode.EXCEL_SECURITY_VIOLATION: {
        'message': 'Excel security validation failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_PARSING_ERROR: {
        'message': 'Excel parsing failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_METADATA_LOADED: {
        'message': 'Excel metadata loaded for {} files',
        'level': None,
    },
    LogCode.EXCEL_FILE_NOT_FOUND: {
        'message': 'Excel metadata file not found: {}',
        'level': LogLevel.WARNING,
    },
    LogCode.EXCEL_FILE_VALIDATION_STARTED: {
        'message': 'Excel file validation started',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_WORKBOOK_LOADED: {
        'message': 'Excel workbook loaded successfully',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_SECURITY_VALIDATION_STARTED: {
        'message': 'Excel security validation started for file size: {} bytes',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_MEMORY_ESTIMATION: {
        'message': 'Excel memory estimation: {} bytes (file) * 3 = {} bytes (estimated)',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_FILE_NOT_FOUND_PATH: {
        'message': 'Excel metadata file not found',
        'level': LogLevel.WARNING,
    },
    LogCode.EXCEL_SECURITY_VALIDATION_FAILED: {
        'message': 'Excel security validation failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_PARSING_FAILED: {
        'message': 'Excel parsing failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_INVALID_FILE_FORMAT: {
        'message': 'Invalid Excel file format: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_FILE_TOO_LARGE: {
        'message': 'Excel file too large to process (memory limit exceeded)',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_FILE_ACCESS_ERROR: {
        'message': 'File access error reading excel metadata: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_UNEXPECTED_ERROR: {
        'message': 'Unexpected error reading excel metadata: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.EXCEL_PATH_RESOLVED_STORAGE: {
        'message': 'Resolved Excel metadata path relative to storage: {}',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_PATH_RESOLUTION_FAILED: {
        'message': 'Storage path resolution failed ({}): {} - trying other strategies',
        'level': LogLevel.INFO,
    },
    LogCode.EXCEL_PATH_RESOLUTION_ERROR: {
        'message': 'Unexpected error resolving storage path ({}): {} - trying other strategies',
        'level': LogLevel.WARNING,
    },
    # Upload progress messages
    LogCode.DATA_FILE_STATUS: {
        'message': 'Data file status update',
        'level': None,
    },
    LogCode.DATA_UNIT_STATUS: {
        'message': 'Data unit status update',
        'level': None,
    },
    LogCode.UPLOADING_DATA_FILES: {
        'message': 'Uploading data files...',
        'level': None,
    },
    LogCode.GENERATING_DATA_UNITS: {
        'message': 'Generating data units...',
        'level': None,
    },
    LogCode.IMPORT_COMPLETED: {
        'message': 'Import completed.',
        'level': None,
    },
    LogCode.FILE_UPLOAD_FAILED: {
        'message': 'Failed to upload file: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.FILE_UPLOADED_SUCCESSFULLY: {
        'message': 'File uploaded successfully: {}',
        'level': LogLevel.SUCCESS,
    },
    LogCode.DATA_UNIT_BATCH_FAILED: {
        'message': 'Failed to create data units batch: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.DATA_UNIT_CREATED: {
        'message': 'Data unit created: {}',
        'level': LogLevel.SUCCESS,
    },
    LogCode.BATCH_PROCESSING_STARTED: {
        'message': 'Batch processing started: {} batches of {} items each',
        'level': LogLevel.INFO,
    },
    LogCode.DATA_UNITS_CREATED_FROM_FILES: {
        'message': 'Created {} data units from {} files',
        'level': LogLevel.INFO,
    },
    # Asset path messages
    LogCode.ASSET_PATH_ACCESS_ERROR: {
        'message': 'Error accessing path for {}: {}',
        'level': LogLevel.WARNING,
    },
    LogCode.ASSET_PATH_NOT_FOUND: {
        'message': 'Path does not exist for {}: {}',
        'level': LogLevel.WARNING,
    },
    # Step lifecycle messages
    LogCode.STEP_STARTING: {
        'message': 'Starting step: {}',
        'level': LogLevel.INFO,
    },
    LogCode.STEP_COMPLETED: {
        'message': 'Completed step: {}',
        'level': LogLevel.INFO,
    },
    LogCode.STEP_SKIPPED: {
        'message': 'Skipped step: {}',
        'level': LogLevel.INFO,
    },
    LogCode.STEP_ERROR: {
        'message': 'Error in step {}: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.STEP_FAILED: {
        'message': "Step '{}' failed: {}",
        'level': LogLevel.DANGER,
    },
    LogCode.STEP_EXCEPTION: {
        'message': "Exception in step '{}': {}",
        'level': LogLevel.DANGER,
    },
    LogCode.STEP_TRACEBACK: {
        'message': 'Traceback: {}',
        'level': LogLevel.DANGER,
    },
    # Rollback messages
    LogCode.ROLLBACK_STARTING: {
        'message': 'Starting rollback of {} executed steps',
        'level': LogLevel.WARNING,
    },
    LogCode.ROLLBACK_COMPLETED: {
        'message': 'Rollback completed',
        'level': LogLevel.INFO,
    },
    LogCode.STEP_ROLLBACK: {
        'message': 'Rolling back step: {}',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_ERROR: {
        'message': "Error rolling back step '{}': {}",
        'level': LogLevel.WARNING,
    },
    LogCode.ROLLBACK_INITIALIZATION: {
        'message': 'Rolling back initialization step',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_DATA_UNIT_GENERATION: {
        'message': 'Rolled back data unit generation',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_FILE_VALIDATION: {
        'message': 'Rolled back file validation',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_FILE_UPLOADS: {
        'message': 'Rolled back file uploads',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_COLLECTION_ANALYSIS: {
        'message': 'Rolled back collection analysis',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_FILE_ORGANIZATION: {
        'message': 'Rolled back file organization',
        'level': LogLevel.INFO,
    },
    LogCode.ROLLBACK_CLEANUP: {
        'message': 'Cleanup step rollback - no action needed',
        'level': LogLevel.INFO,
    },
    # Metadata processing messages
    LogCode.NO_METADATA_STRATEGY: {
        'message': 'No metadata strategy configured - skipping metadata processing',
        'level': LogLevel.INFO,
    },
    LogCode.METADATA_FILE_ATTRIBUTE_PROCESSING: {
        'message': 'Processing metadata for file attribute: {}',
        'level': LogLevel.INFO,
    },
    LogCode.METADATA_TEMP_FILE_CLEANUP: {
        'message': 'Cleaned up temporary Excel file: {}',
        'level': LogLevel.INFO,
    },
    LogCode.METADATA_TEMP_FILE_CLEANUP_FAILED: {
        'message': 'Failed to clean up temporary file {}: {}',
        'level': LogLevel.WARNING,
    },
    LogCode.METADATA_BASE64_DECODED: {
        'message': 'Decoded base64 Excel metadata to temporary file: {}',
        'level': LogLevel.INFO,
    },
    LogCode.METADATA_BASE64_DECODE_FAILED: {
        'message': 'Failed to decode base64 Excel metadata: {}',
        'level': LogLevel.DANGER,
    },
    # Multi-path mode messages
    LogCode.MULTI_PATH_MODE_ENABLED: {
        'message': 'Using multi-path mode with {} asset configurations',
        'level': LogLevel.INFO,
    },
    LogCode.OPTIONAL_SPEC_SKIPPED: {
        'message': 'Skipping optional spec {}: no asset path configured',
        'level': LogLevel.INFO,
    },
    LogCode.DISCOVERING_FILES_FOR_ASSET: {
        'message': 'Discovering files for {} (recursive={})',
        'level': LogLevel.INFO,
    },
    LogCode.NO_FILES_FOUND_FOR_ASSET: {
        'message': 'No files found for {}',
        'level': LogLevel.WARNING,
    },
    LogCode.FILES_FOUND_FOR_ASSET: {
        'message': 'Found {} files for {}',
        'level': LogLevel.INFO,
    },
    LogCode.ORGANIZING_FILES_MULTI_PATH: {
        'message': 'Organizing {} files across {} specs',
        'level': LogLevel.INFO,
    },
    LogCode.TYPE_DIRECTORIES_MULTI_PATH: {
        'message': 'Type directories: {}',
        'level': LogLevel.INFO,
    },
    # Cleanup messages
    LogCode.CLEANUP_WARNING: {
        'message': 'Cleanup warning: {}',
        'level': LogLevel.WARNING,
    },
    LogCode.CLEANUP_TEMP_DIR_SUCCESS: {
        'message': 'Cleaned up temporary directory: {}',
        'level': LogLevel.INFO,
    },
    LogCode.CLEANUP_TEMP_DIR_FAILED: {
        'message': 'Failed to cleanup temporary directory: {}',
        'level': LogLevel.WARNING,
    },
    # Workflow messages
    LogCode.WORKFLOW_STARTING: {
        'message': 'Starting upload workflow with {} steps: {}',
        'level': LogLevel.INFO,
    },
    LogCode.WORKFLOW_COMPLETED: {
        'message': 'Upload workflow completed successfully',
        'level': LogLevel.INFO,
    },
    LogCode.WORKFLOW_FAILED: {
        'message': 'Upload workflow failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.UPLOAD_WORKFLOW_FAILED: {
        'message': 'Upload workflow failed: {}',
        'level': LogLevel.DANGER,
    },
    LogCode.UNKNOWN_LOG_CODE: {
        'message': 'Unknown log code: {}',
        'level': LogLevel.WARNING,
    },
}
