"""Generate data units step for upload workflow."""

from __future__ import annotations

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.strategies import (
    BatchDataUnitStrategy,
    DataUnitStrategy,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult


class GenerateDataUnitsStep(BaseStep[UploadContext]):
    """Generate data units from uploaded files.

    This step:
    1. Takes uploaded file information
    2. Creates data units via the API
    3. Tracks progress and metrics
    4. Stores created data units in context

    Progress weight: 0.20 (20%)
    """

    def __init__(self, data_unit_strategy_class: type[DataUnitStrategy] | None = None):
        """Initialize with optional data unit strategy class.

        Args:
            data_unit_strategy_class: Strategy class for data unit generation.
                Defaults to BatchDataUnitStrategy.
        """
        self._data_unit_strategy_class = data_unit_strategy_class

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'generate_data_units'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.20

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (20%)."""
        return 20

    def execute(self, context: UploadContext) -> StepResult:
        """Execute data unit generation step.

        Args:
            context: Upload context with uploaded files.

        Returns:
            StepResult with generated data units in data.
        """
        # Create strategy instance with context
        strategy_class = self._data_unit_strategy_class or BatchDataUnitStrategy
        strategy = strategy_class(context)

        if not context.uploaded_files:
            context.log(LogCode.NO_DATA_UNITS_GENERATED.value, {})
            return StepResult(
                success=False,
                error='No uploaded files to generate data units from',
            )

        try:
            # Setup progress tracking
            uploaded_files_count = len(context.uploaded_files)
            context.set_progress(0, uploaded_files_count, category='generate_data_units')
            context.log(
                LogCode.GENERATING_DATA_UNITS.value,
                {
                    'count': uploaded_files_count,
                },
            )
            context.log_message(UploadLogMessageCode.UPLOAD_DATA_UNITS_CREATING, count=uploaded_files_count)

            # Initialize metrics
            initial_metrics = {
                'stand_by': uploaded_files_count,
                'success': 0,
                'failed': 0,
            }
            context.set_metrics(initial_metrics, category='data_units')

            # Get batch size from parameters
            batch_size = context.batch_size

            # Generate data units using strategy
            generated_data_units = strategy.generate(context.uploaded_files, batch_size)

            # Update context
            context.data_units = generated_data_units

            # Log data unit results
            for data_unit in generated_data_units:
                context.log(
                    LogCode.DATA_UNIT_CREATED.value,
                    {
                        'id': data_unit.get('id'),
                        'meta': data_unit.get('meta'),
                    },
                )

            # Update final metrics
            final_metrics = {
                'stand_by': 0,
                'success': len(generated_data_units),
                'failed': uploaded_files_count - len(generated_data_units),
            }
            context.set_metrics(final_metrics, category='data_units')

            # Handle success vs failure cases
            if generated_data_units:
                context.set_progress(
                    uploaded_files_count,
                    uploaded_files_count,
                    category='generate_data_units',
                )
                context.log(
                    LogCode.STEP_COMPLETED.value,
                    {
                        'step': self.name,
                        'data_units_count': len(generated_data_units),
                    },
                )
                failed_count = uploaded_files_count - len(generated_data_units)
                if failed_count > 0:
                    context.log_message(
                        UploadLogMessageCode.UPLOAD_DATA_UNITS_COMPLETED_WITH_FAILURES,
                        success=len(generated_data_units),
                        failed=failed_count,
                    )
                else:
                    context.log_message(
                        UploadLogMessageCode.UPLOAD_DATA_UNITS_COMPLETED,
                        count=len(generated_data_units),
                    )
                return StepResult(
                    success=True,
                    data={'generated_data_units': generated_data_units},
                    rollback_data={
                        'data_units_count': len(generated_data_units),
                        'batch_size': batch_size,
                    },
                )
            else:
                context.log(LogCode.NO_DATA_UNITS_GENERATED.value, {})
                return StepResult(
                    success=False,
                    error='No data units were successfully generated',
                )

        except Exception as e:
            context.log(
                LogCode.DATA_UNIT_BATCH_FAILED.value,
                {
                    'error': str(e),
                },
            )
            return StepResult(
                success=False,
                error=f'Data unit generation failed: {e}',
            )

    def can_skip(self, context: UploadContext) -> bool:
        """Data unit generation cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback data unit generation."""
        context.log(LogCode.ROLLBACK_DATA_UNIT_GENERATION.value, {})
        context.data_units = []
