"""Validate files step for upload workflow."""

from __future__ import annotations

from typing import Any

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.strategies import (
    DefaultValidationStrategy,
    ValidationStrategy,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult


class ValidateFilesStep(BaseStep[UploadContext]):
    """Validate organized files against specifications.

    This step uses a validation strategy to:
    1. Filter files by allowed extensions (if configured via get_allowed_extensions())
    2. Validate that required file types are present
    3. Validate file extensions match specifications
    4. Validate file integrity (if configured)

    File Extension Filtering:
        If context.allowed_extensions is set (from action's get_allowed_extensions()),
        files are first filtered to only include those with allowed extensions.
        This happens before spec validation, allowing plugins to restrict input formats.

    Progress weight: 0.10 (10%)
    """

    def __init__(self, validation_strategy: ValidationStrategy | None = None):
        """Initialize with optional validation strategy.

        Args:
            validation_strategy: Strategy for file validation.
                Defaults to DefaultValidationStrategy.
        """
        self._validation_strategy = validation_strategy

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'validate_files'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.10

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (10%)."""
        return 10

    def execute(self, context: UploadContext) -> StepResult:
        """Execute file validation step.

        Args:
            context: Upload context with organized files and specifications.

        Returns:
            StepResult with validation status in data.
        """
        strategy = self._validation_strategy or DefaultValidationStrategy()

        if not context.organized_files:
            context.log(LogCode.NO_FILES_FOUND_WARNING.value, {})
            return StepResult(
                success=False,
                error='No organized files to validate',
            )

        # Get file specifications from data_collection
        file_specifications = self._get_file_specifications(context)
        if not file_specifications:
            return StepResult(
                success=False,
                error='File specifications not available',
            )

        try:
            # Set initial progress
            context.set_progress(0, 1)

            # Filter files by allowed extensions (if configured)
            if context.allowed_extensions:
                original_count = len(context.organized_files)
                context.organized_files = self._filter_by_allowed_extensions(
                    context.organized_files,
                    file_specifications,
                    context.allowed_extensions,
                    context,
                )
                filtered_count = original_count - len(context.organized_files)
                if filtered_count > 0:
                    context.log(
                        LogCode.FILES_FILTERED_BY_EXTENSION.value,
                        {
                            'filtered_count': filtered_count,
                            'remaining_count': len(context.organized_files),
                        },
                    )

                if not context.organized_files:
                    return StepResult(
                        success=False,
                        error='No files remaining after extension filtering',
                    )

            # Validate organized files against specifications
            validation_result = strategy.validate_files(
                context.organized_files,
                file_specifications,
            )

            if not validation_result.valid:
                context.log(
                    LogCode.VALIDATION_FAILED.value,
                    {
                        'errors': validation_result.errors,
                    },
                )
                error_msg = f'File validation failed: {", ".join(validation_result.errors)}'
                context.log_message(error_msg, 'danger')
                return StepResult(
                    success=False,
                    error=error_msg,
                )

            # Complete progress
            context.set_progress(1, 1)

            context.log(
                LogCode.STEP_COMPLETED.value,
                {
                    'step': self.name,
                    'files_count': len(context.organized_files),
                },
            )
            context.log_message(UploadLogMessageCode.UPLOAD_VALIDATION_PASSED, count=len(context.organized_files))

            return StepResult(
                success=True,
                data={'validation_passed': True},
                rollback_data={'validated_files_count': len(context.organized_files)},
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f'File validation failed: {e}',
            )

    def _get_file_specifications(self, context: UploadContext) -> list[dict[str, Any]]:
        """Get file specifications from context."""
        if context.data_collection:
            return context.data_collection.get('file_specifications', [])
        return []

    def _filter_by_allowed_extensions(
        self,
        organized_files: list[dict[str, Any]],
        file_specifications: list[dict[str, Any]],
        allowed_extensions: dict[str, list[str]],
        context: UploadContext,
    ) -> list[dict[str, Any]]:
        """Filter organized files by allowed extensions.

        Filters files based on their file_type and extension according to
        the allowed_extensions configuration from the action.

        Args:
            organized_files: List of organized file dictionaries.
            file_specifications: File specifications from data collection.
            allowed_extensions: Mapping of file_type to allowed extensions.
            context: Upload context for logging.

        Returns:
            Filtered list containing only files with allowed extensions.
        """
        if not organized_files or not file_specifications:
            return organized_files

        # Build spec lookup for file_type
        spec_lookup = {spec['name']: spec for spec in file_specifications}
        valid_files: list[dict[str, Any]] = []

        for file_group in organized_files:
            files_dict = file_group.get('files', {})
            valid_files_dict: dict[str, Any] = {}

            for spec_name, file_path in files_dict.items():
                if spec_name not in spec_lookup:
                    valid_files_dict[spec_name] = file_path
                    continue

                spec = spec_lookup[spec_name]
                file_type = spec.get('file_type', '')

                # If this file_type is not in allowed_extensions, keep the file
                if file_type not in allowed_extensions:
                    valid_files_dict[spec_name] = file_path
                    continue

                # Handle file path (could be Path or list)
                actual_path = file_path
                if isinstance(file_path, list):
                    actual_path = file_path[0] if file_path else None

                if actual_path is None:
                    continue

                # Check extension
                file_ext = actual_path.suffix.lower()
                allowed_exts = [ext.lower() for ext in allowed_extensions[file_type]]

                if file_ext in allowed_exts:
                    valid_files_dict[spec_name] = file_path

            # Include group if it has valid files
            if valid_files_dict:
                # Check if all required specs are present
                required_specs = [spec['name'] for spec in file_specifications if spec.get('is_required', False)]
                has_all_required = all(spec_name in valid_files_dict for spec_name in required_specs)

                if has_all_required:
                    valid_group = {**file_group, 'files': valid_files_dict}
                    valid_files.append(valid_group)

        return valid_files

    def can_skip(self, context: UploadContext) -> bool:
        """File validation cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback file validation."""
        context.log(LogCode.ROLLBACK_FILE_VALIDATION.value, {})
