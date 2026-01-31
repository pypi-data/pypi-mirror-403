"""Export context for sharing state between workflow steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

from synapse_sdk.plugins.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.loggers import BaseLogger
    from synapse_sdk.plugins.actions.export.exporter import BaseExporter
    from synapse_sdk.plugins.actions.export.handlers import ExportTargetHandler


@dataclass
class ExportContext(BaseStepContext):
    """Shared context passed between export workflow steps.

    Extends BaseStepContext with export-specific state fields.
    Carries parameters and accumulated state as the workflow
    progresses through steps.

    Attributes:
        params: Export parameters (from action params).
        results: Fetched results to export (populated by fetch step).
        total_count: Total number of items to export.
        exported_count: Number of items successfully exported.
        failed_count: Number of items that failed to export.
        output_path: Path to export output file/directory.
        export_items: Generator of items to export.
        path_root: Root path for export output.
        storage: Storage configuration for export.
        configuration: Project configuration.
        project_id: Project ID from filter.
        handler: Target handler for the export (populated by FetchResultsStep).
        unique_export_path: Unique export directory path (populated by InitializeStep).
        output_paths: Output directory paths (json, origin_files).
        export_params: Built export parameters (populated by PrepareExportStep).
        exporter: BaseExporter instance for data conversion and file saving.
        converted_items: List of converted data items (populated by ConvertDataStep).
        errors_json: List of JSON file save errors.
        errors_original: List of original file save errors.
        config: Action configuration dict.

    Example:
        >>> context = ExportContext(
        ...     runtime_ctx=runtime_ctx,
        ...     params={'format': 'coco', 'filter': {'project': 123}},
        ... )
        >>> # Steps populate state as they execute
        >>> context.results = fetched_data
        >>> context.export_items = export_generator
    """

    # Export parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    results: Any | None = None
    total_count: int = 0
    exported_count: int = 0
    failed_count: int = 0
    output_path: str | None = None

    # Export-specific state
    export_items: Generator | None = None
    path_root: Path | None = None
    storage: dict[str, Any] | None = None
    configuration: dict[str, Any] | None = None
    project_id: int | None = None

    # Step workflow state (populated by steps)
    handler: ExportTargetHandler | None = None
    unique_export_path: Path | None = None
    output_paths: dict[str, Path] = field(default_factory=dict)
    export_params: dict[str, Any] = field(default_factory=dict)
    exporter: BaseExporter | None = None
    converted_items: list[dict[str, Any]] = field(default_factory=list)
    errors_json: list[Any] = field(default_factory=list)
    errors_original: list[Any] = field(default_factory=list)
    config: dict[str, Any] = field(default_factory=dict)

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
    def logger(self) -> BaseLogger:
        """Logger from runtime context.

        Returns:
            BaseLogger instance.
        """
        return self.runtime_ctx.logger
