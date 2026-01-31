"""Upload context for sharing state between workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


@dataclass
class UploadContext(BaseStepContext):
    """Shared context passed between upload workflow steps.

    Extends BaseStepContext with upload-specific state fields.
    Carries parameters and accumulated state as the workflow
    progresses through steps.

    Supports both single-path and multi-path modes:

    Single Path Mode (use_single_path=True):
        Uses 'path' and 'is_recursive' from params for all files.

    Multi-Path Mode (use_single_path=False):
        Uses 'assets' dict from params with per-asset path configurations.

    Attributes:
        params: Upload parameters (from action params). Contains:
            - name: Upload operation name
            - description: Optional description
            - use_single_path: Mode selector (True=single, False=multi)
            - path: Base path (single path mode)
            - is_recursive: Recursive search flag (single path mode)
            - assets: Per-asset configs (multi-path mode)
            - storage: Storage ID
            - data_collection: Data collection ID
            - project: Optional project ID
            - excel_metadata_path: Optional Excel metadata path
            - max_file_size_mb: Max file size limit
            - creating_data_unit_batch_size: Batch size for data units
            - use_async_upload: Async upload flag
            - extra_params: Additional parameters
        storage: Storage configuration (populated by init step).
        data_collection: Data collection configuration (populated by init step).
        project: Project configuration (populated by init step).
        pathlib_cwd: Working directory path (populated by init step).
        organized_files: Files organized for upload (populated by organize step).
            Each entry contains file info with source path and asset metadata.
        uploaded_files: Successfully uploaded files (populated by upload step).
        data_units: Created data units (populated by generate step).
        excel_metadata: Parsed Excel metadata (populated by metadata step).

    Example:
        Single Path Mode:
            >>> context = UploadContext(
            ...     runtime_ctx=runtime_ctx,
            ...     params={
            ...         'name': 'My Upload',
            ...         'storage': 1,
            ...         'data_collection': 5,
            ...         'use_single_path': True,
            ...         'path': '/data/images',
            ...         'is_recursive': True,
            ...     },
            ... )

        Multi-Path Mode:
            >>> context = UploadContext(
            ...     runtime_ctx=runtime_ctx,
            ...     params={
            ...         'name': 'Multi-Source Upload',
            ...         'storage': 1,
            ...         'data_collection': 5,
            ...         'use_single_path': False,
            ...         'assets': {
            ...             'image_1': {'path': '/sensors/camera', 'is_recursive': True},
            ...             'pcd_1': {'path': '/sensors/lidar', 'is_recursive': False},
            ...         },
            ...     },
            ... )
    """

    # Upload parameters
    params: dict[str, Any] = field(default_factory=dict)

    # File extension restrictions (set by action's get_allowed_extensions())
    # Maps file_type to list of allowed extensions, e.g. {'video': ['.mp4'], 'image': ['.jpg', '.png']}
    # None means no restriction (uses file_specifications from data collection)
    allowed_extensions: dict[str, list[str]] | None = None

    # Processing state (populated by steps)
    storage: Any | None = None
    data_collection: Any | None = None
    project: Any | None = None
    pathlib_cwd: Path | None = None
    organized_files: list[dict[str, Any]] = field(default_factory=list)
    uploaded_files: list[dict[str, Any]] = field(default_factory=list)
    data_units: list[dict[str, Any]] = field(default_factory=list)
    excel_metadata: dict[str, Any] | None = None

    @property
    def client(self) -> BackendClient:
        """Backend client from runtime context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in runtime context.
        """
        if self.runtime_ctx.client is None:
            raise RuntimeError('No client in runtime context')
        return self.runtime_ctx.client

    @property
    def use_single_path(self) -> bool:
        """Check if single path mode is enabled.

        Returns:
            True if single path mode, False if multi-path mode.
        """
        return self.params.get('use_single_path', True)

    @property
    def upload_name(self) -> str:
        """Get the upload operation name.

        Returns:
            Upload operation name from params.
        """
        return self.params.get('name', 'Unnamed Upload')

    @property
    def max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes.

        Returns:
            Max file size converted from MB to bytes.
        """
        mb = self.params.get('max_file_size_mb', 50)
        return mb * 1024 * 1024

    @property
    def batch_size(self) -> int:
        """Get data unit creation batch size.

        Returns:
            Batch size for creating data units.
        """
        return self.params.get('creating_data_unit_batch_size', 1)

    @property
    def use_async_upload(self) -> bool:
        """Check if async upload is enabled.

        Returns:
            True if async upload is enabled.
        """
        return self.params.get('use_async_upload', True)
