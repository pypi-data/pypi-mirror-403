"""Fetch results step for export workflow."""

from __future__ import annotations

from synapse_sdk.clients.exceptions import ClientError
from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.handlers import TargetHandlerFactory
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class FetchResultsStep(BaseStep[ExportContext]):
    """Fetch results from target source using handler.

    This step:
    1. Prepares filter parameters
    2. Gets appropriate target handler
    3. Retrieves data from the API

    Progress weight: 0.10 (10%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'fetch_results'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.10

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (10%)."""
        return 10

    def execute(self, context: ExportContext) -> StepResult:
        """Execute fetch results step.

        Args:
            context: Export context with params and client.

        Returns:
            StepResult with results count in data.
        """
        # 1. Prepare filters
        filters = {**context.params.get('filter', {})}

        # Get data_expand setting from config
        data_expand = context.config.get('data_expand', True)
        if data_expand:
            filters['expand'] = 'data'

        # 2. Get target handler
        target = context.params.get('target')
        if target is None:
            return StepResult(
                success=False,
                error='Target parameter is required',
            )

        try:
            handler = TargetHandlerFactory.get_handler(target)
            context.handler = handler
        except ValueError as e:
            return StepResult(
                success=False,
                error=str(e),
            )

        # 3. Fetch results
        try:
            results, count = handler.get_results(context.client, filters)
            context.results = results
            context.total_count = count
        except ClientError as e:
            return StepResult(
                success=False,
                error=f'Failed to fetch results: {e}',
            )

        if count == 0:
            context.logger.info('No results found for export')
            context.log_message(ExportLogMessageCode.EXPORT_NO_RESULTS)
            return StepResult(
                success=True,
                data={'count': 0, 'message': 'No results found'},
            )

        context.logger.info(f'Retrieved {count} results for export')
        context.log_message(ExportLogMessageCode.EXPORT_RESULTS_FETCHED, count=count)

        return StepResult(
            success=True,
            data={'count': count},
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Fetch step cannot be skipped."""
        return False

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback fetch step (clear results)."""
        context.results = None
        context.total_count = 0
        context.handler = None
