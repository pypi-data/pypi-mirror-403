"""Finalize step for export workflow."""

from __future__ import annotations

from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class FinalizeStep(BaseStep[ExportContext]):
    """Finalize export workflow and save additional files.

    This step:
    1. Calls exporter's additional_file_saving for custom post-processing
    2. Saves error list file if there are errors
    3. Sets final output path

    Progress weight: 0.10 (10%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.10

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (10%)."""
        return 10

    def execute(self, context: ExportContext) -> StepResult:
        """Execute finalization step.

        Args:
            context: Export context with saved files.

        Returns:
            StepResult with export path in data.
        """
        # Handle case where no results were exported
        if context.total_count == 0:
            context.output_path = str(context.path_root) if context.path_root else None
            return StepResult(
                success=True,
                data={
                    'export_path': context.output_path,
                    'exported_count': 0,
                },
            )

        if context.unique_export_path is None:
            return StepResult(
                success=False,
                error='Export path not available.',
            )

        # 1. Call additional_file_saving if exporter is available
        if context.exporter is not None:
            try:
                context.exporter.additional_file_saving(context.unique_export_path)
            except Exception as e:
                context.logger.warning(f'Additional file saving failed: {e}')

            # 2. Save error list
            try:
                context.exporter._save_error_list(
                    context.unique_export_path,
                    context.errors_json,
                    context.errors_original,
                )
            except Exception as e:
                context.logger.warning(f'Error list saving failed: {e}')

        # 3. Set final output path
        context.output_path = str(context.path_root) if context.path_root else None

        context.logger.info(f'Export completed at {context.unique_export_path}')
        if context.failed_count > 0:
            context.log_message(
                ExportLogMessageCode.EXPORT_COMPLETED_WITH_FAILURES,
                exported=context.exported_count,
                failed=context.failed_count,
            )
        else:
            context.log_message(
                ExportLogMessageCode.EXPORT_COMPLETED,
                count=context.exported_count,
            )

        return StepResult(
            success=True,
            data={
                'export_path': context.output_path,
                'unique_export_path': str(context.unique_export_path),
                'exported_count': context.exported_count,
                'failed_count': context.failed_count,
            },
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Finalize step should always run."""
        return False

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback finalization (nothing to rollback)."""
        context.logger.info('Finalize step rolled back')
