"""Deployment action base class for Ray Serve deployments."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.inference.context import DeploymentContext
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.agent import AgentClient
    from synapse_sdk.clients.backend import BackendClient


class DeploymentProgressCategories:
    """Standard progress category names for deployment workflows.

    Use these constants with set_progress() to track deployment phases:
        - INITIALIZE: Ray cluster initialization
        - DEPLOY: Deploying to Ray Serve
        - REGISTER: Registering with backend

    Example:
        >>> self.set_progress(1, 3, self.progress.INITIALIZE)
        >>> self.set_progress(2, 3, self.progress.DEPLOY)
    """

    INITIALIZE: str = 'initialize'
    DEPLOY: str = 'deploy'
    REGISTER: str = 'register'


class BaseDeploymentAction(BaseAction[P]):
    """Base class for Ray Serve deployment actions.

    Provides helper methods for deploying inference endpoints to Ray Serve.
    Handles Ray initialization, deployment creation, and backend registration.

    Supports two execution modes:
    1. Simple execute: Override execute() directly for simple deployments
    2. Step-based: Override setup_steps() to register workflow steps

    Attributes:
        progress: Standard progress category names.
        entrypoint: The serve deployment class to deploy (set in subclass).

    Example (simple execute):
        >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
        ...     action_name = 'deployment'
        ...     category = 'neural_net'
        ...     params_model = MyParams
        ...     entrypoint = MyServeDeployment
        ...
        ...     def execute(self) -> dict[str, Any]:
        ...         self.ray_init()
        ...         self.set_progress(1, 3, self.progress.INITIALIZE)
        ...         self.deploy()
        ...         self.set_progress(2, 3, self.progress.DEPLOY)
        ...         app_id = self.register_serve_application()
        ...         self.set_progress(3, 3, self.progress.REGISTER)
        ...         return {'serve_application': app_id}

    Example (step-based):
        >>> class MyDeploymentAction(BaseDeploymentAction[MyParams]):
        ...     entrypoint = MyServeDeployment
        ...
        ...     def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
        ...         registry.register(InitializeRayStep())
        ...         registry.register(DeployStep())
        ...         registry.register(RegisterStep())
    """

    progress = DeploymentProgressCategories()

    # Override in subclass with your serve deployment class
    entrypoint: type | None = None

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError('No client in context. Provide a client via RuntimeContext.')
        return self.ctx.client

    @property
    def agent_client(self) -> AgentClient:
        """Agent client from context.

        Returns:
            AgentClient instance for Ray operations.

        Raises:
            RuntimeError: If no agent_client in context.
        """
        if self.ctx.agent_client is None:
            raise RuntimeError('No agent_client in context. Provide an agent_client via RuntimeContext.')
        return self.ctx.agent_client

    def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method to register custom steps for deployment workflow.
        If steps are registered, step-based execution takes precedence.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[DeploymentContext]) -> None:
            ...     registry.register(InitializeRayStep())
            ...     registry.register(DeployStep())
            ...     registry.register(RegisterStep())
        """
        pass  # Default: no steps, uses simple execute()

    def create_context(self) -> DeploymentContext:
        """Create deployment context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            DeploymentContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return DeploymentContext(
            runtime_ctx=self.ctx,
            params=params_dict,
            model_id=params_dict.get('model_id'),
            serve_app_name=self.get_serve_app_name(),
            route_prefix=self.get_route_prefix(),
            ray_actor_options=self.get_ray_actor_options(),
        )

    def run(self) -> Any:
        """Run the action, using steps if registered.

        This method is called by executors. It checks if steps are
        registered and uses step-based execution if so.

        Returns:
            Action result (dict or any return type).
        """
        # Check if steps are registered
        registry: StepRegistry[DeploymentContext] = StepRegistry()
        self.setup_steps(registry)

        if registry:
            # Step-based execution
            context = self.create_context()
            orchestrator: Orchestrator[DeploymentContext] = Orchestrator(
                registry=registry,
                context=context,
                progress_callback=lambda curr, total: self.set_progress(curr, total),
            )
            result = orchestrator.execute()

            # Add context data to result
            if context.serve_app_id:
                result['serve_application'] = context.serve_app_id
            result['deployed'] = context.deployed

            return result

        # Simple execute mode
        return self.execute()

    def get_serve_app_name(self) -> str:
        """Get the name for the Ray Serve application.

        Priority:
        1. SYNAPSE_PLUGIN_RELEASE_CODE env var
        2. Computed from config.yaml: {plugin_code}@{version}

        Returns:
            Serve application name (e.g., 'my_plugin@1.0.0').

        Raises:
            RuntimeError: If neither env var nor config.yaml is available.
        """
        # Try env var first
        if code := self.ctx.env.get_str('SYNAPSE_PLUGIN_RELEASE_CODE'):
            return code

        # Compute from config.yaml
        import os
        from pathlib import Path

        from synapse_sdk.plugins.discovery import PluginDiscovery

        config_path = Path(os.getcwd()) / 'config.yaml'
        if config_path.exists():
            discovery = PluginDiscovery.from_path(config_path)
            return f'{discovery.config.code}@{discovery.config.version}'

        raise RuntimeError(
            'Cannot determine serve app name. Set SYNAPSE_PLUGIN_RELEASE_CODE env var '
            'or ensure config.yaml exists in working directory.'
        )

    def get_route_prefix(self) -> str:
        """Get the route prefix for the deployment.

        Priority:
        1. SYNAPSE_PLUGIN_RELEASE_CHECKSUM env var
        2. MD5 hash of get_serve_app_name()

        Returns:
            Route prefix string (e.g., '/a1b2c3d4e5f6...').
        """
        # Try env var first
        if checksum := self.ctx.env.get_str('SYNAPSE_PLUGIN_RELEASE_CHECKSUM'):
            return f'/{checksum}'

        # Compute MD5 hash of app name
        import hashlib

        app_name = self.get_serve_app_name()
        md5_hash = hashlib.md5(app_name.encode('utf-8')).hexdigest()
        return f'/{md5_hash}'

    def get_ray_actor_options(self) -> dict[str, Any]:
        """Get Ray actor options for the deployment.

        Default extracts num_cpus and num_gpus from params.
        Override for custom resource allocation.

        Returns:
            Dict with Ray actor options (num_cpus, num_gpus, etc.).
        """
        options: dict[str, Any] = {
            'runtime_env': self.get_runtime_env(),
        }

        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)

        for option in ['num_cpus', 'num_gpus', 'memory']:
            if value := params_dict.get(option):
                options[option] = value

        return options

    def get_runtime_env(self) -> dict[str, Any]:
        """Get Ray runtime environment.

        By default, reads requirements.txt from the current working directory
        and builds a runtime_env with those packages. Respects the package_manager
        setting from config.yaml (pip or uv).

        Returns:
            Dict with runtime environment configuration.
        """
        import os
        import shlex
        from pathlib import Path

        from synapse_sdk.plugins.discovery import PluginDiscovery
        from synapse_sdk.plugins.enums import PackageManager
        from synapse_sdk.plugins.executors.ray.base import read_requirements

        # Try to read requirements.txt from current working directory
        cwd = Path(os.getcwd())
        req_file = cwd / 'requirements.txt'

        requirements = read_requirements(req_file)
        if not requirements:
            return {}

        # Split packages and pip options
        packages = []
        pip_args = []
        for req in requirements:
            stripped = req.strip()
            if stripped.startswith('-'):
                pip_args.append(stripped)
            else:
                packages.append(stripped)

        if not packages:
            return {}

        # Split pip args (e.g., "--extra-index-url https://foo" -> ["--extra-index-url", "https://foo"])
        split_pip_args = []
        for arg in pip_args:
            split_pip_args.extend(shlex.split(arg))

        # Read package_manager from config.yaml (defaults to pip)
        package_manager = PackageManager.PIP
        config_path = cwd / 'config.yaml'
        if config_path.exists():
            try:
                discovery = PluginDiscovery.from_path(config_path)
                package_manager = discovery.config.package_manager
            except Exception:
                pass  # Use default if config parsing fails

        # Build runtime_env based on package_manager setting
        if package_manager == PackageManager.UV:
            runtime_env: dict[str, Any] = {
                'uv': {
                    'packages': packages,
                    'uv_pip_install_options': split_pip_args + ['--no-cache'] if split_pip_args else ['--no-cache'],
                }
            }
        else:
            # pip (default)
            runtime_env = {
                'pip': {
                    'packages': packages,
                    'pip_install_options': split_pip_args + ['--upgrade'] if split_pip_args else ['--upgrade'],
                }
            }

        return runtime_env

    def ray_init(self, **kwargs: Any) -> None:
        """Initialize Ray cluster connection.

        Call this before deploying to ensure Ray is connected.

        Args:
            **kwargs: Additional arguments for ray.init().
        """
        try:
            import ray
        except ImportError:
            raise ImportError("Ray is required for deployment actions. Install with: pip install 'synapse-sdk[ray]'")

        if not ray.is_initialized():
            ray.init(**kwargs)

    def deploy(self) -> None:
        """Deploy the inference endpoint to Ray Serve.

        Uses the entrypoint class and current configuration to create
        a Ray Serve deployment.

        Raises:
            RuntimeError: If entrypoint is not set.
            ImportError: If Ray Serve is not installed.
        """
        if self.entrypoint is None:
            raise RuntimeError(
                'entrypoint must be set to a serve deployment class. Example: entrypoint = MyServeDeployment'
            )

        try:
            from ray import serve
        except ImportError:
            raise ImportError(
                "Ray Serve is required for deployment actions. Install with: pip install 'synapse-sdk[ray]'"
            )

        # Get deployment configuration
        app_name = self.get_serve_app_name()
        route_prefix = self.get_route_prefix()
        ray_actor_options = self.get_ray_actor_options()

        # Delete existing deployment if present
        try:
            serve.delete(app_name)
        except Exception:
            pass  # Ignore if not exists

        # Get backend URL for the deployment
        backend_url = (
            self.ctx.env.get_str('SYNAPSE_PLUGIN_RUN_HOST', '') or self.ctx.env.get_str('SYNAPSE_HOST', '') or ''
        )

        # Apply serve.ingress if the entrypoint has a FastAPI app
        deployment_cls = self.entrypoint
        if hasattr(deployment_cls, 'app') and deployment_cls.app is not None:
            deployment_cls = serve.ingress(deployment_cls.app)(deployment_cls)

        # Create and deploy
        # The entrypoint should be a class that implements BaseServeDeployment
        deployment = serve.deployment(ray_actor_options=ray_actor_options)(deployment_cls).bind(backend_url)

        serve.run(
            deployment,
            name=app_name,
            route_prefix=route_prefix,
        )

    def register_serve_application(self) -> int | None:
        """Register the serve application with the backend.

        Creates a serve application record in the backend for tracking.

        Returns:
            Serve application ID if created, None otherwise.
        """
        job_id = self.ctx.job_id
        if not job_id:
            return None

        app_name = self.get_serve_app_name()

        # Get serve application status from Ray
        try:
            serve_app = self.agent_client.get_serve_application(app_name)
        except Exception:
            return None

        # Register with backend
        result = self.client.create_serve_application({
            'job': job_id,
            'status': serve_app.get('status'),
            'data': serve_app,
        })

        return result.get('id')
