"""Process metadata step for upload workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.strategies import (
    ExcelMetadataStrategy,
    MetadataStrategy,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.utils.excel import ExcelParsingError, ExcelSecurityError
from synapse_sdk.utils.storage import get_pathlib


class ProcessMetadataStep(BaseStep[UploadContext]):
    """Process metadata from Excel files.

    This step handles Excel metadata file processing:
    1. Resolves Excel file path (absolute, storage-relative, or cwd-relative)
    2. Extracts metadata using ExcelMetadataStrategy
    3. Validates the extracted metadata

    Progress weight: 0.10 (10%)
    """

    def __init__(self, metadata_strategy: MetadataStrategy | None = None):
        """Initialize with optional metadata strategy.

        Args:
            metadata_strategy: Strategy for metadata extraction.
                Defaults to ExcelMetadataStrategy.
        """
        self._metadata_strategy = metadata_strategy

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'process_metadata'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.10

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (10%)."""
        return 10

    def execute(self, context: UploadContext) -> StepResult:
        """Execute metadata processing step.

        Args:
            context: Upload context with params and storage.

        Returns:
            StepResult with extracted metadata in data.
        """
        context.set_progress(0, 1)
        strategy = self._metadata_strategy or ExcelMetadataStrategy()
        excel_metadata: dict[str, dict[str, Any]] = {}

        try:
            excel_metadata_path = context.params.get('excel_metadata_path')

            if excel_metadata_path:
                # Resolve and process specified Excel file
                excel_path = self._resolve_excel_path(excel_metadata_path, context)

                if not excel_path or not excel_path.exists():
                    context.log(
                        LogCode.EXCEL_FILE_NOT_FOUND_PATH.value,
                        {
                            'path': excel_metadata_path,
                        },
                    )
                    return StepResult(
                        success=True,
                        data={'metadata': {}},
                    )

                excel_metadata = strategy.extract(excel_path)
            else:
                # Look for default metadata files (single-path mode only)
                if context.pathlib_cwd:
                    excel_path = self._find_default_excel_file(context.pathlib_cwd)
                    if excel_path:
                        excel_metadata = strategy.extract(excel_path)
                else:
                    context.log(LogCode.NO_METADATA_STRATEGY.value, {})

            # Validate extracted metadata
            if excel_metadata:
                validation = strategy.validate(excel_metadata)
                if not validation.valid:
                    return StepResult(
                        success=False,
                        error=f'Metadata validation failed: {", ".join(validation.errors)}',
                    )

                context.log(
                    LogCode.EXCEL_METADATA_LOADED.value,
                    {
                        'file_count': len(excel_metadata),
                    },
                )
                context.log_message(UploadLogMessageCode.UPLOAD_METADATA_LOADED, count=len(excel_metadata))

            # Store in context
            context.excel_metadata = excel_metadata
            context.set_progress(1, 1)

            return StepResult(
                success=True,
                data={'metadata': excel_metadata},
                rollback_data={'metadata_processed': len(excel_metadata) > 0},
            )

        except ExcelSecurityError as e:
            context.log(LogCode.EXCEL_SECURITY_VIOLATION.value, {'error': str(e)})
            return StepResult(
                success=False,
                error=f'Excel security violation: {e}',
            )

        except ExcelParsingError as e:
            # If path was explicitly specified, it's an error
            if context.params.get('excel_metadata_path'):
                context.log(LogCode.EXCEL_PARSING_ERROR.value, {'error': str(e)})
                return StepResult(
                    success=False,
                    error=f'Excel parsing error: {e}',
                )
            # Otherwise, just skip with empty metadata
            context.log(LogCode.EXCEL_PARSING_ERROR.value, {'error': str(e)})
            return StepResult(
                success=True,
                data={'metadata': {}},
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f'Unexpected error processing metadata: {e}',
            )

    def can_skip(self, context: UploadContext) -> bool:
        """Skip if no metadata path and no default file found."""
        if context.params.get('excel_metadata_path'):
            return False
        if context.pathlib_cwd:
            default_path = self._find_default_excel_file(context.pathlib_cwd)
            return default_path is None
        return True

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback metadata processing."""
        context.excel_metadata = None

    def _resolve_excel_path(
        self,
        excel_path_str: str,
        context: UploadContext,
    ) -> Path | None:
        """Resolve Excel metadata path from string.

        Tries in order:
        1. Absolute path
        2. Relative to storage default path
        3. Relative to working directory (single-path mode)
        """
        # Try absolute path
        path = Path(excel_path_str)
        if path.exists() and path.is_file():
            return path

        # Try relative to storage
        if context.storage:
            try:
                storage_config = {
                    'provider': context.storage.provider,
                    'configuration': context.storage.configuration,
                }
                storage_path = get_pathlib(storage_config, excel_path_str)
                if storage_path.exists() and storage_path.is_file():
                    context.log(
                        LogCode.EXCEL_PATH_RESOLVED_STORAGE.value,
                        {
                            'path': str(storage_path),
                        },
                    )
                    return storage_path
            except (FileNotFoundError, PermissionError) as e:
                context.log(
                    LogCode.EXCEL_PATH_RESOLUTION_FAILED.value,
                    {
                        'error_type': type(e).__name__,
                        'error': str(e),
                    },
                )
            except Exception as e:
                context.log(
                    LogCode.EXCEL_PATH_RESOLUTION_ERROR.value,
                    {
                        'error_type': type(e).__name__,
                        'error': str(e),
                    },
                )

        # Try relative to cwd (single-path mode)
        if context.pathlib_cwd:
            path = context.pathlib_cwd / excel_path_str
            if path.exists() and path.is_file():
                return path

        return None

    def _find_default_excel_file(self, pathlib_cwd: Path) -> Path | None:
        """Find default Excel metadata file in working directory."""
        if not pathlib_cwd:
            return None

        # Check .xlsx first (more common)
        excel_path = pathlib_cwd / 'meta.xlsx'
        if excel_path.exists():
            return excel_path

        # Fallback to .xls
        excel_path = pathlib_cwd / 'meta.xls'
        if excel_path.exists():
            return excel_path

        return None
