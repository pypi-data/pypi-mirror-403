from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Union

if TYPE_CHECKING:
    from synapse_sdk.clients.protocols import ClientProtocol


class ContainerClientMixin:
    """Mixin for container management endpoints."""

    # Build management
    def get_build_status(self: ClientProtocol, build_id: str) -> dict:
        """Get the status of an async container build.

        Args:
            build_id: The build ID returned from create_container.

        Returns:
            dict: Build status including 'status', 'result', 'error' fields.
        """
        return self._get(f'builds/{build_id}/')

    def wait_for_build(
        self: ClientProtocol,
        build_id: str,
        *,
        timeout: float = 300,
        poll_interval: float = 2,
    ) -> dict:
        """Wait for an async build to complete.

        Args:
            build_id: The build ID to wait for.
            timeout: Maximum time to wait in seconds (default: 300).
            poll_interval: Time between status checks in seconds (default: 2).

        Returns:
            dict: The completed build result with container info.

        Raises:
            TimeoutError: If build doesn't complete within timeout.
            RuntimeError: If build fails.
        """
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f'Build {build_id} did not complete within {timeout}s')

            status = self.get_build_status(build_id)
            build_status = status.get('status', '')

            if build_status == 'completed':
                return status.get('result', {})
            elif build_status in ('failed', 'cancelled'):
                error = status.get('error', 'Unknown error')
                raise RuntimeError(f'Build {build_id} failed: {error}')

            time.sleep(poll_interval)

    # Docker containers
    def list_docker_containers(self: ClientProtocol) -> list[dict]:
        """List all Docker containers on the host."""
        return self._get('containers/docker/')

    def get_docker_container(self: ClientProtocol, container_id: str) -> dict:
        """Get a specific Docker container by ID."""
        return self._get(f'containers/docker/{container_id}')

    def create_docker_container(
        self: ClientProtocol,
        plugin_release: str,
        *,
        params: dict[str, Any] | None = None,
        envs: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        """Build and run a Docker container for a plugin.

        Args:
            plugin_release: Plugin identifier (e.g., "plugin_code@version").
            params: Parameters forwarded to the plugin.
            envs: Environment variables injected into the container.
            metadata: Additional metadata stored with the container record.
            labels: Container labels for display or filtering.
        """
        data = {'plugin_release': plugin_release}
        if params is not None:
            data['params'] = params
        if envs is not None:
            data['envs'] = envs
        if metadata is not None:
            data['metadata'] = metadata
        if labels is not None:
            data['labels'] = labels

        return self._post('containers/docker/', data=data)

    def delete_docker_container(self: ClientProtocol, container_id: str) -> None:
        """Stop and remove a Docker container."""
        self._delete(f'containers/docker/{container_id}')

    def create_container(
        self,
        plugin_release: Optional[Union[str, Any]] = None,
        *,
        model: Optional[int] = None,
        params: Optional[Dict[str, Any]] = None,
        envs: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        labels: Optional[Iterable[str]] = None,
        plugin_file: Optional[Union[str, Path]] = None,
        wait: bool = True,
        timeout: float = 300,
    ):
        """Create a Docker container running a plugin Gradio interface.

        Container builds run asynchronously. By default, this method waits for
        the build to complete and returns the final container info with endpoint.

        Args:
            plugin_release: Plugin identifier. Accepts either ``synapse_sdk.plugins.models.PluginRelease``
                instances or the ``"<plugin_code>@<version>"`` shorthand string.
            model: Optional model ID to associate with the container. Used together with
                ``plugin_release`` to uniquely identify a container for restart behavior.
            params: Arbitrary parameters forwarded to ``plugin/gradio_interface.py``.
            envs: Extra environment variables injected into the container.
            metadata: Additional metadata stored with the container record.
            labels: Optional container labels/tags for display or filtering.
            plugin_file: Optional path to a packaged plugin release to upload directly.
                The archive must contain ``plugin/gradio_interface.py``.
            wait: If True (default), wait for build to complete and return container info.
                If False, return immediately with build_id and streaming URLs.
            timeout: Maximum time to wait for build completion in seconds (default: 300).
                Only used when wait=True.

        Returns:
            dict: If wait=True, returns container info with 'endpoint', 'id', 'status', etc.
                If wait=False, returns build info with 'build_id', 'ws_url', 'sse_url', 'status_url'.

        Raises:
            FileNotFoundError: If ``plugin_file`` is provided but does not exist.
            ValueError: If neither ``plugin_release`` nor ``plugin_file`` are provided.
            TimeoutError: If wait=True and build doesn't complete within timeout.
            RuntimeError: If wait=True and build fails.
        """
        if not plugin_release and not plugin_file:
            raise ValueError('Either "plugin_release" or "plugin_file" must be provided to create a container.')

        data: Dict[str, Any] = {}

        if plugin_release:
            data.update(self._serialize_plugin_release(plugin_release))

        if model is not None:
            data['model'] = model

        optional_payload = {
            'params': params if params is not None else None,
            'envs': envs or None,
            'metadata': metadata or None,
            'labels': list(labels) if labels else None,
        }
        data.update({key: value for key, value in optional_payload.items() if value is not None})

        files = None
        if plugin_file:
            file_path = Path(plugin_file)
            if not file_path.exists():
                raise FileNotFoundError(f'Plugin release file not found: {file_path}')
            files = {'file': file_path}
        post_kwargs = {'data': data}
        if files:
            post_kwargs['files'] = files

        response = self._post('containers/', **post_kwargs)

        # If wait=False, return the async build response immediately
        if not wait:
            return response

        # Wait for build to complete and return container info
        build_id = response.get('build_id')
        if not build_id:
            # Fallback for sync response (shouldn't happen with new API)
            return response

        return self.wait_for_build(build_id, timeout=timeout)

    @staticmethod
    def _serialize_plugin_release(plugin_release: Union[str, Any]) -> Dict[str, Any]:
        """Normalize plugin release data for API payloads."""
        if hasattr(plugin_release, 'code') and hasattr(plugin_release, 'version'):
            payload = {
                'plugin_release': plugin_release.code,
                'plugin': getattr(plugin_release, 'plugin', None),
                'version': plugin_release.version,
            }

            # Extract action and entrypoint from the first action in the config
            if hasattr(plugin_release, 'config') and 'actions' in plugin_release.config:
                actions = plugin_release.config['actions']
                if actions:
                    # Get the first action (typically 'gradio')
                    action_name = next(iter(actions.keys()))
                    action_config = actions[action_name]
                    payload['action'] = action_name

                    # Convert entrypoint from dotted path to file path
                    if 'entrypoint' in action_config:
                        entrypoint = action_config['entrypoint']
                        # Convert 'plugin.gradio_interface.app' to 'plugin/gradio_interface.py'
                        file_path = entrypoint.rsplit('.', 1)[0].replace('.', '/') + '.py'
                        payload['entrypoint'] = file_path

            return payload

        if isinstance(plugin_release, str):
            payload = {'plugin_release': plugin_release}
            if '@' in plugin_release:
                plugin, version = plugin_release.rsplit('@', 1)
                payload.setdefault('plugin', plugin)
                payload.setdefault('version', version)
            return payload

        raise TypeError('plugin_release must be a PluginRelease instance or a formatted string "code@version"')

    # Database container records
    def list_containers(
        self: ClientProtocol,
        params: dict | None = None,
        *,
        list_all: bool = False,
    ) -> dict | tuple[Any, int]:
        """List tracked containers from database."""
        return self._list('containers/', params=params, list_all=list_all)

    def get_container(self: ClientProtocol, container_id: int) -> dict:
        """Get a tracked container by database ID."""
        return self._get(f'containers/{container_id}')

    def update_container(
        self: ClientProtocol,
        container_id: int,
        *,
        status: str | None = None,
    ) -> dict:
        """Update a tracked container's status."""
        data = {}
        if status is not None:
            data['status'] = status
        return self._patch(f'containers/{container_id}', data=data)

    def delete_container(self: ClientProtocol, container_id: int) -> None:
        """Delete a tracked container (stops Docker container too)."""
        self._delete(f'containers/{container_id}')
