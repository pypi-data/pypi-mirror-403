"""Exception classes for upload action operations.

Provides specialized exceptions for:
    - Excel file processing errors
    - File upload errors
    - Validation errors
"""

from __future__ import annotations

# Re-export Excel exceptions from utils for backward compatibility
from synapse_sdk.utils.excel import ExcelParsingError, ExcelSecurityError

__all__ = [
    'ExcelParsingError',
    'ExcelSecurityError',
    'UploadError',
    'FileUploadError',
    'FileValidationError',
    'FileProcessingError',
]


class UploadError(Exception):
    """Base exception for upload operations.

    All upload-specific exceptions inherit from this class,
    enabling broad exception handling for upload workflows.

    Example:
        >>> try:
        ...     upload_files(files)
        ... except UploadError as e:
        ...     log_error(f"Upload failed: {e}")
    """

    pass


class FileUploadError(UploadError):
    """Exception raised when file upload operations fail.

    This exception is raised when a file cannot be uploaded due to
    network issues, storage errors, or other upload-related problems.

    Attributes:
        message: Human-readable error description
        file_path: Path to the file that failed to upload (optional)
        storage_id: ID of the target storage (optional)
        original_error: The underlying exception (optional)

    Example:
        >>> try:
        ...     upload_to_storage(file, storage_id)
        ... except ConnectionError as e:
        ...     raise FileUploadError(
        ...         f"Failed to upload file: {e}",
        ...         file_path=file,
        ...         storage_id=storage_id,
        ...         original_error=e
        ...     )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        storage_id: int | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.storage_id = storage_id
        self.original_error = original_error


class FileValidationError(UploadError):
    """Exception raised when file validation fails.

    This exception is raised when files do not meet the expected
    specifications or requirements for upload.

    Attributes:
        message: Human-readable error description
        file_path: Path to the problematic file (optional)
        validation_type: Type of validation that failed (optional)

    Example:
        >>> if not matches_spec(file, spec):
        ...     raise FileValidationError(
        ...         f"File does not match specification: {spec.name}",
        ...         file_path=file,
        ...         validation_type="spec_mismatch"
        ...     )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        validation_type: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.validation_type = validation_type


class FileProcessingError(UploadError):
    """Exception raised when file processing fails.

    This exception is raised when files cannot be processed
    during the upload workflow (e.g., organization, grouping).

    Attributes:
        message: Human-readable error description
        file_path: Path to the problematic file (optional)
        step: The processing step that failed (optional)
        original_error: The underlying exception (optional)

    Example:
        >>> try:
        ...     organize_files(files)
        ... except OSError as e:
        ...     raise FileProcessingError(
        ...         f"Failed to organize files: {e}",
        ...         step="organize",
        ...         original_error=e
        ...     )
    """

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        step: str | None = None,
        original_error: Exception | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.file_path = file_path
        self.step = step
        self.original_error = original_error
