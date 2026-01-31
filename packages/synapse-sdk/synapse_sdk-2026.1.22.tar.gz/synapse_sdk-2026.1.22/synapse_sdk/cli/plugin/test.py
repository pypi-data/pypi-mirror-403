"""Plugin local test command implementation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from rich.console import Console


@dataclass
class TestResult:
    """Result of plugin test execution."""

    action: str
    plugin: str
    result: Any
    mode: str
    job_id: str | None = None


def test_plugin(
    action: str,
    console: Console,
    *,
    path: Path,
    params: dict[str, Any] | None = None,
    mode: Literal['local', 'task', 'job'] = 'local',
    ray_address: str = 'auto',
    num_gpus: int | None = None,
    num_cpus: int | None = None,
    job_id: str | None = None,
    env: dict[str, Any] | None = None,
    include_sdk: bool = False,
) -> TestResult:
    """Execute plugin action for testing.

    Args:
        action: Action name to execute (e.g., test, train).
        console: Rich console.
        path: Plugin directory path.
        params: Optional parameters to pass to the action.
        mode: Execution mode:
            - 'local': In-process execution (best for debugging)
            - 'task': Ray Actor execution (no log streaming)
            - 'job': Ray Jobs API with log streaming (recommended for remote)
        ray_address: Ray cluster address (for 'task'/'job' modes).
        num_gpus: Number of GPUs to request.
        num_cpus: Number of CPUs to request.
        job_id: Optional job identifier for tracking.
        env: Environment variables to pass.

    Returns:
        TestResult with action result.

    Raises:
        ActionNotFoundError: If action doesn't exist.
        ExecutionError: If execution fails.
    """
    import sys

    from synapse_sdk.plugins.discovery import PluginDiscovery

    # Add plugin directory to sys.path so entrypoints like 'plugin.test.TestAction' can be imported
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

    # Discover plugin
    discovery = PluginDiscovery.from_path(path)
    config = discovery.config
    plugin_code = config.code

    # Check if config is out of sync with code
    config_file = path / 'config.yaml'
    if not config_file.exists():
        config_file = path / 'synapse.yaml'
    if config_file.exists():
        pending_changes = discovery.check_config_sync(config_file)
        if pending_changes:
            console.print('[yellow]Warning: config.yaml may be out of sync with code[/yellow]')
            for action_name, change in pending_changes.items():
                console.print(f'  [dim]{action_name}:[/dim] {change}')
            console.print('[dim]Run `synapse plugin update-config` to sync[/dim]\n')

    # Merge env: CLI env takes precedence over config env
    merged_env = {**config.env, **(env or {})}

    console.print(f'[dim]Plugin:[/dim] {plugin_code}')
    console.print(f'[dim]Action:[/dim] {action}')
    console.print(f'[dim]Mode:[/dim] {mode}')

    params = params or {}

    if mode == 'local':
        from synapse_sdk.plugins.executors.local import LocalExecutor

        console.print()

        # Get action class (local import works since we're in-process)
        action_cls = discovery.get_action_class(action)

        executor = LocalExecutor(env=merged_env, job_id=job_id)
        result = executor.execute(action_cls, params)

        return TestResult(
            action=action,
            plugin=plugin_code,
            result=result,
            mode=mode,
        )

    elif mode == 'task':
        from synapse_sdk.plugins.executors.ray.task import RayActorExecutor

        if num_gpus is not None:
            console.print(f'[dim]GPUs:[/dim] {num_gpus}')
        if num_cpus is not None:
            console.print(f'[dim]CPUs:[/dim] {num_cpus}')
        console.print()

        # Get entrypoint string (don't load class locally - it runs on remote Ray worker)
        entrypoint = discovery.get_action_entrypoint(action)

        executor = RayActorExecutor(
            working_dir=path,
            ray_address=ray_address,
            num_gpus=num_gpus,
            num_cpus=num_cpus,
            env=merged_env,
            job_id=job_id,
            include_sdk=include_sdk,
            package_manager=config.package_manager,
            package_manager_options=config.package_manager_options or None,
            wheels_dir=config.wheels_dir,
            runtime_env=config.runtime_env or None,
        )

        try:
            result = executor.execute(entrypoint, params)
        finally:
            executor.shutdown()

        return TestResult(
            action=action,
            plugin=plugin_code,
            result=result,
            mode=mode,
        )

    else:  # mode == 'job' (or 'jobs-api' alias)
        from synapse_sdk.plugins.executors.ray.jobs_api import RayJobsApiExecutor

        # Derive dashboard address from ray_address
        if ray_address.startswith('ray://'):
            from urllib.parse import urlparse

            parsed = urlparse(ray_address)
            dashboard_addr = f'http://{parsed.hostname}:8265'
        else:
            dashboard_addr = 'http://localhost:8265'

        console.print(f'[dim]Dashboard:[/dim] {dashboard_addr}')
        if num_gpus is not None:
            console.print(f'[dim]GPUs:[/dim] {num_gpus}')
        if num_cpus is not None:
            console.print(f'[dim]CPUs:[/dim] {num_cpus}')
        console.print()

        # Get entrypoint string (don't load class locally - it runs on remote Ray worker)
        entrypoint = discovery.get_action_entrypoint(action)

        executor = RayJobsApiExecutor(
            dashboard_address=dashboard_addr,
            working_dir=path,
            num_gpus=num_gpus,
            num_cpus=num_cpus,
            env=merged_env,
            include_sdk=include_sdk,
            package_manager=config.package_manager,
            package_manager_options=config.package_manager_options or None,
        )

        # Submit job via Ray Jobs API
        submitted_job_id = executor.submit(entrypoint, params, job_id=job_id)

        console.print(f'[dim]Job submitted:[/dim] {submitted_job_id}')
        console.print('[dim]Streaming logs (Ctrl+C to stop watching)...[/dim]')
        console.print()

        # Stream logs in real-time
        try:
            for log_line in executor.stream_logs(submitted_job_id):
                console.print(log_line, end='')
        except KeyboardInterrupt:
            console.print('\n[dim]Stopped watching logs.[/dim]')

        # Get final result
        result = executor.get_result(submitted_job_id, timeout=30)
        console.print('\n[dim]Status:[/dim] SUCCEEDED')

        return TestResult(
            action=action,
            plugin=plugin_code,
            result=result,
            mode=mode,
            job_id=submitted_job_id,
        )


__all__ = ['TestResult', 'test_plugin']
