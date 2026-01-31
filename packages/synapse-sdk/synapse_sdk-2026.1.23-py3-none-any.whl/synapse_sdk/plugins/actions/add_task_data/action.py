"""Add task data action for pre-annotation workflows."""

from __future__ import annotations

import time
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Iterable

from pydantic import BaseModel, Field

from synapse_sdk.clients.backend.models import JobStatus
from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.add_task_data.context import AddTaskDataContext
from synapse_sdk.plugins.actions.add_task_data.log_messages import AddTaskDataLogMessageCode
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry
from synapse_sdk.plugins.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class AddTaskDataMethod(StrEnum):
    """Supported methods for add_task_data."""

    FILE = 'file'
    INFERENCE = 'inference'


class AddTaskDataParams(BaseModel):
    """Parameters for AddTaskDataAction."""

    name: str = Field(min_length=1)
    description: str | None = None
    project: int
    agent: int
    task_filters: dict[str, Any] = Field(default_factory=dict)
    method: AddTaskDataMethod = AddTaskDataMethod.FILE
    target_specification_name: str | None = None
    model: int | None = None
    pre_processor: int | None = None
    pre_processor_params: dict[str, Any] = Field(default_factory=dict)


class AddTaskDataResult(BaseModel):
    """Result payload for AddTaskDataAction."""

    status: JobStatus
    message: str
    total_tasks: int
    success_count: int
    failed_count: int
    failures: list[dict[str, Any]] = Field(default_factory=list)


class AddTaskDataProgressCategories:
    """Progress category names for add_task_data workflow."""

    ANNOTATE_TASK_DATA: str = 'annotate_task_data'


