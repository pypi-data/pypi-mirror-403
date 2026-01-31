"""Ray Jobs API executor for plugin actions with runtime env log streaming.

This executor uses Ray's Jobs API (JobSubmissionClient) instead of ray.remote,
which provides access to runtime environment setup logs and proper job lifecycle.
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, AsyncIterator, Iterator, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager
from synapse_sdk.plugins.errors import ExecutionError
from synapse_sdk.plugins.executors.ray.base import BaseRayExecutor

if TYPE_CHECKING:
    from ray.job_submission import JobStatus

    from synapse_sdk.plugins.action import BaseAction


class RayJobsApiExecutor(BaseRayExecutor):
    """Ray Jobs API based execution with log streaming support.

    Uses Ray's JobSubmissionClient for job management, which provides:
    - Access to runtime environment setup logs
    - Real-time log streaming via tail_job_logs
    - Proper job lifecycle management

    Example:
        >>> executor = RayJobsApiExecutor(
        ...     dashboard_address='http://localhost:8265',
        ...     working_dir='/path/to/plugin',
        ... )
        >>> job_id = executor.submit(TrainAction, {'epochs': 100})
        >>>
        >>> # Stream logs including runtime env setup
        >>> for log_line in executor.stream_logs(job_id):
        ...     print(log_line, end='')
        >>>
        >>> result = executor.get_result(job_id)
    """

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        *,
        dashboard_address: str = 'http://localhost:8265',
        runtime_env: dict[str, Any] | None = None,
        working_dir: str | Path | None = None,
        requirements_file: str | Path | None = None,
        package_manager: PackageManager | Literal['pip', 'uv'] = PackageManager.PIP,
        package_manager_options: list[str] | None = None,
        wheels_dir: str = 'wheels',
        ray_address: str = 'auto',
        num_cpus: int | float | None = None,
        num_gpus: int | float | None = None,
        memory: int | None = None,
        include_sdk: bool = False,
    ) -> None:
        """Initialize Ray Jobs API executor.

        Args:
            env: Environment config for the action. If None, loads from os.environ.
            dashboard_address: Ray Dashboard HTTP address (e.g., 'http://localhost:8265').
            runtime_env: Ray runtime environment config.
            working_dir: Plugin working directory.
            requirements_file: Path to requirements.txt.
            package_manager: Package manager to use ('pip' or 'uv').
            package_manager_options: Additional options for the package manager.
            wheels_dir: Directory containing .whl files relative to working_dir.
            ray_address: Ignored. Ray Jobs API always uses 'auto' internally.
            num_cpus: Number of CPUs for the entrypoint.
            num_gpus: Number of GPUs for the entrypoint.
            memory: Memory in bytes for the entrypoint.
            include_sdk: If True, bundle local SDK with upload (for development).
        """
        # Use 'auto' for ray_address since we're using the Jobs API
        super().__init__(
            env=env,
            runtime_env=runtime_env,
            working_dir=working_dir,
            requirements_file=requirements_file,
            package_manager=package_manager,
            package_manager_options=package_manager_options,
            wheels_dir=wheels_dir,
            ray_address='auto',
            include_sdk=include_sdk,
        )
        self._dashboard_address = dashboard_address
        self._num_cpus = num_cpus
        self._num_gpus = num_gpus
        self._memory = memory
        self._client: Any | None = None
        self._job_results: dict[str, Any] = {}  # job_id -> parsed result  # job_id -> parsed result

    def _get_client(self) -> Any:
        """Get or create JobSubmissionClient."""
        if self._client is None:
            from ray.job_submission import JobSubmissionClient

            self._client = JobSubmissionClient(self._dashboard_address)
        return self._client

    def _build_jobs_api_runtime_env(self) -> dict[str, Any]:
        """Build runtime environment for Jobs API.

        The Jobs API requires working_dir to be a local path that it will upload,
        or a remote URI (gcs://, s3://, etc.). Unlike ray.remote actors, the Jobs API
        handles the upload automatically, so we don't need to call _get_working_dir_uri().
        """
        # Build base runtime env without GCS upload (Jobs API doesn't need ray.init())
        # We inline the parent logic but skip _get_working_dir_uri() call
        runtime_env = {**self._runtime_env}

        # Build package manager config with requirements and wheels
        import shlex

        pm_key = str(self._package_manager)  # 'pip' or 'uv'
        raw_requirements = self._get_requirements() or []
        wheel_files = self._get_wheel_files()

        # Separate packages from pip args (lines starting with -)
        packages = []
        pip_args = []
        for req in raw_requirements:
            stripped = req.strip()
            if stripped.startswith('-'):
                pip_args.append(stripped)
            else:
                packages.append(stripped)

        # Combine packages and wheel files
        all_packages = packages + wheel_files

        if all_packages:
            if pm_key not in runtime_env:
                runtime_env[pm_key] = {'packages': []}
            elif isinstance(runtime_env[pm_key], list):
                runtime_env[pm_key] = {'packages': runtime_env[pm_key]}

            runtime_env[pm_key].setdefault('packages', [])
            runtime_env[pm_key]['packages'].extend(all_packages)

        # Apply package manager options
        pm_options = self._get_package_manager_options()
        if pm_key not in runtime_env:
            runtime_env[pm_key] = {}
        elif not isinstance(runtime_env[pm_key], dict):
            runtime_env[pm_key] = {'packages': runtime_env[pm_key]} if runtime_env[pm_key] else {}

        # Add pip args to options
        if pip_args:
            split_pip_args = []
            for arg in pip_args:
                split_pip_args.extend(shlex.split(arg))

            if self._package_manager == PackageManager.UV:
                runtime_env[pm_key].setdefault('uv_pip_install_options', [])
                runtime_env[pm_key]['uv_pip_install_options'].extend(split_pip_args)
            else:
                runtime_env[pm_key].setdefault('pip_install_options', [])
                runtime_env[pm_key]['pip_install_options'].extend(split_pip_args)

        # Apply default package manager options
        if pm_options:
            for key, value in pm_options.items():
                if key in runtime_env[pm_key]:
                    existing = runtime_env[pm_key][key]
                    for v in value:
                        if v not in existing:
                            existing.append(v)
                else:
                    runtime_env[pm_key][key] = value

        # Add env vars
        runtime_env.setdefault('env_vars', {})
        runtime_env['env_vars'].update(self._env.to_dict())

        # Include Synapse credentials for backend client on workers
        from synapse_sdk.utils.auth import ENV_SYNAPSE_ACCESS_TOKEN, ENV_SYNAPSE_HOST, load_credentials

        creds = load_credentials()
        if creds.host and ENV_SYNAPSE_HOST not in runtime_env['env_vars']:
            runtime_env['env_vars'][ENV_SYNAPSE_HOST] = creds.host
        if creds.token and ENV_SYNAPSE_ACCESS_TOKEN not in runtime_env['env_vars']:
            runtime_env['env_vars'][ENV_SYNAPSE_ACCESS_TOKEN] = creds.token

        # For Jobs API, include SDK in py_modules if requested
        if self._include_sdk:
            import synapse_sdk

            sdk_path = str(Path(synapse_sdk.__file__).parent)
            runtime_env.setdefault('py_modules', [])
            if sdk_path not in runtime_env['py_modules']:
                runtime_env['py_modules'].append(sdk_path)

        # Set working_dir as local path (Jobs API handles upload automatically)
        if self._working_dir and 'working_dir' not in runtime_env:
            runtime_env['working_dir'] = str(self._working_dir)

        return runtime_env

    def submit(
        self,
        action_cls: type[BaseAction] | str,
        params: dict[str, Any],
        *,
        job_id: str | None = None,
    ) -> str:
        """Submit action as a Ray Job (non-blocking).

        Args:
            action_cls: BaseAction subclass or entrypoint string.
            params: Parameters dict for the action.
            job_id: Optional job identifier. If None, Ray generates one.

        Returns:
            Job ID for tracking.
        """
        import json

        client = self._get_client()

        # Convert class to entrypoint string
        if isinstance(action_cls, str):
            entrypoint = action_cls
        else:
            entrypoint = f'{action_cls.__module__}.{action_cls.__name__}'

        # Build runtime env
        runtime_env = self._build_jobs_api_runtime_env()

        # Add params and entrypoint to env vars
        runtime_env.setdefault('env_vars', {})
        runtime_env['env_vars']['SYNAPSE_ACTION_ENTRYPOINT'] = entrypoint

        # For small params, use env var directly. For large params, use a temp file.
        params_json = json.dumps(params)
        if len(params_json) < 32000:  # Safe limit for env var size
            runtime_env['env_vars']['SYNAPSE_ACTION_PARAMS'] = params_json
        else:
            # Write params to a temp file in working_dir
            if self._working_dir:
                params_file = Path(self._working_dir) / '.synapse_params.json'
                params_file.write_text(params_json)
                runtime_env['env_vars']['SYNAPSE_ACTION_PARAMS_FILE'] = '.synapse_params.json'
            else:
                # Fallback: use temp directory
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    f.write(params_json)
                    runtime_env['env_vars']['SYNAPSE_ACTION_PARAMS_FILE'] = f.name

        # Use SDK module as entrypoint
        entrypoint_cmd = 'python -m synapse_sdk.plugins.entrypoint'

        if job_id:
            runtime_env['env_vars']['SYNAPSE_JOB_ID'] = job_id

        # Submit job
        submit_kwargs: dict[str, Any] = {
            'entrypoint': entrypoint_cmd,
            'runtime_env': runtime_env,
        }

        if job_id:
            submit_kwargs['submission_id'] = job_id

        if self._num_cpus is not None:
            submit_kwargs['entrypoint_num_cpus'] = self._num_cpus
        if self._num_gpus is not None:
            submit_kwargs['entrypoint_num_gpus'] = self._num_gpus
        if self._memory is not None:
            submit_kwargs['entrypoint_memory'] = self._memory

        ray_job_id = client.submit_job(**submit_kwargs)
        result = job_id if job_id else ray_job_id
        return result

    def get_status(self, job_id: str) -> JobStatus:
        """Get job status.

        Args:
            job_id: Job ID from submit().

        Returns:
            JobStatus enum (PENDING, RUNNING, SUCCEEDED, FAILED, STOPPED).
        """
        client = self._get_client()
        return client.get_job_status(job_id)

    def get_logs(self, job_id: str) -> str:
        """Get all job logs (includes runtime env setup logs).

        Args:
            job_id: Job ID from submit().

        Returns:
            Full job logs as a string.
        """
        client = self._get_client()
        return client.get_job_logs(job_id)

    def stream_logs(
        self,
        job_id: str,
        *,
        timeout: float = 3600.0,
    ) -> Iterator[str]:
        """Stream job logs synchronously (includes runtime env setup logs).

        This is a synchronous wrapper around the async tail_job_logs method.
        Streams logs in real-time, including runtime environment setup progress.

        Args:
            job_id: Job ID from submit().
            timeout: Maximum time to stream logs in seconds.

        Yields:
            Log lines as they become available.

        Example:
            >>> for line in executor.stream_logs(job_id):
            ...     print(line, end='')
        """

        async def _stream() -> AsyncIterator[str]:
            client = self._get_client()
            async for lines in client.tail_job_logs(job_id):
                yield lines

        # Run async generator in sync context
        loop = asyncio.new_event_loop()
        try:
            agen = _stream()
            while True:
                try:
                    future = asyncio.wait_for(
                        agen.__anext__(),  # type: ignore[union-attr]
                        timeout=timeout,
                    )
                    yield loop.run_until_complete(future)
                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    break
        finally:
            loop.close()

    async def stream_logs_async(
        self,
        job_id: str,
    ) -> AsyncIterator[str]:
        """Stream job logs asynchronously (includes runtime env setup logs).

        Streams logs in real-time, including runtime environment setup progress.

        Args:
            job_id: Job ID from submit().

        Yields:
            Log lines as they become available.

        Example:
            >>> async for line in executor.stream_logs_async(job_id):
            ...     print(line, end='')
        """
        client = self._get_client()
        async for lines in client.tail_job_logs(job_id):
            yield lines

    def get_result(self, job_id: str, timeout: float | None = None) -> Any:
        """Get job result (blocks until complete).

        Parses the result from the job output logs.

        Args:
            job_id: Job ID from submit().
            timeout: Optional timeout in seconds.

        Returns:
            Action result parsed from job output.

        Raises:
            ExecutionError: If job failed or result cannot be parsed.
        """
        import time

        client = self._get_client()
        start_time = time.time()

        while True:
            status = client.get_job_status(job_id)

            if status.is_terminal():
                if str(status) in ('SUCCEEDED', 'JobStatus.SUCCEEDED'):
                    # Parse result from logs
                    logs = client.get_job_logs(job_id)
                    return self._parse_result_from_logs(logs, job_id)
                else:
                    logs = client.get_job_logs(job_id)
                    raise ExecutionError(f'Job {job_id} failed with status {status}. Logs:\n{logs}')

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    raise ExecutionError(f'Job {job_id} timed out after {timeout}s')

            time.sleep(1)

    def _parse_result_from_logs(self, logs: str, job_id: str) -> Any:
        """Parse result from job output logs.

        Args:
            logs: Full job logs.
            job_id: Job ID for error messages.

        Returns:
            Parsed result dict.

        Raises:
            ExecutionError: If result markers not found or parsing fails.
        """
        import json

        start_marker = '__SYNAPSE_RESULT_START__'
        end_marker = '__SYNAPSE_RESULT_END__'

        start_idx = logs.find(start_marker)
        end_idx = logs.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            raise ExecutionError(
                f'Could not parse result from job {job_id} logs. Result markers not found. Logs:\n{logs}'
            )

        result_json = logs[start_idx + len(start_marker) : end_idx].strip()
        try:
            return json.loads(result_json)
        except json.JSONDecodeError as e:
            raise ExecutionError(f'Failed to parse result JSON from job {job_id}: {e}') from e

    def wait(
        self,
        job_id: str,
        timeout_seconds: float = 300,
        poll_interval: float = 1.0,
    ) -> str:
        """Wait for job to complete.

        Args:
            job_id: Job ID from submit().
            timeout_seconds: Maximum time to wait.
            poll_interval: Time between status checks.

        Returns:
            Final job status as string.

        Raises:
            ExecutionError: If job fails or times out.
        """
        import time

        client = self._get_client()
        start_time = time.time()

        while True:
            status = client.get_job_status(job_id)

            if status.is_terminal():
                return str(status)

            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                raise ExecutionError(f'Job {job_id} timed out after {timeout_seconds}s')

            time.sleep(poll_interval)

    def stop(self, job_id: str) -> bool:
        """Stop a running job.

        Args:
            job_id: Job ID from submit().

        Returns:
            True if stop was successful.
        """
        client = self._get_client()
        return client.stop_job(job_id)

    def delete(self, job_id: str) -> bool:
        """Delete job info (only for terminal jobs).

        Args:
            job_id: Job ID from submit().

        Returns:
            True if deletion was successful.
        """
        client = self._get_client()
        return client.delete_job(job_id)


__all__ = ['RayJobsApiExecutor']
