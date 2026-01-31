"""Save files step for export workflow."""

from __future__ import annotations

from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.exporter import MetricsRecord
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class SaveFilesStep(BaseStep[ExportContext]):
    """Save converted data to files.

    This step:
    1. Saves original files (if enabled)
    2. Saves JSON data files
    3. Tracks metrics for success/failure

    Progress weight: 0.35 (35%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'save_files'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.35

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (35%)."""
        return 35

    def execute(self, context: ExportContext) -> StepResult:
        """Execute file saving step.

        Args:
            context: Export context with converted items.

        Returns:
            StepResult with save counts in data.
        """
        # Skip if no results
        if context.total_count == 0:
            return StepResult(
                success=True,
                data={'skipped': True, 'reason': 'No files to save'},
            )

        if not context.converted_items:
            return StepResult(
                success=True,
                data={'skipped': True, 'reason': 'No converted items to save'},
            )

        if context.exporter is None:
            return StepResult(
                success=False,
                error='Exporter not available.',
            )

        if context.unique_export_path is None:
            return StepResult(
                success=False,
                error='Export path not available. InitializeStep must run first.',
            )

        exporter = context.exporter
        total = context.total_count
        save_original = context.params.get('save_original_file', False)

        # Initialize error lists and metrics
        errors_json: list = []
        errors_original: list = []

        if save_original:
            original_metrics = MetricsRecord(stand_by=total, success=0, failed=0)
        else:
            original_metrics = MetricsRecord(stand_by=0, success=0, failed=0)
        data_metrics = MetricsRecord(stand_by=total, success=0, failed=0)

        # Initialize progress
        if save_original:
            context.runtime_ctx.logger.set_progress(0, total, category='original_file')
        context.runtime_ctx.logger.set_progress(0, total, category='data_file')

        context.logger.info('Saving files.')
        context.log_message(ExportLogMessageCode.EXPORT_SAVING_FILES, count=total)

        try:
            for no, final_data in enumerate(context.converted_items, start=1):
                exporter.process_file_saving(
                    final_data,
                    context.unique_export_path,
                    save_original,
                    errors_json,
                    errors_original,
                    original_metrics,
                    data_metrics,
                    no,
                )
        except Exception as e:
            return StepResult(
                success=False,
                error=f'File saving failed: {e}',
                data={
                    'exported_count': data_metrics.success,
                    'failed_count': data_metrics.failed,
                },
            )

        # Store results in context
        context.errors_json = errors_json
        context.errors_original = errors_original
        context.exported_count = data_metrics.success
        context.failed_count = data_metrics.failed

        context.logger.info(f'Saved {data_metrics.success} files, {data_metrics.failed} failed')
        if data_metrics.failed > 0:
            context.log_message(
                ExportLogMessageCode.EXPORT_FILES_SAVED_WITH_FAILURES,
                success=data_metrics.success,
                failed=data_metrics.failed,
            )
        else:
            context.log_message(ExportLogMessageCode.EXPORT_FILES_SAVED, count=data_metrics.success)

        return StepResult(
            success=True,
            data={
                'exported_count': data_metrics.success,
                'failed_count': data_metrics.failed,
                'original_success': original_metrics.success,
                'original_failed': original_metrics.failed,
            },
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Skip if no items to save."""
        return context.total_count == 0 or not context.converted_items

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback file saving (clear error lists and counts)."""
        context.errors_json = []
        context.errors_original = []
        context.exported_count = 0
        context.failed_count = 0
