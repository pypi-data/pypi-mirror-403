"""Cleanup step for upload workflow."""

from __future__ import annotations

import shutil
from pathlib import Path

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class CleanupStep(BaseStep[UploadContext]):
    """Cleanup temporary resources and finalize workflow.

    This step:
    1. Cleans up any temporary directories/files
    2. Logs workflow completion
    3. Reports final statistics

    Progress weight: 0.05 (5%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'cleanup'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.05

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (5%)."""
        return 5

    def execute(self, context: UploadContext) -> StepResult:
        """Execute cleanup step.

        Args:
            context: Upload context with workflow state.

        Returns:
            StepResult with cleanup status in data.
        """
        context.set_progress(0, 1)
        try:
            # Cleanup temporary directory if configured
            if context.params.get('cleanup_temp', False):
                temp_path = context.params.get('temp_path')
                if temp_path:
                    self._cleanup_temp_directory(context, Path(temp_path))

            # Log completion statistics
            stats = {
                'organized_files': len(context.organized_files),
                'uploaded_files': len(context.uploaded_files),
                'data_units': len(context.data_units),
            }

            context.log(LogCode.IMPORT_COMPLETED.value, stats)
            context.log_message(
                UploadLogMessageCode.UPLOAD_COMPLETED,
                files=stats['uploaded_files'],
                data_units=stats['data_units'],
            )
            context.set_progress(1, 1)

            return StepResult(
                success=True,
                data={
                    'cleanup_completed': True,
                    'statistics': stats,
                },
                rollback_data={'temp_cleaned': True},
            )

        except Exception as e:
            # Cleanup failures shouldn't stop the workflow
            context.log(
                LogCode.CLEANUP_WARNING.value,
                {
                    'error': str(e),
                },
            )
            return StepResult(
                success=True,
                data={'cleanup_completed': False},
                rollback_data={'cleanup_error': str(e)},
            )

    def can_skip(self, context: UploadContext) -> bool:
        """Cleanup step can be skipped if disabled."""
        return context.params.get('skip_cleanup', False)

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback cleanup (nothing to rollback for cleanup)."""
        context.log(LogCode.ROLLBACK_CLEANUP.value, {})

    def _cleanup_temp_directory(
        self,
        context: UploadContext,
        temp_path: Path,
    ) -> None:
        """Clean up temporary directory.

        Args:
            context: Upload context for logging.
            temp_path: Path to temporary directory.
        """
        if not temp_path.exists():
            return

        try:
            shutil.rmtree(temp_path, ignore_errors=True)
            context.log(
                LogCode.CLEANUP_TEMP_DIR_SUCCESS.value,
                {
                    'path': str(temp_path),
                },
            )
        except Exception as e:
            context.log(
                LogCode.CLEANUP_TEMP_DIR_FAILED.value,
                {
                    'path': str(temp_path),
                    'error': str(e),
                },
            )
