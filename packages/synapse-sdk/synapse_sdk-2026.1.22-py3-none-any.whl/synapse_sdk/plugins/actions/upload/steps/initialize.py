"""Initialize step for upload workflow."""

from __future__ import annotations

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.utils.storage import get_pathlib


class InitializeStep(BaseStep[UploadContext]):
    """Initialize upload workflow by setting up storage and paths.

    This step:
    1. Validates and retrieves storage configuration
    2. Sets up the working directory path (single-path mode)
    3. Prepares the context for subsequent steps

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

    def execute(self, context: UploadContext) -> StepResult:
        """Execute initialization step.

        Args:
            context: Upload context with params and client.

        Returns:
            StepResult with storage and pathlib_cwd in data.
        """
        context.set_progress(0, 1)

        # Get and validate storage
        storage_id = context.params.get('storage')
        if storage_id is None:
            return StepResult(
                success=False,
                error='Storage parameter is required',
            )

        try:
            storage = context.client.get_storage(storage_id)
            context.storage = storage
        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to get storage {storage_id}: {e}',
            )

        # Check operational mode
        use_single_path = context.use_single_path
        path = context.params.get('path')
        pathlib_cwd = None

        # Convert Storage model to dict format for get_pathlib
        storage_config = {
            'provider': storage.provider,
            'configuration': storage.configuration,
        }

        if use_single_path:
            # Single-path mode: path is required
            if path is None:
                return StepResult(
                    success=False,
                    error='Path parameter is required in single-path mode',
                )

            try:
                pathlib_cwd = get_pathlib(storage_config, path)
                context.pathlib_cwd = pathlib_cwd
            except Exception as e:
                return StepResult(
                    success=False,
                    error=f'Failed to get path {path}: {e}',
                )
        else:
            # Multi-path mode: path is optional
            if path:
                try:
                    pathlib_cwd = get_pathlib(storage_config, path)
                    context.pathlib_cwd = pathlib_cwd
                except Exception as e:
                    return StepResult(
                        success=False,
                        error=f'Failed to get path {path}: {e}',
                    )

        # Log initialization
        context.set_progress(1, 1)
        context.log(LogCode.STEP_COMPLETED.value, {'step': self.name})
        context.log_message(UploadLogMessageCode.UPLOAD_INITIALIZED)

        return StepResult(
            success=True,
            data={
                'storage': storage,
                'pathlib_cwd': pathlib_cwd,
            },
            rollback_data={
                'storage_id': storage_id,
                'path': path,
                'use_single_path': use_single_path,
            },
        )

    def can_skip(self, context: UploadContext) -> bool:
        """Initialize step cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback initialization (cleanup if needed)."""
        context.log(LogCode.ROLLBACK_INITIALIZATION.value, {})
        context.storage = None
        context.pathlib_cwd = None
