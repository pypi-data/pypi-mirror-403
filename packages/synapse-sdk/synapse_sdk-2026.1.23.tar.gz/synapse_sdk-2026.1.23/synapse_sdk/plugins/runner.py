from __future__ import annotations

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.discovery import PluginDiscovery
from synapse_sdk.plugins.enums import ExecutionMode
from synapse_sdk.plugins.executors.local import LocalExecutor
from synapse_sdk.plugins.executors.ray.jobs_api import RayJobsApiExecutor
from synapse_sdk.plugins.executors.ray.task import RayActorExecutor

if TYPE_CHECKING:
    from synapse_sdk.plugins.action import BaseAction


def _discover_action(plugin_code: str, action: str) -> type[BaseAction] | Callable:
    """Discover action class from plugin code."""
    path = Path(plugin_code)

    if path.exists() or (path.parent.exists() and path.suffix == '.yaml'):
        discovery = PluginDiscovery.from_path(path)
    else:
        module = importlib.import_module(plugin_code)
        discovery = PluginDiscovery.from_module(module)

    return discovery.get_action_class(action)


def _get_action_cls(
    plugin_code: str,
    action: str,
    executor_kwargs: dict[str, Any],
) -> type[BaseAction] | Callable:
    """Get action class from kwargs or discover it."""
    action_cls = executor_kwargs.pop('action_cls', None)
    if action_cls is None:
        action_cls = _discover_action(plugin_code, action)
    return action_cls


def _run_local(
    action_cls: type[BaseAction] | Callable,
    params: dict[str, Any],
    executor_kwargs: dict[str, Any],
) -> Any:
    executor = LocalExecutor(**executor_kwargs)
    return executor.execute(action_cls, params)


def _run_task(
    action_cls: type[BaseAction] | Callable,
    params: dict[str, Any],
    executor_kwargs: dict[str, Any],
) -> Any:
    executor = RayActorExecutor(**executor_kwargs)
    return executor.execute(action_cls, params)


def _run_job(
    plugin_code: str,
    action: str,
    params: dict[str, Any],
    executor_kwargs: dict[str, Any],
) -> str:
    """Run plugin action as a Ray Job.

    For JOB mode, we don't import the action class locally - we just need
    the entrypoint string. The actual import happens on the Ray worker.
    """
    path = Path(plugin_code)

    # Set working_dir from plugin path if not provided
    if 'working_dir' not in executor_kwargs:
        if path.exists():
            executor_kwargs['working_dir'] = path if path.is_dir() else path.parent

    job_id = executor_kwargs.pop('job_id', None)
    discovery = PluginDiscovery.from_path(path)
    entrypoint = discovery.get_action_entrypoint(action)

    executor = RayJobsApiExecutor(**executor_kwargs)
    return executor.submit(entrypoint, params, job_id=job_id)


def run_plugin(
    plugin_code: str,
    action: str,
    params: dict[str, Any] | None = None,
    *,
    mode: ExecutionMode = ExecutionMode.LOCAL,
    **executor_kwargs: Any,
) -> Any:
    """Run a plugin action.

    Args:
        plugin_code: Plugin identifier - module path ('my_plugins.yolov8') or
            filesystem path ('/path/to/plugin').
        action: Action name to execute (e.g., 'train', 'infer').
        params: Action parameters dictionary.
        mode: Execution mode:
            - LOCAL: In-process (default, good for dev)
            - TASK: Ray Actor pool (fast startup)
            - JOB: Ray Job API (heavy workloads)
        **executor_kwargs: Executor options (action_cls, env, job_id, working_dir).

    Returns:
        Action result for LOCAL/TASK, job ID string for JOB.
    """
    params = params or {}

    # For JOB mode, don't import the action class locally
    # The plugin code may not be importable in the current environment
    if mode == ExecutionMode.JOB:
        return _run_job(plugin_code, action, params, executor_kwargs)

    # For LOCAL and TASK modes, we need to import the action class
    action_cls = _get_action_cls(plugin_code, action, executor_kwargs)

    match mode:
        case ExecutionMode.LOCAL:
            return _run_local(action_cls, params, executor_kwargs)
        case ExecutionMode.TASK:
            return _run_task(action_cls, params, executor_kwargs)


__all__ = ['run_plugin', 'ExecutionMode']
