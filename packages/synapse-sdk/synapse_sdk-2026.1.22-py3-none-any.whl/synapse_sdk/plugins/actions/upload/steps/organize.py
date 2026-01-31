"""Organize files step for upload workflow."""

from __future__ import annotations

from typing import Any

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.actions.upload.strategies import (
    FileDiscoveryStrategy,
    RecursiveFileDiscoveryStrategy,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.utils.storage import get_pathlib


class OrganizeFilesStep(BaseStep[UploadContext]):
    """Organize files according to specifications.

    This step uses a file discovery strategy to:
    1. Discover files in type directories
    2. Organize files by stem (grouping related files)
    3. Match files with metadata

    Supports both single-path and multi-path modes.

    Progress weight: 0.15 (15%)
    """

    def __init__(self, file_discovery_strategy: FileDiscoveryStrategy | None = None):
        """Initialize with optional file discovery strategy.

        Args:
            file_discovery_strategy: Strategy for file discovery.
                Defaults to RecursiveFileDiscoveryStrategy.
        """
        self._file_discovery_strategy = file_discovery_strategy

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'organize_files'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.15

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (15%)."""
        return 15

    def execute(self, context: UploadContext) -> StepResult:
        """Execute file organization step.

        Args:
            context: Upload context with storage, specs, and metadata.

        Returns:
            StepResult with organized_files in data.
        """
        context.set_progress(0, 1)
        strategy = self._file_discovery_strategy or RecursiveFileDiscoveryStrategy()

        # Get file specifications from data_collection
        file_specifications = self._get_file_specifications(context)
        if not file_specifications:
            return StepResult(
                success=False,
                error='File specifications not available',
            )

        try:
            if context.use_single_path:
                return self._execute_single_path_mode(context, strategy, file_specifications)
            else:
                return self._execute_multi_path_mode(context, strategy, file_specifications)

        except Exception as e:
            return StepResult(
                success=False,
                error=f'File organization failed: {e}',
            )

    def _get_file_specifications(self, context: UploadContext) -> list[dict[str, Any]]:
        """Get file specifications from context."""
        if context.data_collection:
            return context.data_collection.get('file_specifications', [])
        return []

    def _execute_single_path_mode(
        self,
        context: UploadContext,
        strategy: FileDiscoveryStrategy,
        file_specifications: list[dict[str, Any]],
    ) -> StepResult:
        """Execute file organization in single path mode."""
        if not context.pathlib_cwd:
            return StepResult(
                success=False,
                error='Working directory path not set in single-path mode',
            )

        # Create type directories mapping
        type_dirs = {}
        for spec in file_specifications:
            spec_name = spec.get('name', '')
            if not spec_name:
                continue
            spec_dir = context.pathlib_cwd / spec_name
            if spec_dir.exists() and spec_dir.is_dir():
                type_dirs[spec_name] = spec_dir

        if type_dirs:
            context.log(
                LogCode.TYPE_DIRECTORIES_FOUND.value,
                {
                    'directories': list(type_dirs.keys()),
                },
            )
        else:
            context.log(LogCode.NO_TYPE_DIRECTORIES.value, {})
            return StepResult(
                success=True,
                data={'organized_files': []},
            )

        context.log(LogCode.TYPE_STRUCTURE_DETECTED.value, {})
        context.log(LogCode.FILE_ORGANIZATION_STARTED.value, {})

        # Discover files in type directories
        all_files = []
        is_recursive = context.params.get('is_recursive', True)

        for spec_name, dir_path in type_dirs.items():
            files_in_dir = strategy.discover(dir_path, is_recursive)
            all_files.extend(files_in_dir)

        if not all_files:
            context.log(LogCode.NO_FILES_FOUND_WARNING.value, {})
            return StepResult(
                success=True,
                data={'organized_files': []},
            )

        # Organize files using strategy
        metadata = context.excel_metadata or {}
        organized_files = strategy.organize(
            all_files,
            file_specifications,
            metadata,
            type_dirs,
        )

        if organized_files:
            context.log(
                LogCode.FILES_DISCOVERED.value,
                {
                    'count': len(organized_files),
                },
            )
            context.organized_files = organized_files
            context.log_message(UploadLogMessageCode.UPLOAD_FILES_ORGANIZED, count=len(organized_files))
        else:
            context.log_message(UploadLogMessageCode.UPLOAD_NO_FILES_FOUND)

        context.set_progress(1, 1)
        return StepResult(
            success=True,
            data={'organized_files': organized_files},
            rollback_data={
                'files_count': len(organized_files),
                'type_dirs': list(type_dirs.keys()),
            },
        )

    def _execute_multi_path_mode(
        self,
        context: UploadContext,
        strategy: FileDiscoveryStrategy,
        file_specifications: list[dict[str, Any]],
    ) -> StepResult:
        """Execute file organization in multi-path mode."""
        assets = context.params.get('assets', {})
        if not assets:
            return StepResult(
                success=False,
                error='Multi-path mode requires assets configuration',
            )

        # Validate required specs have asset paths
        required_specs = [spec['name'] for spec in file_specifications if spec.get('is_required', False)]
        missing_required = [spec for spec in required_specs if spec not in assets]

        if missing_required:
            return StepResult(
                success=False,
                error=f'Multi-path mode requires asset paths for: {", ".join(missing_required)}',
            )

        context.log(
            LogCode.MULTI_PATH_MODE_ENABLED.value,
            {
                'asset_count': len(assets),
            },
        )
        context.log(LogCode.FILE_ORGANIZATION_STARTED.value, {})

        # Collect files from all asset paths
        all_files = []
        type_dirs = {}
        specs_with_files = []

        for spec in file_specifications:
            spec_name = spec.get('name', '')
            is_required = spec.get('is_required', False)

            if spec_name not in assets:
                if is_required:
                    return StepResult(
                        success=False,
                        error=f'Required spec {spec_name} missing asset path',
                    )
                context.log(
                    LogCode.OPTIONAL_SPEC_SKIPPED.value,
                    {
                        'spec': spec_name,
                    },
                )
                continue

            asset_config = assets[spec_name]

            # Get asset path from storage
            try:
                storage_config = {
                    'provider': context.storage.provider,
                    'configuration': context.storage.configuration,
                }
                asset_path = get_pathlib(
                    storage_config,
                    asset_config.get('path', ''),
                )
                type_dirs[spec_name] = asset_path
            except Exception as e:
                context.log(
                    LogCode.ASSET_PATH_ACCESS_ERROR.value,
                    {
                        'spec': spec_name,
                        'error': str(e),
                    },
                )
                continue

            if not asset_path.exists():
                context.log(
                    LogCode.ASSET_PATH_NOT_FOUND.value,
                    {
                        'spec': spec_name,
                        'path': asset_config.get('path', ''),
                    },
                )
                continue

            # Discover files for this asset
            is_recursive = asset_config.get('is_recursive', True)
            context.log(
                LogCode.DISCOVERING_FILES_FOR_ASSET.value,
                {
                    'spec': spec_name,
                    'recursive': is_recursive,
                },
            )

            files = strategy.discover(asset_path, is_recursive)

            if not files:
                context.log(
                    LogCode.NO_FILES_FOUND_FOR_ASSET.value,
                    {
                        'spec': spec_name,
                    },
                )
                continue

            all_files.extend(files)
            specs_with_files.append(spec)
            context.log(
                LogCode.FILES_FOUND_FOR_ASSET.value,
                {
                    'count': len(files),
                    'spec': spec_name,
                },
            )

        # Organize all files together
        organized_files = []
        if all_files and specs_with_files:
            context.log(
                LogCode.ORGANIZING_FILES_MULTI_PATH.value,
                {
                    'file_count': len(all_files),
                    'spec_count': len(specs_with_files),
                },
            )
            context.log(
                LogCode.TYPE_DIRECTORIES_MULTI_PATH.value,
                {
                    'directories': list(type_dirs.keys()),
                },
            )

            metadata = context.excel_metadata or {}
            organized_files = strategy.organize(
                all_files,
                specs_with_files,
                metadata,
                type_dirs,
            )

        if organized_files:
            context.log(
                LogCode.FILES_DISCOVERED.value,
                {
                    'count': len(organized_files),
                },
            )
            context.log(
                LogCode.DATA_UNITS_CREATED_FROM_FILES.value,
                {
                    'data_unit_count': len(organized_files),
                    'file_count': len(all_files),
                },
            )
            context.organized_files = organized_files
            context.log_message(UploadLogMessageCode.UPLOAD_FILES_ORGANIZED, count=len(organized_files))
        else:
            context.log(LogCode.NO_FILES_FOUND_WARNING.value, {})
            context.log_message(UploadLogMessageCode.UPLOAD_NO_FILES_FOUND)

        context.set_progress(1, 1)
        return StepResult(
            success=True,
            data={'organized_files': organized_files},
            rollback_data={
                'files_count': len(organized_files),
                'type_dirs': list(type_dirs.keys()),
            },
        )

    def can_skip(self, context: UploadContext) -> bool:
        """File organization cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback file organization."""
        context.log(LogCode.ROLLBACK_FILE_ORGANIZATION.value, {})
        context.organized_files = []