class AddTaskDataAction(BaseAction[AddTaskDataParams]):
    """Add task data action for file-based and inference-based pre-annotation.

    This action annotates tasks by either reading task data from file
    specifications or invoking a pre-processor for inference. Subclasses
    must implement the conversion hooks to map raw data into task payloads.
    """

    action_name = 'add_task_data'
    category = PluginCategory.PRE_ANNOTATION
    result_model = AddTaskDataResult
    progress = AddTaskDataProgressCategories()
    context: AddTaskDataContext | None = None

    @classmethod
    def get_log_message_code_class(cls) -> type[AddTaskDataLogMessageCode]:
        from synapse_sdk.plugins.actions.add_task_data.log_messages import AddTaskDataLogMessageCode

        return AddTaskDataLogMessageCode

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient: Backend client instance from runtime context.

        Raises:
            RuntimeError: If no backend client is attached to the context.
        """
        if self.ctx.client is None:
            raise RuntimeError('No backend client in context. Provide one via RuntimeContext.')
        return self.ctx.client

    def create_context(self) -> AddTaskDataContext:
        """Create execution context.

        Returns:
            AddTaskDataContext: Fresh context seeded with params and runtime ctx.
        """
        params_dict = self.params.model_dump()
        return AddTaskDataContext(runtime_ctx=self.ctx, params=params_dict)

    def setup_steps(self, registry: StepRegistry[AddTaskDataContext]) -> None:
        """Register workflow steps for add_task_data.

        Args:
            registry: Step registry to populate.
        """

        class AnnotateTaskDataStep(BaseStep[AddTaskDataContext]):
            """Single step that performs task annotation."""

            def __init__(self, action: AddTaskDataAction) -> None:
                """Initialize the annotation step.

                Args:
                    action: The parent AddTaskDataAction instance.
                """
                self._action = action

            @property
            def name(self) -> str:
                """Get the step name for progress tracking.

                Returns:
                    The progress category name for task annotation.
                """
                return AddTaskDataProgressCategories.ANNOTATE_TASK_DATA

            @property
            def progress_weight(self) -> float:
                """Get the relative weight of this step in overall progress.

                Returns:
                    The weight value (1.0 for full weight).
                """
                return 1.0

            def execute(self, context: AddTaskDataContext) -> StepResult:
                """Execute the task annotation step.

                Args:
                    context: The execution context containing task information.

                Returns:
                    Result of the annotation step execution.
                """
                return self._action._annotate_tasks(context)  # noqa: SLF001

        registry.register(AnnotateTaskDataStep(self))

    def run(self) -> AddTaskDataResult:
        """Run the action, using step orchestration when steps are registered.

        Returns:
            AddTaskDataResult: Summary of annotation outcome.
        """
        registry: StepRegistry[AddTaskDataContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            context = self.create_context()
            self.context = context
            orchestrator: Orchestrator[AddTaskDataContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total, self.progress.ANNOTATE_TASK_DATA),
            )
            orchestrator.execute()
            return AddTaskDataResult(
                status=JobStatus.SUCCEEDED,
                message=f'add_task_data completed. success={context.success_count}, failed={context.failed_count}',
                total_tasks=context.total_tasks,
                success_count=context.success_count,
                failed_count=context.failed_count,
                failures=context.failures,
            )

        return self.execute()

    def execute(self) -> AddTaskDataResult:
        """Execute add_task_data workflow.

        Returns:
            AddTaskDataResult: Summary of success/failure counts and failures.

        Raises:
            ValueError: If required params are missing or no tasks are found.
        """
        self.context = self.context or self.create_context()
        context = self.context

        step_result = self._annotate_tasks(context)
        if not step_result.success:
            raise ValueError(step_result.error or 'add_task_data failed')

        message = step_result.data.get(
            'message',
            f'add_task_data completed. success={context.success_count}, failed={context.failed_count}',
        )
        return AddTaskDataResult(
            status=JobStatus.SUCCEEDED,
            message=message,
            total_tasks=context.total_tasks,
            success_count=context.success_count,
            failed_count=context.failed_count,
            failures=context.failures,
        )

    def _annotate_tasks(self, context: AddTaskDataContext) -> StepResult:
        """Annotate tasks using file or inference method.

        Args:
            context: Shared action context.

        Returns:
            StepResult: Success flag and optional error/message.
        """
        try:
            data_collection = self._load_data_collection()
            context.data_collection = data_collection

            if self.params.method == AddTaskDataMethod.FILE:
                self._validate_target_specification(data_collection)
                context.inference = None
            elif self.params.method == AddTaskDataMethod.INFERENCE:
                context.inference = self._prepare_inference_context()
            else:
                raise ValueError(f'Unsupported annotation method: {self.params.method}')

            task_ids, total_tasks = self._iter_task_ids()
            context.task_ids = list(task_ids)
            if total_tasks <= 0:
                raise ValueError('No tasks found to annotate')

            self.log_message(
                AddTaskDataLogMessageCode.TASK_DATA_ANNOTATING,
                count=total_tasks,
                method=self.params.method.value,
            )

            context.success_count = 0
            context.failed_count = 0
            context.failures = []

            self._update_progress(0, total_tasks, context.success_count, context.failed_count)

            for index, task_id in enumerate(context.task_ids, start=1):
                try:
                    task_data = self._fetch_task(task_id)
                    if self.params.method == AddTaskDataMethod.FILE:
                        self._process_file_task(task_id, task_data)
                    else:
                        assert context.inference is not None
                        self._process_inference_task(task_id, task_data, context.inference)
                    context.success_count += 1
                except Exception as exc:  # noqa: BLE001
                    context.failed_count += 1
                    context.failures.append({'task_id': task_id, 'error': str(exc)})
                    self.log(
                        'add_task_data_task_failed',
                        {'task_id': task_id, 'error': str(exc)},
                    )

                self._update_progress(index, total_tasks, context.success_count, context.failed_count)

            message = f'add_task_data completed. success={context.success_count}, failed={context.failed_count}'
            if context.failed_count > 0:
                self.log_message(
                    AddTaskDataLogMessageCode.TASK_DATA_COMPLETED_WITH_FAILURES,
                    success=context.success_count,
                    failed=context.failed_count,
                )
            else:
                self.log_message(
                    AddTaskDataLogMessageCode.TASK_DATA_COMPLETED,
                    count=context.success_count,
                )
            return StepResult(success=True, data={'message': message})

        except Exception as exc:  # noqa: BLE001
            return StepResult(success=False, error=str(exc))

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_name: str | None,
        data_file_url: str,
        data_file_name: str | None,
        task_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convert file-based data into task data payload.

        Args:
            primary_file_url: URL of the primary file.
            primary_file_name: Original name of the primary file.
            data_file_url: URL of the annotation data file.
            data_file_name: Original name of the annotation data file.
            task_data: Optional task payload for additional context.

        Returns:
            dict[str, Any]: Task data payload ready for submission.
        """
        raise NotImplementedError('Override convert_data_from_file() in a subclass.')

    def convert_data_from_inference(
        self,
        inference_data: Any,
        task_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Convert inference output into task data payload.

        Args:
            inference_data: Raw output returned by the pre-processor.
            task_data: Optional task payload for additional context.

        Returns:
            dict[str, Any]: Task data payload ready for submission.
        """
        raise NotImplementedError('Override convert_data_from_inference() in a subclass.')

    def _load_data_collection(self) -> dict[str, Any]:
        """Load project and data collection metadata.

        Returns:
            dict[str, Any]: Data collection payload including file specs.

        Raises:
            ValueError: If project or data collection responses are invalid.
        """
        project = self.client.get_project(self.params.project)
        if not isinstance(project, dict):
            raise ValueError('Invalid project response')

        data_collection_id = project.get('data_collection')
        if not data_collection_id:
            raise ValueError('Project does not have a data collection')

        data_collection = self.client.get_data_collection(data_collection_id)
        if not isinstance(data_collection, dict):
            raise ValueError('Invalid data collection response')

        return data_collection

    def _validate_target_specification(self, data_collection: dict[str, Any]) -> None:
        """Validate target specification name for file mode.

        Args:
            data_collection: Data collection metadata with file specifications.

        Raises:
            ValueError: If target spec is missing or not found.
        """
        target_spec = self.params.target_specification_name
        if not target_spec:
            raise ValueError('target_specification_name is required for file method')

        file_specs = data_collection.get('file_specifications', [])
        if not any(spec.get('name') == target_spec for spec in file_specs if isinstance(spec, dict)):
            raise ValueError(f"Target specification '{target_spec}' not found in file specifications")

    def _prepare_inference_context(self) -> dict[str, Any]:
        """Prepare inference context from pre-processor release.

        Returns:
            dict[str, Any]: Contains pre-processor code and version.

        Raises:
            ValueError: If required fields are missing or responses are invalid.
        """
        if not self.params.pre_processor:
            raise ValueError('pre_processor is required for inference method')
        if not self.params.model:
            raise ValueError('model is required for inference method')
        if not self.params.agent:
            raise ValueError('agent is required for inference method')

        release = self.client.get_plugin_release(self.params.pre_processor)
        if not isinstance(release, dict):
            raise ValueError('Invalid pre-processor response')

        config = release.get('config', {})
        code = config.get('code')
        version = release.get('version')
        if not code or not version:
            raise ValueError('Invalid pre-processor configuration')

        required_resources = config.get('actions', {}).get('inference', {}).get('required_resources', {})
        self._ensure_pre_processor_running(code, required_resources)

        return {
            'code': code,
            'version': version,
        }

    def _ensure_pre_processor_running(self, code: str, required_resources: dict[str, Any]) -> None:
        """Ensure pre-processor serve app is running.

        Args:
            code: Pre-processor plugin code.
            required_resources: Resource hints from plugin config.

        Raises:
            RuntimeError: If pre-processor fails to become ready.
        """
        if self._has_running_serve_app(code):
            return

        num_cpus = required_resources.get('required_cpu_count', required_resources.get('num_cpus', 1))
        num_gpus = required_resources.get('required_gpu_count', required_resources.get('num_gpus', 0.1))

        self.ctx.log_message(AddTaskDataLogMessageCode.TASK_DATA_PREPROCESSOR_DEPLOYING)
        self.client.run_plugin(
            code,
            {
                'agent': self.params.agent,
                'action': 'deployment',
                'params': {
                    'num_cpus': num_cpus,
                    'num_gpus': num_gpus,
                },
            },
        )

        self._wait_for_pre_processor(code)

    def _wait_for_pre_processor(self, code: str, timeout_seconds: int = 180, poll_seconds: int = 10) -> None:
        """Wait until the pre-processor serve app is running.

        Args:
            code: Pre-processor plugin code.
            timeout_seconds: Maximum time to wait.
            poll_seconds: Polling interval.

        Raises:
            RuntimeError: If the serve app does not reach RUNNING status.
        """
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            if self._has_running_serve_app(code):
                return
            time.sleep(poll_seconds)

        raise RuntimeError('Pre-processor did not become ready within timeout')

    def _has_running_serve_app(self, code: str) -> bool:
        """Check if a serve application is running for the pre-processor.

        Args:
            code: Pre-processor plugin code.

        Returns:
            bool: True if a RUNNING serve app exists for the given code.
        """
        response = self.client.list_serve_applications(
            params={'plugin_code': code, 'job__agent': self.params.agent},
        )
        results = response.get('results', []) if isinstance(response, dict) else response
        if isinstance(results, list):
            return any(isinstance(app, dict) and app.get('status') == 'RUNNING' for app in results)
        return False

    def _iter_task_ids(self) -> tuple[Iterable[int], int]:
        """Iterate task IDs and count.

        Returns:
            tuple[Iterable[int], int]: Generator of task IDs and total count.

        Raises:
            ValueError: If the response format is unexpected.
        """
        params = dict(self.params.task_filters or {})
        params['fields'] = 'id'
        params['project'] = self.params.project

        response = self.client.list_tasks(params=params, list_all=True)
        if isinstance(response, tuple):
            items, count = response
            return self._extract_task_ids(items), count

        if isinstance(response, dict):
            results = response.get('results', [])
            count = response.get('count', len(results))
            return self._extract_task_ids(results), count

        if isinstance(response, list):
            return self._extract_task_ids(response), len(response)

        raise ValueError('Unexpected task list response')

    def _extract_task_ids(self, items: Iterable[Any]) -> Iterable[int]:
        """Extract integer task IDs from iterable items.

        Args:
            items: Iterable of task records.

        Yields:
            int: Task ID values.
        """
        for item in items:
            if isinstance(item, dict) and item.get('id') is not None:
                yield int(item['id'])

    def _fetch_task(self, task_id: int) -> dict[str, Any]:
        """Fetch task with required fields.

        Args:
            task_id: Task identifier.

        Returns:
            dict[str, Any]: Task payload with data_unit expanded.

        Raises:
            ValueError: If the response is not a dict.
        """
        task = self.client.get_task(task_id, params={'fields': 'id,data,data_unit', 'expand': 'data_unit'})
        if not isinstance(task, dict):
            raise ValueError('Invalid task response')
        return task

    def _process_file_task(self, task_id: int, task_data: dict[str, Any]) -> None:
        """Process a task using file-based annotation."""
        files = self._get_task_files(task_data)
        primary_url, primary_name = self._extract_primary_file(files)
        if not primary_url:
            raise ValueError('Primary file URL not found for task')

        target_spec = self.params.target_specification_name
        target_file = self._find_file_by_spec(files, target_spec)
        if not target_file:
            raise ValueError('Target specification file not found for task')

        data_file_url = target_file.get('url')
        if not data_file_url:
            raise ValueError('Target specification URL not found for task')

        data_file_name = self._get_file_name(target_file)
        converted = self.convert_data_from_file(
            primary_url,
            primary_name,
            data_file_url,
            data_file_name,
            task_data=task_data,
        )
        self._submit_task_data(task_id, converted)

    def _process_inference_task(
        self,
        task_id: int,
        task_data: dict[str, Any],
        inference_context: dict[str, Any],
    ) -> None:
        """Process a task using inference-based annotation."""
        files = self._get_task_files(task_data)
        primary_url, _ = self._extract_primary_file(files)
        if not primary_url:
            raise ValueError('Primary file URL not found for task')

        inference_data = self._run_inference(
            inference_context['code'],
            inference_context['version'],
            primary_url,
        )
        converted = self.convert_data_from_inference(inference_data, task_data=task_data)
        self._submit_task_data(task_id, converted)

    def _run_inference(self, code: str, version: str, primary_file_url: str) -> Any:
        """Run inference through pre-processor serve app."""
        params = dict(self.params.pre_processor_params)
        params['image_path'] = primary_file_url

        payload = {
            'agent': self.params.agent,
            'action': 'inference',
            'version': version,
            'params': {
                'model': self.params.model,
                'method': 'post',
                'json': params,
            },
        }

        result = self.client.run_plugin(code, payload)
        if result is None:
            raise ValueError('Inference returned no data')
        return result

    def _submit_task_data(self, task_id: int, data: dict[str, Any]) -> None:
        """Submit converted task data to backend."""
        self.client.annotate_task_data(task_id, data={'action': 'submit', 'data': data})

    def _get_task_files(self, task_data: dict[str, Any]) -> dict[str, Any] | list[dict[str, Any]]:
        """Retrieve files from task data unit, fetching if needed."""
        data_unit = task_data.get('data_unit')
        if not isinstance(data_unit, dict):
            raise ValueError('Task does not have a data unit')

        files = data_unit.get('files')
        if not files and data_unit.get('id'):
            data_unit = self.client.get_data_unit(data_unit['id'], params={'expand': 'files'})
            if isinstance(data_unit, dict):
                files = data_unit.get('files')

        if not files:
            raise ValueError('Data unit does not have files')
        return files

    def _extract_primary_file(self, files: dict[str, Any] | list[dict[str, Any]]) -> tuple[str | None, str | None]:
        """Extract primary file URL and name from files collection."""
        for file_info in self._iter_files(files):
            if file_info.get('is_primary') and file_info.get('url'):
                return file_info.get('url'), self._get_file_name(file_info)
        return None, None

    def _find_file_by_spec(
        self,
        files: dict[str, Any] | list[dict[str, Any]],
        spec_name: str | None,
    ) -> dict[str, Any] | None:
        """Find file matching the given specification name."""
        if not spec_name:
            return None

        if isinstance(files, dict):
            candidate = files.get(spec_name)
            if isinstance(candidate, dict):
                return candidate

        for file_info in self._iter_files(files):
            for key in ('specification', 'specification_name', 'name'):
                if file_info.get(key) == spec_name:
                    return file_info

        return None

    def _iter_files(self, files: dict[str, Any] | list[dict[str, Any]]) -> Iterable[dict[str, Any]]:
        """Iterate over file dicts regardless of mapping or list input."""
        if isinstance(files, dict):
            for value in files.values():
                if isinstance(value, dict):
                    yield value
        elif isinstance(files, list):
            for item in files:
                if isinstance(item, dict):
                    yield item

    def _get_file_name(self, file_info: dict[str, Any]) -> str | None:
        """Extract a best-effort original filename from file info."""
        for key in ('file_name_original', 'filename', 'name'):
            value = file_info.get(key)
            if value:
                return str(value)
        return None

    def _update_progress(self, current: int, total: int, success: int, failed: int) -> None:
        """Update progress metrics for task annotation workflow.

        Args:
            current: Current number of processed tasks.
            total: Total number of tasks to process.
            success: Number of successfully annotated tasks.
            failed: Number of failed annotation attempts.
        """
        self.set_progress(current, total, self.progress.ANNOTATE_TASK_DATA)
        remaining = max(total - current, 0)
        self.set_metrics(
            {'success': success, 'failed': failed, 'stand_by': remaining},
            self.progress.ANNOTATE_TASK_DATA,
        )
