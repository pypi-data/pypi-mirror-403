"""Convert data step for export workflow."""

from __future__ import annotations

from typing import Any

from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class ConvertDataStep(BaseStep[ExportContext]):
    """Convert export items through the data conversion pipeline.

    This step:
    1. Iterates through export items
    2. Applies before_convert -> convert_data -> after_convert
    3. Stores converted items for file saving

    Progress weight: 0.30 (30%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'convert_data'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.30

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (30%)."""
        return 30

    def execute(self, context: ExportContext) -> StepResult:
        """Execute data conversion step.

        Args:
            context: Export context with export items.

        Returns:
            StepResult with converted count in data.
        """
        # Skip if no results
        if context.total_count == 0:
            return StepResult(
                success=True,
                data={'skipped': True, 'reason': 'No results to convert'},
            )

        if context.export_items is None:
            return StepResult(
                success=False,
                error='Export items not available. PrepareExportStep must run first.',
            )

        if context.exporter is None:
            return StepResult(
                success=False,
                error='Exporter not available. Set exporter in context before running this step.',
            )

        exporter = context.exporter
        total = context.total_count
        converted_items: list[dict[str, Any]] = []

        context.logger.info('Converting dataset.')
        context.log_message(ExportLogMessageCode.EXPORT_CONVERTING, count=total)

        try:
            for no, export_item in enumerate(context.export_items, start=1):
                # Update progress
                context.runtime_ctx.logger.set_progress(min(no, total), total, category='dataset_conversion')

                # Apply conversion pipeline: before_convert -> convert_data -> after_convert
                final_data = exporter.process_data_conversion(export_item)
                converted_items.append(final_data)

        except Exception as e:
            return StepResult(
                success=False,
                error=f'Data conversion failed at item {len(converted_items) + 1}: {e}',
                data={'converted_count': len(converted_items)},
            )

        context.converted_items = converted_items
        context.logger.info(f'Converted {len(converted_items)} items')
        context.log_message(ExportLogMessageCode.EXPORT_CONVERTED, count=len(converted_items))

        return StepResult(
            success=True,
            data={'converted_count': len(converted_items)},
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Skip if no results to convert."""
        return context.total_count == 0

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback conversion step (clear converted items)."""
        context.converted_items = []
