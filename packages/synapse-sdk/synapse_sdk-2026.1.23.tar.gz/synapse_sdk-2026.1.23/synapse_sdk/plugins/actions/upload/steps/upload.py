"""Upload files step for upload workflow."""

from __future__ import annotations

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.strategies import (
    SyncUploadStrategy,
    UploadConfig,
    UploadStrategy,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult


class UploadFilesStep(BaseStep[UploadContext]):
    """Upload organized files using upload strategy.

    This step:
    1. Prepares upload configuration from context parameters
    2. Uploads files using the configured strategy (presigned URLs or direct)
    3. Tracks upload progress and metrics
    4. Stores uploaded file information in context

    Progress weight: 0.30 (30%)
    """

    def __init__(self, upload_strategy_class: type[UploadStrategy] | None = None):
        """Initialize with optional upload strategy class.

        Args:
            upload_strategy_class: Strategy class for file upload.
                Defaults to SyncUploadStrategy.
        """
        self._upload_strategy_class = upload_strategy_class

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'upload_files'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.30

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (30%)."""
        return 30

    def execute(self, context: UploadContext) -> StepResult:
        """Execute file upload step.

        Args:
            context: Upload context with organized files.

        Returns:
            StepResult with uploaded files in data.
        """
        # Create strategy instance with context
        strategy_class = self._upload_strategy_class or SyncUploadStrategy
        strategy = strategy_class(context)

        if not context.organized_files:
            context.log(LogCode.NO_FILES_UPLOADED.value, {})
            return StepResult(
                success=False,
                error='No organized files to upload',
            )

        try:
            # Setup progress tracking
            organized_files_count = len(context.organized_files)
            context.set_progress(0, organized_files_count, category='upload_data_files')
            context.log(
                LogCode.UPLOADING_DATA_FILES.value,
                {
                    'count': organized_files_count,
                },
            )
            context.log_message(UploadLogMessageCode.UPLOAD_FILES_UPLOADING, count=organized_files_count)

            # Initialize metrics
            initial_metrics = {
                'stand_by': organized_files_count,
                'success': 0,
                'failed': 0,
            }
            context.set_metrics(initial_metrics, category='data_files')

            # Create upload configuration
            upload_config = UploadConfig(
                chunked_threshold_mb=context.params.get('max_file_size_mb', 50),
                batch_size=context.params.get('upload_batch_size', 1),
                use_presigned=context.params.get('use_presigned', True),
            )

            # Execute upload using strategy
            uploaded_files = strategy.upload(context.organized_files, upload_config)

            # Update context
            context.uploaded_files = uploaded_files

            # Log upload results
            for uploaded_file in uploaded_files:
                context.log(
                    LogCode.FILE_UPLOADED_SUCCESSFULLY.value,
                    {
                        'file': uploaded_file.get('name', 'unknown'),
                    },
                )

            # Update final metrics
            final_metrics = {
                'stand_by': 0,
                'success': len(uploaded_files),
                'failed': organized_files_count - len(uploaded_files),
            }
            context.set_metrics(final_metrics, category='data_files')

            # Handle success vs failure cases
            if uploaded_files:
                context.set_progress(
                    organized_files_count,
                    organized_files_count,
                    category='upload_data_files',
                )
                context.log(
                    LogCode.STEP_COMPLETED.value,
                    {
                        'step': self.name,
                        'uploaded_count': len(uploaded_files),
                    },
                )
                failed_count = organized_files_count - len(uploaded_files)
                if failed_count > 0:
                    context.log_message(
                        UploadLogMessageCode.UPLOAD_FILES_COMPLETED_WITH_FAILURES,
                        success=len(uploaded_files),
                        failed=failed_count,
                    )
                else:
                    context.log_message(
                        UploadLogMessageCode.UPLOAD_FILES_COMPLETED,
                        success=len(uploaded_files),
                    )
                return StepResult(
                    success=True,
                    data={'uploaded_files': uploaded_files},
                    rollback_data={'uploaded_files_count': len(uploaded_files)},
                )
            else:
                context.log(LogCode.NO_FILES_UPLOADED.value, {})
                return StepResult(
                    success=False,
                    error='No files were successfully uploaded',
                )

        except Exception as e:
            context.log(
                LogCode.FILE_UPLOAD_FAILED.value,
                {
                    'error': str(e),
                },
            )
            return StepResult(
                success=False,
                error=f'File upload failed: {e}',
            )

    def can_skip(self, context: UploadContext) -> bool:
        """File upload cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback file upload."""
        context.log(LogCode.ROLLBACK_FILE_UPLOADS.value, {})
        context.uploaded_files = []
