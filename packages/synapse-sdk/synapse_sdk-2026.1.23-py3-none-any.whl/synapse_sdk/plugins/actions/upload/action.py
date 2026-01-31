"""Upload action base class with workflow step support."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.steps import (
    AnalyzeCollectionStep,
    CleanupStep,
    GenerateDataUnitsStep,
    InitializeStep,
    OrganizeFilesStep,
    ProcessMetadataStep,
    UploadFilesStep,
    ValidateFilesStep,
)
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode


class BaseUploadAction(BaseAction[P]):
    """Base class for upload actions with workflow step support.

    Provides a full step-based workflow system:
    - Override setup_steps() to register custom steps
    - Steps execute in order with automatic rollback on failure
    - Progress tracked across all steps based on weights

    Attributes:
        category: Plugin category (defaults to UPLOAD).

    File Extension Restrictions:
        Override get_allowed_extensions() to restrict file types by extension.
        This is useful for plugins that only process specific file formats
        (e.g., video-to-image converter only accepts video files).

        Example:
            >>> def get_allowed_extensions(self) -> dict[str, list[str]] | None:
            ...     return {
            ...         'video': ['.mp4', '.avi', '.mov'],
            ...         'image': ['.jpg', '.jpeg', '.png'],
            ...     }

    Example:
        >>> class MyUploadAction(BaseUploadAction[MyParams]):
        ...     action_name = 'upload'
        ...     params_model = MyParams
        ...
        ...     def setup_steps(self, registry: StepRegistry) -> None:
        ...         registry.register(InitializeStep())
        ...         registry.register(ValidateStep())
        ...         registry.register(UploadFilesStep())
        ...         registry.register(CleanupStep())
        >>>
        >>> # Steps are executed in order with automatic rollback on failure
        >>> # Progress is tracked based on step weights
    """

    category = PluginCategory.UPLOAD

    @classmethod
    def get_log_message_code_class(cls) -> type[UploadLogMessageCode]:
        from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode

        return UploadLogMessageCode

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

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        """Register workflow steps.

        Override this method to register custom steps for your upload workflow.
        Steps are executed in registration order.

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
            ...     registry.register(InitializeStep())
            ...     registry.register(ValidateStep())
            ...     registry.register(UploadFilesStep())
        """
        pass  # Subclasses override to add steps

    def get_allowed_extensions(self) -> dict[str, list[str]] | None:
        """Get allowed file extensions by file type.

        Override this method to restrict which file extensions are accepted
        during the validation step. Files with extensions not in this list
        will be filtered out before upload.

        Returns:
            Dict mapping file_type to list of allowed extensions, or None for no restriction.
            Extensions should include the dot prefix (e.g., '.mp4', not 'mp4').
            Extension matching is case-insensitive.

        Example:
            To allow only MP4 and AVI videos, and JPG/PNG images::

                def get_allowed_extensions(self) -> dict[str, list[str]] | None:
                    return {
                        'video': ['.mp4', '.avi'],
                        'image': ['.jpg', '.jpeg', '.png'],
                    }

            To allow all extensions (default behavior)::

                def get_allowed_extensions(self) -> dict[str, list[str]] | None:
                    return None
        """
        return None  # Default: no restriction

    def create_context(self) -> UploadContext:
        """Create upload context for the workflow.

        Override to customize context creation or add additional state.

        Returns:
            UploadContext instance with params, runtime context, and allowed extensions.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return UploadContext(
            params=params_dict,
            runtime_ctx=self.ctx,
            allowed_extensions=self.get_allowed_extensions(),
        )

    def run(self) -> dict[str, Any]:
        """Run the upload workflow.

        Called by executors. Delegates to execute().

        Returns:
            Dict with success status and workflow results.
        """
        return self.execute()

    def execute(self) -> dict[str, Any]:
        """Execute the upload workflow.

        Creates registry, registers steps via setup_steps(), creates context,
        and runs the orchestrator.

        Returns:
            Dict with success status and workflow results.

        Raises:
            RuntimeError: If no steps registered or a step fails.
        """
        # Setup
        registry: StepRegistry[UploadContext] = StepRegistry()
        self.setup_steps(registry)

        if not registry:
            raise RuntimeError('No steps registered. Override setup_steps() to register workflow steps.')

        # Create context and orchestrator
        context = self.create_context()
        orchestrator: Orchestrator[UploadContext] = Orchestrator(
            registry=registry,
            context=context,
            progress_callback=lambda curr, total: self.set_progress(curr, total, category='overall'),
        )

        # Execute workflow
        result = orchestrator.execute()

        # Add upload-specific result data
        result['uploaded_files'] = len(context.uploaded_files)
        result['data_units'] = len(context.data_units)

        return result


class DefaultUploadAction(BaseUploadAction[P]):
    """Default upload action with standard 8-step workflow.

    Provides a complete upload workflow with all standard steps:
    1. InitializeStep (5%) - Storage and path setup
    2. ProcessMetadataStep (10%) - Excel metadata loading
    3. AnalyzeCollectionStep (5%) - File specifications loading
    4. OrganizeFilesStep (15%) - File grouping by stem
    5. ValidateFilesStep (10%) - Validation against specs
    6. UploadFilesStep (30%) - File upload to storage
    7. GenerateDataUnitsStep (20%) - Data unit creation
    8. CleanupStep (5%) - Final cleanup

    Use this class when you need the standard upload workflow without
    customization. For custom workflows, extend BaseUploadAction instead.

    Example:
        >>> from synapse_sdk.plugins.actions.upload import (
        ...     DefaultUploadAction,
        ...     UploadParams,
        ... )
        >>>
        >>> class MyUploadAction(DefaultUploadAction[UploadParams]):
        ...     action_name = 'upload'
        ...     params_model = UploadParams
        >>>
        >>> # All 8 steps are automatically registered
    """

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        """Register the standard 8-step upload workflow.

        Steps are registered in execution order with their default
        configurations and strategies.

        Args:
            registry: StepRegistry to register steps with.
        """
        # 1. Initialize - Setup storage and paths (5%)
        registry.register(InitializeStep())

        # 2. Process Metadata - Load Excel metadata (10%)
        registry.register(ProcessMetadataStep())

        # 3. Analyze Collection - Load file specifications (5%)
        registry.register(AnalyzeCollectionStep())

        # 4. Organize Files - Group files by stem (15%)
        registry.register(OrganizeFilesStep())

        # 5. Validate Files - Validate against specs (10%)
        registry.register(ValidateFilesStep())

        # 6. Upload Files - Upload to storage (30%)
        registry.register(UploadFilesStep())

        # 7. Generate Data Units - Create data units (20%)
        registry.register(GenerateDataUnitsStep())

        # 8. Cleanup - Final cleanup (5%)
        registry.register(CleanupStep())
