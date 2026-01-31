"""Strategy interfaces for upload operations.

Provides abstract base classes defining contracts for:
    - FileDiscoveryStrategy: File discovery and organization
    - MetadataStrategy: Metadata extraction and validation
    - UploadStrategy: File upload operations
    - DataUnitStrategy: Data unit generation

These interfaces enable pluggable strategies for different upload scenarios.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from synapse_sdk.plugins.actions.upload.context import UploadContext


@dataclass
class ValidationResult:
    """Result of validation operations.

    Attributes:
        valid: Whether validation passed.
        errors: List of error messages if validation failed.

    Example:
        >>> result = ValidationResult(valid=True)
        >>> if result:
        ...     print("Validation passed")

        >>> result = ValidationResult(valid=False, errors=["File not found"])
        >>> if not result:
        ...     print(f"Errors: {result.errors}")
    """

    valid: bool = True
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Allow using ValidationResult in boolean context."""
        return self.valid


@dataclass
class UploadConfig:
    """Configuration for upload operations.

    Attributes:
        chunked_threshold_mb: File size threshold for chunked upload in MB.
        batch_size: Batch size for data unit creation.
        max_workers: Maximum concurrent upload workers.
        use_presigned: Whether to use presigned URL uploads.

    Example:
        >>> config = UploadConfig(chunked_threshold_mb=100, batch_size=10)
    """

    chunked_threshold_mb: int = 50
    batch_size: int = 1
    max_workers: int = 32
    use_presigned: bool = True


class ValidationStrategy(ABC):
    """Strategy interface for validation operations.

    Responsible for:
    - Validating action parameters
    - Validating organized files against specifications

    Example:
        >>> class DefaultValidationStrategy(ValidationStrategy):
        ...     def validate_params(self, params):
        ...         if not params.get('storage'):
        ...             return ValidationResult(valid=False, errors=["storage is required"])
        ...         return ValidationResult(valid=True)
        ...
        ...     def validate_files(self, files, specs):
        ...         # Validate files against specs
        ...         return ValidationResult(valid=True)
    """

    @abstractmethod
    def validate_params(self, params: dict[str, Any]) -> ValidationResult:
        """Validate action parameters.

        Args:
            params: Action parameters dictionary.

        Returns:
            ValidationResult indicating success or failure with errors.
        """
        pass

    @abstractmethod
    def validate_files(
        self,
        files: list[dict[str, Any]],
        specs: list[dict[str, Any]],
    ) -> ValidationResult:
        """Validate organized files against specifications.

        Args:
            files: List of organized file dictionaries.
            specs: File specifications from data collection.

        Returns:
            ValidationResult indicating success or failure with errors.
        """
        pass


class FileDiscoveryStrategy(ABC):
    """Strategy interface for file discovery and organization.

    Responsible for:
    - Discovering files in directories
    - Organizing files according to specifications
    - Matching files with metadata

    Example:
        >>> class MyDiscoveryStrategy(FileDiscoveryStrategy):
        ...     def discover(self, path, recursive):
        ...         return list(path.rglob('*') if recursive else path.glob('*'))
        ...
        ...     def organize(self, files, specs, metadata, type_dirs):
        ...         # Custom organization logic
        ...         return organized_files
    """

    @abstractmethod
    def discover(self, path: Path, recursive: bool = True) -> list[Path]:
        """Discover files in the given path.

        Args:
            path: Directory path to search.
            recursive: Whether to search recursively.

        Returns:
            List of discovered file paths.
        """
        pass

    @abstractmethod
    def organize(
        self,
        files: list[Path],
        specs: list[dict[str, Any]],
        metadata: dict[str, dict[str, Any]],
        type_dirs: dict[str, Path] | None = None,
    ) -> list[dict[str, Any]]:
        """Organize files according to specifications.

        Groups files by stem and matches with specifications to create
        data unit candidates.

        Args:
            files: List of discovered file paths.
            specs: File specifications from data collection.
            metadata: Metadata dictionary keyed by filename.
            type_dirs: Optional mapping of spec names to directories.

        Returns:
            List of organized file dictionaries with structure:
                {
                    'files': {spec_name: Path, ...},
                    'meta': {key: value, ...}
                }
        """
        pass


class MetadataStrategy(ABC):
    """Strategy interface for metadata extraction and processing.

    Responsible for:
    - Extracting metadata from sources (e.g., Excel files)
    - Validating metadata structure and content

    Example:
        >>> class ExcelStrategy(MetadataStrategy):
        ...     def extract(self, source_path):
        ...         # Load Excel and extract metadata
        ...         return {"file1.jpg": {"label": "cat"}}
        ...
        ...     def validate(self, metadata):
        ...         return ValidationResult(valid=True)
    """

    @abstractmethod
    def extract(self, source_path: Path) -> dict[str, dict[str, Any]]:
        """Extract metadata from source.

        Args:
            source_path: Path to metadata source (e.g., Excel file).

        Returns:
            Dictionary mapping filenames to their metadata dictionaries.

        Raises:
            ExcelSecurityError: If security constraints are violated.
            ExcelParsingError: If the source cannot be parsed.
        """
        pass

    @abstractmethod
    def validate(self, metadata: dict[str, dict[str, Any]]) -> ValidationResult:
        """Validate extracted metadata.

        Args:
            metadata: Metadata dictionary to validate.

        Returns:
            ValidationResult indicating success or failure with errors.
        """
        pass


class UploadStrategy(ABC):
    """Strategy interface for file upload operations.

    Responsible for:
    - Uploading files to storage
    - Handling presigned URL uploads
    - Managing chunked uploads for large files

    Example:
        >>> class SyncStrategy(UploadStrategy):
        ...     def __init__(self, context):
        ...         self.context = context
        ...
        ...     def upload(self, files, config):
        ...         # Upload logic
        ...         return uploaded_files
    """

    def __init__(self, context: UploadContext):
        """Initialize strategy with upload context.

        Args:
            context: UploadContext providing access to client, params, and state.
        """
        self.context = context

    @abstractmethod
    def upload(
        self,
        files: list[dict[str, Any]],
        config: UploadConfig,
    ) -> list[dict[str, Any]]:
        """Upload files to storage.

        Args:
            files: List of organized file dictionaries to upload.
            config: Upload configuration.

        Returns:
            List of uploaded file information dictionaries.
        """
        pass


class DataUnitStrategy(ABC):
    """Strategy interface for data unit generation.

    Responsible for:
    - Creating data units from uploaded files
    - Managing batch creation

    Example:
        >>> class BatchStrategy(DataUnitStrategy):
        ...     def __init__(self, context):
        ...         self.context = context
        ...
        ...     def generate(self, uploaded_files, batch_size):
        ...         # Create data units in batches
        ...         return data_units
    """

    def __init__(self, context: UploadContext):
        """Initialize strategy with upload context.

        Args:
            context: UploadContext providing access to client and state.
        """
        self.context = context

    @abstractmethod
    def generate(
        self,
        uploaded_files: list[dict[str, Any]],
        batch_size: int = 1,
    ) -> list[dict[str, Any]]:
        """Generate data units from uploaded files.

        Args:
            uploaded_files: List of uploaded file information.
            batch_size: Number of data units to create per batch.

        Returns:
            List of created data unit dictionaries.
        """
        pass


__all__ = [
    'ValidationResult',
    'UploadConfig',
    'ValidationStrategy',
    'FileDiscoveryStrategy',
    'MetadataStrategy',
    'UploadStrategy',
    'DataUnitStrategy',
]
