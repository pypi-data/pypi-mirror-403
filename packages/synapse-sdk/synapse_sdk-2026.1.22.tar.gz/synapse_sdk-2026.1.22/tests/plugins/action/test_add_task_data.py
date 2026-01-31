"""Unit tests for AddTaskDataAction."""

from __future__ import annotations

from typing import Any, Iterable

import pytest

from synapse_sdk.loggers import NoOpLogger
from synapse_sdk.plugins.actions.add_task_data import AddTaskDataAction, AddTaskDataMethod, AddTaskDataParams
from synapse_sdk.plugins.context import PluginEnvironment, RuntimeContext


class FakeBackendClient:
    """Lightweight stub for BackendClient behaviour needed by AddTaskDataAction."""

    def __init__(
        self,
        *,
        tasks: list[int],
        files: dict[str, Any],
        inference_result: Any | None = None,
        has_target_spec: bool = True,
        serve_running: bool = True,
    ) -> None:
        self.tasks = tasks
        self.files = files
        self.inference_result = inference_result or {'data': 'inference'}
        self.has_target_spec = has_target_spec
        self.serve_running = serve_running
        self.annotated: list[dict[str, Any]] = []
        self.run_calls: list[tuple[str, dict[str, Any]]] = []

    def get_project(self, project_id: int) -> dict[str, Any]:
        return {'id': project_id, 'data_collection': 1}

    def get_data_collection(self, collection_id: int) -> dict[str, Any]:
        specs = [{'name': 'ann_spec'}] if self.has_target_spec else []
        return {'id': collection_id, 'file_specifications': specs}

    def list_tasks(self, params: dict[str, Any] | None = None, list_all: bool = False):
        def gen() -> Iterable[dict[str, Any]]:
            for task_id in self.tasks:
                yield {'id': task_id}

        return gen(), len(self.tasks)

    def get_task(self, task_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {'id': task_id, 'data_unit': {'files': self.files}}

    def get_data_unit(self, unit_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {'id': unit_id, 'files': self.files}

    def annotate_task_data(self, task_id: int, data: dict[str, Any]) -> dict[str, Any]:
        self.annotated.append({'task_id': task_id, 'data': data})
        return {'ok': True}

    def list_serve_applications(self, params: dict[str, Any]) -> dict[str, Any]:
        results = [{'status': 'RUNNING'}] if self.serve_running else []
        return {'results': results}

    def get_plugin_release(self, release_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            'config': {
                'code': 'preproc',
                'actions': {'inference': {'required_resources': {'required_cpu_count': 1, 'required_gpu_count': 0}}},
            },
            'version': '1.0',
        }

    def run_plugin(self, plugin: int | str, data: dict[str, Any]) -> dict[str, Any]:
        self.run_calls.append((plugin, data))
        if data.get('action') == 'deployment':
            self.serve_running = True
            return {'job_id': 'deploy-job'}
        return self.inference_result


class TestAddTaskDataAction(AddTaskDataAction):
    """Concrete test implementation to capture conversion calls."""

    def __init__(self, params: AddTaskDataParams, ctx: RuntimeContext):
        super().__init__(params, ctx)
        self.file_calls: list[tuple[Any, ...]] = []
        self.infer_calls: list[tuple[Any, ...]] = []

    def convert_data_from_file(
        self,
        primary_file_url: str,
        primary_file_name: str | None,
        data_file_url: str,
        data_file_name: str | None,
        task_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.file_calls.append((primary_file_url, primary_file_name, data_file_url, data_file_name, task_data))
        return {'converted_from': data_file_url}

    def convert_data_from_inference(
        self,
        inference_data: Any,
        task_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.infer_calls.append((inference_data, task_data))
        return {'converted_inference': True}

    def _wait_for_pre_processor(self, code: str, timeout_seconds: int = 180, poll_seconds: int = 10) -> None:
        # Skip sleep in tests; rely on fake client state.
        if not self._has_running_serve_app(code):
            raise RuntimeError('Pre-processor not running')


def _make_ctx(client: FakeBackendClient) -> RuntimeContext:
    return RuntimeContext(logger=NoOpLogger(), env=PluginEnvironment(), client=client)


def test_file_method_success() -> None:
    files = {
        'primary': {'url': 'primary-url', 'is_primary': True, 'file_name_original': 'image.jpg'},
        'ann_spec': {'url': 'ann-url', 'file_name_original': 'ann.json'},
    }
    client = FakeBackendClient(tasks=[1, 2], files=files)
    params = AddTaskDataParams(
        name='job',
        description='desc',
        project=1,
        agent=1,
        task_filters={'status': 'pending'},
        method=AddTaskDataMethod.FILE,
        target_specification_name='ann_spec',
        pre_processor_params={},
    )
    action = TestAddTaskDataAction(params, _make_ctx(client))

    result = action.execute()

    assert result.success_count == 2
    assert result.failed_count == 0
    assert client.annotated == [
        {'task_id': 1, 'data': {'action': 'submit', 'data': {'converted_from': 'ann-url'}}},
        {'task_id': 2, 'data': {'action': 'submit', 'data': {'converted_from': 'ann-url'}}},
    ]
    assert len(action.file_calls) == 2
    metrics = action.ctx.logger.get_metrics('annotate_task_data')
    assert metrics['success'] == 2
    assert metrics['failed'] == 0
    assert metrics['stand_by'] == 0


def test_file_method_missing_target_spec_raises() -> None:
    files = {
        'primary': {'url': 'primary-url', 'is_primary': True, 'file_name_original': 'image.jpg'},
        'other': {'url': 'other-url', 'file_name_original': 'other.json'},
    }
    client = FakeBackendClient(tasks=[1], files=files, has_target_spec=False)
    params = AddTaskDataParams(
        name='job',
        description='desc',
        project=1,
        agent=1,
        task_filters={},
        method=AddTaskDataMethod.FILE,
        target_specification_name='ann_spec',
        pre_processor_params={},
    )
    action = TestAddTaskDataAction(params, _make_ctx(client))

    with pytest.raises(ValueError):
        action.execute()

    assert client.annotated == []


def test_inference_method_success() -> None:
    files = {
        'primary': {'url': 'primary-url', 'is_primary': True, 'file_name_original': 'image.jpg'},
    }
    client = FakeBackendClient(tasks=[10], files=files, inference_result={'boxes': []}, serve_running=True)
    params = AddTaskDataParams(
        name='job',
        description='desc',
        project=1,
        agent=99,
        task_filters={},
        method=AddTaskDataMethod.INFERENCE,
        pre_processor=123,
        model=5,
        pre_processor_params={'threshold': 0.5},
    )
    action = TestAddTaskDataAction(params, _make_ctx(client))

    result = action.execute()

    assert result.success_count == 1
    assert result.failed_count == 0
    assert client.run_calls[-1][0] == 'preproc'
    payload = client.run_calls[-1][1]
    assert payload['action'] == 'inference'
    assert payload['params']['model'] == 5
    assert client.annotated == [
        {'task_id': 10, 'data': {'action': 'submit', 'data': {'converted_inference': True}}},
    ]
    assert len(action.infer_calls) == 1
