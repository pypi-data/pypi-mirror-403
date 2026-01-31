"""Base class for Ray executors with shared runtime env logic."""

from __future__ import annotations

import logging
import shlex
from pathlib import Path
from typing import Any, Literal

from synapse_sdk.plugins.context import PluginEnvironment
from synapse_sdk.plugins.enums import PackageManager

logger = logging.getLogger(__name__)


def read_requirements(file_path: str | Path) -> list[str] | None:
    """Read and parse a requirements.txt file.

    Args:
        file_path: Path to the requirements.txt file.

    Returns:
        List of requirement strings, or None if file doesn't exist.
    """
    path = Path(file_path)
    print(f'[SDK] read_requirements: file_path={path}, exists={path.exists()}', flush=True)
    if not path.exists():
        print('[SDK] read_requirements: file does not exist, returning None', flush=True)
        return None

    requirements = []
    raw_text = path.read_text()
    print(f'[SDK] read_requirements: raw file content:\n{raw_text}', flush=True)
    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            requirements.append(stripped)
    print(f'[SDK] read_requirements: parsed requirements={requirements}', flush=True)
    return requirements


class BaseRayExecutor:
    """Base class for Ray executors with shared runtime env building logic."""

    def __init__(
        self,
        env: PluginEnvironment | dict[str, Any] | None = None,
        *,
        runtime_env: dict[str, Any] | None = None,
        working_dir: str | Path | None = None,
        requirements_file: str | Path | None = None,
        package_manager: PackageManager | Literal['pip', 'uv'] = PackageManager.PIP,
        package_manager_options: list[str] | None = None,
        wheels_dir: str = 'wheels',
        ray_address: str = 'auto',
        include_sdk: bool = False,
    ) -> None:
        """Initialize base Ray executor.

        Args:
            env: Environment config for the action. If None, loads from os.environ.
            runtime_env: Ray runtime environment config.
            working_dir: Plugin working directory.
            requirements_file: Path to requirements.txt.
            package_manager: Package manager to use ('pip' or 'uv').
            package_manager_options: Additional options for the package manager.
            wheels_dir: Directory containing .whl files relative to working_dir.
            ray_address: Ray cluster address (for detecting remote mode).
            include_sdk: If True, bundle local SDK with upload (for development).
        """
        if env is None:
            self._env = PluginEnvironment.from_environ()
        elif isinstance(env, dict):
            self._env = PluginEnvironment(env)
        else:
            self._env = env

        self._runtime_env = runtime_env or {}
        self._working_dir = Path(working_dir) if working_dir else None
        self._requirements_file = Path(requirements_file) if requirements_file else None
        self._package_manager = PackageManager(package_manager)
        self._package_manager_options = package_manager_options
        self._wheels_dir = wheels_dir
        self._ray_address = ray_address
        self._include_sdk = include_sdk
        self._gcs_uri: str | None = None  # Cached GCS URI

    def _ray_init(self) -> None:
        """Initialize Ray connection with SDK bundling if requested."""
        import ray

        if ray.is_initialized():
            return

        # Build init kwargs
        init_kwargs: dict[str, Any] = {
            'address': self._ray_address,
            'ignore_reinit_error': True,
        }

        # Build runtime_env for init level
        runtime_env: dict[str, Any] = {}

        # Include SDK at init level (directories only work here, not at actor level)
        if self._include_sdk:
            import synapse_sdk

            sdk_path = str(Path(synapse_sdk.__file__).parent)
            runtime_env['py_modules'] = [sdk_path]

        # Include working_dir at init level for local mode
        # (local paths are only supported at ray.init() level, not at actor level)
        if self._working_dir and not self._is_remote_cluster():
            runtime_env['working_dir'] = str(self._working_dir)

        if runtime_env:
            init_kwargs['runtime_env'] = runtime_env

        ray.init(**init_kwargs)

    def _is_remote_cluster(self) -> bool:
        """Check if connecting to a remote Ray cluster."""
        # Remote if address starts with ray:// protocol
        return self._ray_address.startswith('ray://')

    def _get_working_dir_uri(self) -> str | None:
        """Get working directory URI, uploading to GCS.

        Ray requires URIs (not local paths) for actor-level runtime_env.
        This method uploads the working directory to Ray's GCS and returns
        a gcs:// URI that works for both local and remote clusters.
        """
        if not self._working_dir:
            return None

        # Always upload to GCS - Ray requires URIs at actor level
        if self._gcs_uri is None:
            from synapse_sdk.plugins.executors.ray.packaging import upload_working_dir_to_gcs

            self._gcs_uri = upload_working_dir_to_gcs(self._working_dir)
        return self._gcs_uri

    def _build_runtime_env(self) -> dict[str, Any]:
        """Build runtime environment with working_dir, requirements, and env vars."""
        print(f'[SDK] _build_runtime_env: starting with _working_dir={self._working_dir}', flush=True)
        print(f'[SDK] _build_runtime_env: initial _runtime_env={self._runtime_env}', flush=True)
        runtime_env = {**self._runtime_env}

        # Set working_dir if provided - must be a URI for actor-level runtime_env
        # Ray only allows local paths at ray.init() level, not at actor level
        if self._working_dir and 'working_dir' not in runtime_env:
            working_dir_uri = self._get_working_dir_uri()
            print(f'[SDK] _build_runtime_env: working_dir_uri={working_dir_uri}', flush=True)
            if working_dir_uri:
                runtime_env['working_dir'] = working_dir_uri

        # Build package manager config with requirements and wheels
        pm_key = str(self._package_manager)  # 'pip' or 'uv'
        raw_requirements = self._get_requirements() or []
        print(f'[SDK] _build_runtime_env: raw_requirements={raw_requirements}', flush=True)
        wheel_files = self._get_wheel_files()
        print(f'[SDK] _build_runtime_env: wheel_files={wheel_files}', flush=True)

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
            # Initialize package manager config
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

        # Add pip args to options (e.g., --extra-index-url)
        # Split args like "--extra-index-url https://foo" into separate tokens
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
                    # Extend existing options, avoid duplicates
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

        # Log the final runtime_env (excluding sensitive env_vars)
        log_runtime_env = {k: v for k, v in runtime_env.items() if k != 'env_vars'}
        print(f'[SDK] _build_runtime_env: final runtime_env (excl env_vars)={log_runtime_env}', flush=True)

        return runtime_env

    def _get_package_manager_options(self) -> dict[str, Any]:
        """Get package manager options with defaults.

        Returns:
            Dict of package manager options.
        """
        user_options = self._package_manager_options or []

        if self._package_manager == PackageManager.UV:
            defaults = ['--no-cache']
            options_list = defaults.copy()
            for opt in user_options:
                if opt not in options_list:
                    options_list.append(opt)
            return {'uv_pip_install_options': options_list}
        else:
            # pip - use pip_install_options with --upgrade flag
            defaults = ['--upgrade']
            options_list = defaults.copy()
            for opt in user_options:
                if opt not in options_list:
                    options_list.append(opt)
            return {'pip_install_options': options_list}

    def _get_requirements(self) -> list[str] | None:
        """Get requirements from file.

        Returns:
            List of requirements, or None if no requirements file found.
        """
        print(f'[SDK] _get_requirements: _requirements_file={self._requirements_file}', flush=True)
        print(f'[SDK] _get_requirements: _working_dir={self._working_dir}', flush=True)

        # Explicit requirements file takes priority
        if self._requirements_file:
            print('[SDK] _get_requirements: using explicit requirements file', flush=True)
            return read_requirements(self._requirements_file)

        # Auto-discover from working_dir
        if self._working_dir:
            req_path = self._working_dir / 'requirements.txt'
            print(f'[SDK] _get_requirements: auto-discovering from {req_path}', flush=True)
            return read_requirements(req_path)

        print('[SDK] _get_requirements: no requirements file found', flush=True)
        return None

    def _get_requirements_file_path(self) -> Path | None:
        """Get path to requirements.txt file if it exists.

        Returns:
            Path to requirements.txt, or None if not found.
        """
        if self._requirements_file and Path(self._requirements_file).exists():
            return Path(self._requirements_file)

        if self._working_dir:
            req_path = self._working_dir / 'requirements.txt'
            if req_path.exists():
                return req_path

        return None

    def _get_wheel_files(self) -> list[str]:
        """Get wheel file paths for Ray runtime env.

        Scans the wheels_dir for .whl files and returns them as Ray-compatible
        paths using ${RAY_RUNTIME_ENV_CREATE_WORKING_DIR}.

        Returns:
            List of wheel file paths for Ray.
        """
        if not self._working_dir:
            return []

        wheels_path = self._working_dir / self._wheels_dir
        if not wheels_path.exists():
            return []

        wheel_files = []
        for whl in wheels_path.glob('*.whl'):
            # Use Ray's working dir variable for the path
            ray_path = f'${{RAY_RUNTIME_ENV_CREATE_WORKING_DIR}}/{self._wheels_dir}/{whl.name}'
            wheel_files.append(ray_path)

        return wheel_files


__all__ = ['BaseRayExecutor', 'read_requirements']
