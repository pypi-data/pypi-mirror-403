"""Prepare export step for export workflow."""

from __future__ import annotations

from itertools import tee

from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.steps import BaseStep, StepResult


class PrepareExportStep(BaseStep[ExportContext]):
    """Prepare export parameters and project configuration.

    This step:
    1. Builds export parameters
    2. Retrieves project configuration based on target type
    3. Creates export items generator

    Progress weight: 0.10 (10%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'prepare_export'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.10

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (10%)."""
        return 10

    def execute(self, context: ExportContext) -> StepResult:
        """Execute prepare export step.

        Args:
            context: Export context with params and fetched results.

        Returns:
            StepResult with export params in data.
        """
        # Skip if no results
        if context.total_count == 0:
            return StepResult(
                success=True,
                data={'skipped': True, 'reason': 'No results to export'},
            )

        # 1. Build export params
        export_params: dict = {
            'name': context.params.get('name'),
            'count': context.total_count,
            'save_original_file': context.params.get('save_original_file', False),
        }

        # 2. Merge extra params
        extra_params = context.params.get('extra_params')
        if extra_params:
            export_params.update(extra_params)

        # 3. Get project configuration based on target type
        target = context.params.get('target')

        try:
            if target == 'ground_truth':
                # Extract project_id from first result
                peek_iter, main_iter = tee(context.results)
                first_result = next(peek_iter)
                project_pk = first_result['project']
                export_params['project_id'] = project_pk

                project_info = context.client.get_project(project_pk)
                export_params['configuration'] = project_info.get('configuration', {})
                context.results = main_iter
                context.project_id = project_pk

            elif target in ['assignment', 'task']:
                project_pk = context.params.get('filter', {}).get('project')
                if project_pk:
                    project_info = context.client.get_project(project_pk)
                    export_params['configuration'] = project_info.get('configuration', {})
                    context.project_id = project_pk

        except StopIteration:
            export_params['configuration'] = {}
        except KeyError:
            export_params['configuration'] = {}
        except Exception as e:
            context.logger.warning(f'Failed to get project configuration: {e}')
            export_params['configuration'] = {}

        context.export_params = export_params
        context.configuration = export_params.get('configuration', {})

        # 4. Create export items generator
        if context.handler is None:
            return StepResult(
                success=False,
                error='Handler not available. FetchResultsStep must run first.',
            )

        context.export_items = context.handler.get_export_item(context.results)

        context.logger.info(f'Prepared export params for {context.total_count} items')

        return StepResult(
            success=True,
            data={
                'export_params': export_params,
                'project_id': context.project_id,
            },
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Skip if no results to export."""
        return context.total_count == 0

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback prepare step (clear export params)."""
        context.export_params = {}
        context.configuration = {}
        context.export_items = None
