"""Export action base class with optional step support."""

from __future__ import annotations

from itertools import tee
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel
from pydantic_core import PydanticCustomError

from synapse_sdk.clients.exceptions import ClientError
from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.handlers import ExportTargetHandler, TargetHandlerFactory
from synapse_sdk.plugins.actions.export.models import ExportParams
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry
from synapse_sdk.utils.storage import get_pathlib

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from upath import UPath

    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode


class BaseExportAction(BaseAction[P]):
    """Base class for export actions.

    Provides helper methods for export workflows.
    Override get_filtered_results() for your specific target type.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple workflows
    2. Step-based: Override setup_steps() to register workflow steps

    If setup_steps() registers any steps, the step-based workflow
    takes precedence and execute() is not called directly.

    Attributes:
        category: Plugin category (defaults to EXPORT).

    Example (simple execute):
        >>> class MyExportAction(BaseExportAction[MyParams]):
        ...     action_name = 'export'
        ...     params_model = MyParams
        ...
        ...     def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
        ...         return self.client.get_assignments(filters)
        ...
        ...     def execute(self) -> dict[str, Any]:
        ...         results, count = self.get_filtered_results(self.params.filter)
        ...         self.set_progress(0, count, self.progress.DATASET_CONVERSION)
        ...         for i, item in enumerate(results, 1):
        ...             # Process and export item
        ...             self.set_progress(i, count, self.progress.DATASET_CONVERSION)
        ...         return {'exported': count}

    Example (step-based):
        >>> class MyExportAction(BaseExportAction[MyParams]):
        ...     def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        ...         registry.register(FetchResultsStep())
        ...         registry.register(ProcessStep())
        ...         registry.register(FinalizeStep())
    """

    category = PluginCategory.EXPORT

    @classmethod
    def get_log_message_code_class(cls) -> type[ExportLogMessageCode]:
        from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode

        return ExportLogMessageCode

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError(
                'No client in context. Either provide a client via RuntimeContext or override get_filtered_results().'
            )
        return self.ctx.client

    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for your export workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
            ...     registry.register(FetchResultsStep())
            ...     registry.register(ProcessStep())
            ...     registry.register(FinalizeStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> ExportContext:
        """Create export context for step-based workflow.

        Override to customize context creation or add additional state.
        The context is populated with params and runtime context, along with
        project_id extracted from filter parameters.

        Returns:
            ExportContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)

        # Extract project_id from filter if available
        project_id = None
        if hasattr(self.params, 'filter') and isinstance(self.params.filter, dict):
            project_id = self.params.filter.get('project')

        return ExportContext(
            runtime_ctx=self.ctx,
            params=params_dict,
            project_id=project_id,
        )

    def run(self) -> Any:
        """Run the action, using steps if registered.

        This method is called by executors. It checks if steps are
        registered and uses step-based execution if so.

        Returns:
            Action result (dict or any return type).
        """
        # Check if steps are registered
        registry: StepRegistry[ExportContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[ExportContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            result['exported_count'] = context.exported_count
            result['failed_count'] = context.failed_count
            result['total_count'] = context.total_count
            if context.output_path:
                result['output_path'] = context.output_path

            return result

        # Simple execute mode
        return self.execute()

    def get_filtered_results(self, filters: dict[str, Any]) -> tuple[Any, int]:
        """Fetch filtered results for export.

        Override this method for your specific target type
        (assignments, ground_truth, tasks, or custom).

        Args:
            filters: Filter criteria dict.

        Returns:
            Tuple of (results_iterator, total_count).

        Raises:
            NotImplementedError: Must be overridden by subclass.

        Example:
            >>> # Override for assignments:
            >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
            ...     return self.client.get_assignments(filters)
            >>>
            >>> # Override for ground truth:
            >>> def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
            ...     return self.client.get_ground_truth(filters)
        """
        raise NotImplementedError(
            'Override get_filtered_results() for your target type. Example: return self.client.get_assignments(filters)'
        )

    def get_storage(self, storage_id: int) -> Any:
        """Fetch storage configuration from backend.

        Default implementation uses client.get_storage().

        Args:
            storage_id: Storage ID to fetch.

        Returns:
            Storage configuration object.

        Raises:
            RuntimeError: If no client in context.

        Example:
            >>> storage = self.get_storage(self.params.storage)
            >>> storage_config = storage.model_dump()
        """
        return self.client.get_storage(storage_id)

    def get_project(self, project_id: int) -> dict[str, Any]:
        """Fetch project information from backend.

        Args:
            project_id: Project ID to fetch.

        Returns:
            Project information dictionary.

        Raises:
            RuntimeError: If no client in context.
        """
        return self.client.get_project(project_id)

    def get_project_configuration(self, project_id: int) -> dict[str, Any]:
        """Get project configuration from backend.

        Args:
            project_id: Project ID.

        Returns:
            Project configuration dict.

        Raises:
            RuntimeError: If no client in context.
        """
        project_info = self.get_project(project_id)
        return project_info.get('configuration', {})


class ExportAction(BaseExportAction['ExportParams']):
    """Main export action for processing and exporting data from various targets.

    .. deprecated::
        Use :class:`DefaultExportAction` for step-based workflows.
        This class uses a simple execute() method without step orchestration.

    Handles export operations including target validation, data retrieval,
    and file generation. Supports export from assignment, ground_truth, and task
    targets with comprehensive progress tracking and error handling.

    Features:
        - Multiple target source support (assignment, ground_truth, task)
        - Filter validation and data retrieval
        - Original file and data file export options
        - Progress tracking with detailed metrics
        - Project configuration handling

    Attributes:
        action_name: Action identifier ('export').
        category: EXPORT category.
        params_model: ExportParams for parameter validation.

    Example:
        >>> action = ExportAction(
        ...     params={
        ...         'name': 'Assignment Export',
        ...         'storage': 1,
        ...         'path': '/exports/assignments',
        ...         'target': 'assignment',
        ...         'filter': {'project': 123}
        ...     },
        ...     ctx=runtime_context
        ... )
        >>> result = action.run()
    """

    action_name = 'export'
    params_model = ExportParams

    def get_filtered_results(self, filters: dict[str, Any], handler: ExportTargetHandler) -> tuple[Any, int]:
        """Get filtered target results.

        Retrieves data from the specified target using the provided filters
        through the appropriate target handler.

        Args:
            filters: Filter criteria to apply.
            handler: Target-specific handler.

        Returns:
            Tuple of (results, count) where results is the data and count is total.

        Raises:
            PydanticCustomError: If data retrieval fails.
        """
        try:
            result_list = handler.get_results(self.client, filters)
            results = result_list[0]
            count = result_list[1]
        except ClientError as e:
            raise PydanticCustomError('client_error', f'Unable to get dataset: {e}') from e
        return results, count

    def execute(self) -> dict[str, Any]:
        """Execute the export process.

        Main entry point for export operations. Handles parameter preparation,
        target handler selection, data retrieval, and export execution.

        Returns:
            Export results from the exporter.
        """
        # Get expand setting from config, default to True (expand data)
        filters = {**self.params.filter}
        config = getattr(self, 'config', {}) or {}
        data_expand = config.get('data_expand', True)
        if data_expand:
            filters['expand'] = 'data'

        target = self.params.target
        handler = TargetHandlerFactory.get_handler(target)

        # FETCH progress
        self.set_progress(0, 1, step='fetch')
        results, count = self.get_filtered_results(filters, handler)
        self.set_progress(1, 1, step='fetch')

        if count == 0:
            self.log('export_info', {'message': 'No results found for export'})
            return {'exported_count': 0}

        self.log('export_info', {'message': f'Retrieved {count} results for export', 'count': count})

        # Build export params
        export_params: dict[str, Any] = {
            'name': self.params.name,
            'count': count,
            'save_original_file': self.params.save_original_file,
        }

        if self.params.extra_params:
            export_params.update(self.params.extra_params)

        # For 'ground_truth' target, retrieve project info from first result
        if target == 'ground_truth':
            try:
                peek_iter, main_iter = tee(results)
                first_result = next(peek_iter)
                project_pk = first_result['project']
                export_params['project_id'] = project_pk
                export_params['configuration'] = self.get_project_configuration(project_pk)
                results = main_iter
            except (StopIteration, KeyError):
                export_params['configuration'] = {}
        # For 'assignment' and 'task' targets, retrieve project from filter
        elif target in ['assignment', 'task'] and 'project' in self.params.filter:
            project_pk = self.params.filter['project']
            export_params['configuration'] = self.get_project_configuration(project_pk)

        # Get export items from handler
        export_items = handler.get_export_item(results)

        # Get storage and path
        storage = self.client.get_storage(self.params.storage)
        storage_config = storage.model_dump()
        pathlib_cwd: Path | UPath = get_pathlib(storage_config, self.params.path)

        # Get entrypoint (exporter class) and execute
        exporter = self.entrypoint(self.ctx, export_items, pathlib_cwd, **export_params)

        try:
            result = exporter.export()
            self.log('export_completed', {'message': 'Export completed successfully'})
            return result
        except Exception as e:
            self.log('export_failed', {'message': f'Export failed: {e}', 'error': str(e)})
            raise


class DefaultExportAction(BaseExportAction['ExportParams']):
    """Default export action with 6-step workflow.

    Provides a complete export workflow with all standard steps:
    1. InitializeStep (5%) - Storage/path setup, output directory creation
    2. FetchResultsStep (10%) - Target handler data retrieval
    3. PrepareExportStep (10%) - Export params build, project config retrieval
    4. ConvertDataStep (30%) - Data conversion (before_convert -> convert_data -> after_convert)
    5. SaveFilesStep (35%) - File saving (original_file + data_file)
    6. FinalizeStep (10%) - Additional file saving, error list, cleanup

    Use this class when you need the standard export workflow with step-based
    orchestration. For simple exports without step orchestration, use ExportAction.

    Attributes:
        action_name: Action identifier ('export').
        category: EXPORT category.
        params_model: ExportParams for parameter validation.

    Example:
        >>> from synapse_sdk.plugins.actions.export import (
        ...     DefaultExportAction,
        ...     ExportParams,
        ... )
        >>>
        >>> class MyExportAction(DefaultExportAction):
        ...     action_name = 'my_export'
        >>>
        >>> # All 6 steps are automatically registered
    """

    action_name = 'export'
    params_model = ExportParams

    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        """Register the standard 6-step export workflow.

        Steps are registered in execution order with their default
        configurations.

        Args:
            registry: StepRegistry to register steps with.
        """
        from synapse_sdk.plugins.actions.export.steps import (
            ConvertDataStep,
            FetchResultsStep,
            FinalizeStep,
            InitializeStep,
            PrepareExportStep,
            SaveFilesStep,
        )

        # 1. Initialize - Storage/path setup (5%)
        registry.register(InitializeStep())

        # 2. Fetch Results - Data retrieval (10%)
        registry.register(FetchResultsStep())

        # 3. Prepare Export - Export params build (10%)
        registry.register(PrepareExportStep())

        # 4. Convert Data - Data conversion (30%)
        registry.register(ConvertDataStep())

        # 5. Save Files - File saving (35%)
        registry.register(SaveFilesStep())

        # 6. Finalize - Cleanup (10%)
        registry.register(FinalizeStep())

    def create_context(self) -> ExportContext:
        """Create export context with exporter instance.

        Extends base create_context to also set up the exporter instance
        needed by ConvertDataStep and SaveFilesStep.

        Returns:
            ExportContext instance with params, runtime context, and exporter.
        """
        context = super().create_context()

        # Set action config
        context.config = getattr(self, 'config', {}) or {}

        return context

    def run(self) -> Any:
        """Run the export workflow with step orchestration.

        Creates exporter after context setup but before step execution,
        as steps need access to the exporter for data conversion and file saving.

        Returns:
            Export result dict with counts and paths.
        """
        # Check if steps are registered
        registry: StepRegistry[ExportContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()

            # Run orchestrator
            orchestrator: Orchestrator[ExportContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )

            # Execute first two steps to get path and export items
            # Then create exporter before remaining steps
            result = self._execute_with_exporter(orchestrator, context)

            return result

        # Fallback to simple execute mode
        return self.execute()

    def _execute_with_exporter(
        self, orchestrator: Orchestrator[ExportContext], context: ExportContext
    ) -> dict[str, Any]:
        """Execute workflow with exporter creation at the right time.

        The exporter needs path_root and export_items which are set by
        InitializeStep and PrepareExportStep. This method handles creating
        the exporter after those steps complete.

        Args:
            orchestrator: Step orchestrator.
            context: Export context.

        Returns:
            Export result dict.
        """
        # Execute all steps
        result = orchestrator.execute()

        # If we got to the convert step without an exporter, we need to create one
        # This handles the case where the exporter wasn't set up
        if context.exporter is None and context.path_root is not None:
            try:
                # Create exporter with available context data
                export_items = context.export_items or iter([])
                exporter = self.entrypoint(
                    self.ctx,
                    export_items,
                    context.path_root,
                    **context.export_params,
                )
                context.exporter = exporter
            except Exception:
                pass  # Exporter creation failed, steps will handle errors

        # Add context data to result
        result['exported_count'] = context.exported_count
        result['failed_count'] = context.failed_count
        result['total_count'] = context.total_count
        if context.output_path:
            result['output_path'] = context.output_path

        return result
