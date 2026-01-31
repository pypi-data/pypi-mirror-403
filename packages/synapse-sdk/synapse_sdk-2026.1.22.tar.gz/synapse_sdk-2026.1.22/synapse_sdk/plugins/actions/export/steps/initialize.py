"""Initialize step for export workflow."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.utils.storage import get_pathlib

if TYPE_CHECKING:
    from upath import UPath


class InitializeStep(BaseStep[ExportContext]):
    """Initialize export workflow by setting up storage and paths.

    This step:
    1. Validates and retrieves storage configuration
    2. Sets up the working directory path
    3. Creates unique export directory
    4. Sets up output directories (json, origin_files)

    Progress weight: 0.05 (5%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'initialize'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.05

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (5%)."""
        return 5

    def execute(self, context: ExportContext) -> StepResult:
        """Execute initialization step.

        Args:
            context: Export context with params and client.

        Returns:
            StepResult with storage and path_root in data.
        """
        # 1. Get and validate storage
        storage_id = context.params.get('storage')
        if storage_id is None:
            return StepResult(
                success=False,
                error='Storage parameter is required',
            )

        try:
            storage = context.client.get_storage(storage_id)
            context.storage = storage.model_dump()
        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to get storage {storage_id}: {e}',
            )

        # 2. Setup path
        path = context.params.get('path')
        if path is None:
            return StepResult(
                success=False,
                error='Path parameter is required',
            )

        try:
            storage_config = context.storage
            pathlib_cwd: Path | UPath = get_pathlib(storage_config, path)
            context.path_root = pathlib_cwd
        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to setup path {path}: {e}',
            )

        # 3. Create unique export directory
        export_name = context.params.get('name', 'export')
        try:
            context.unique_export_path = self._create_unique_export_path(context.path_root, export_name)
        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to create export directory: {e}',
            )

        # 4. Setup output directories
        save_original_file = context.params.get('save_original_file', False)
        try:
            context.output_paths = self._setup_output_directories(context.unique_export_path, save_original_file)
        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to setup output directories: {e}',
            )

        context.logger.info(f'Initialized export at {context.unique_export_path}')
        context.log_message(ExportLogMessageCode.EXPORT_INITIALIZED)

        return StepResult(
            success=True,
            data={
                'storage': context.storage,
                'path_root': str(context.path_root),
                'unique_export_path': str(context.unique_export_path),
            },
            rollback_data={
                'unique_export_path': str(context.unique_export_path),
            },
        )

    def can_skip(self, context: ExportContext) -> bool:
        """Initialize step cannot be skipped."""
        return False

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        """Rollback initialization by removing created directories."""
        import shutil

        if result.rollback_data:
            export_path = result.rollback_data.get('unique_export_path')
            if export_path:
                path = Path(export_path)
                if path.exists():
                    shutil.rmtree(path, ignore_errors=True)
                    context.logger.info(f'Rolled back: removed {export_path}')

        context.storage = None
        context.path_root = None
        context.unique_export_path = None
        context.output_paths = {}

    def _create_unique_export_path(self, base_path: Path, base_name: str) -> Path:
        """Create a unique export path to avoid conflicts.

        Args:
            base_path: Root path for export.
            base_name: Base name for the export directory.

        Returns:
            Path to the unique export directory (created).
        """
        export_path = base_path / base_name
        unique_export_path = export_path
        counter = 1
        while unique_export_path.exists():
            unique_export_path = export_path.with_name(f'{export_path.name}({counter})')
            counter += 1
        unique_export_path.mkdir(parents=True)
        return unique_export_path

    def _setup_output_directories(self, unique_export_path: Path, save_original_file: bool) -> dict[str, Path]:
        """Setup output directories for export.

        Args:
            unique_export_path: Base path for export.
            save_original_file: Whether original files will be saved.

        Returns:
            Dictionary containing paths for different file types.
        """
        # Path to save JSON files
        json_output_path = unique_export_path / 'json'
        json_output_path.mkdir(parents=True, exist_ok=True)

        output_paths: dict[str, Path] = {'json_output_path': json_output_path}

        # Path to save original files
        if save_original_file:
            origin_files_output_path = unique_export_path / 'origin_files'
            origin_files_output_path.mkdir(parents=True, exist_ok=True)
            output_paths['origin_files_output_path'] = origin_files_output_path

        return output_paths
