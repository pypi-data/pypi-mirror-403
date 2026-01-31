"""Train action base class with optional step support."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, Field, model_validator

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.train.context import TrainContext
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.steps import BaseStep, Orchestrator, StepRegistry, StepResult

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.plugins.actions.train.log_messages import TrainLogMessageCode


class BaseTrainParams(BaseModel):
    """Base parameters for training actions.

    Provides common fields used across training workflows.
    Extend this class to add plugin-specific training parameters.

    Attributes:
        dataset: Ground truth dataset ID to download from Synapse.
        splits: Optional split definitions for train/valid/test.
        checkpoint: Optional model ID to use as starting checkpoint.
        is_tune: Whether this is a hyperparameter tuning run (backend field).
        hyperparameters: Optional list of hyperparameter dicts from backend.
            When provided, hyperparameters[0] is flattened to top-level fields.

    Example:
        >>> class MyTrainParams(BaseTrainParams):
        ...     epochs: int = 100
        ...     batch_size: int = 32
    """

    dataset: int = Field(description='Synapse ground truth dataset ID')
    splits: dict[str, Any] | None = Field(
        default=None,
        description='Split definitions: {"train": {...filters}, "valid": {...}}',
    )
    checkpoint: int | None = Field(default=None, description='Checkpoint model ID to resume from')
    is_tune: bool = Field(default=False, description='Hyperparameter tuning mode (requires tune_config)')
    hyperparameters: list[dict[str, Any]] | None = Field(
        default=None,
        description='Hyperparameters list from backend (hyperparameters[0] is flattened to top-level)',
    )

    model_config = {'extra': 'allow'}

    @model_validator(mode='before')
    @classmethod
    def flatten_hyperparameters(cls, data: Any) -> Any:
        """Flatten hyperparameters[0] fields to top level for backend compatibility.

        The backend sends params like:
            {"dataset": 176, "hyperparameters": [{"epochs": 10, "batch_size": 8}]}

        This validator flattens hyperparameters[0] to top level:
            {"dataset": 176, "epochs": 10, "batch_size": 8, "hyperparameters": [...]}
        """
        if not isinstance(data, dict):
            return data

        hyperparams = data.get('hyperparameters')
        if hyperparams and isinstance(hyperparams, list) and len(hyperparams) > 0:
            first_hp = hyperparams[0]
            if isinstance(first_hp, dict):
                for key, value in first_hp.items():
                    # Only set if not already present at top level
                    if key not in data:
                        data[key] = value

        return data


class BaseTrainAction(BaseAction[P]):
    """Base class for training actions.

    Provides a simplified API for training workflows. Plugin developers
    only need to:
    1. Set `target_format` class attribute (e.g., 'yolo')
    2. Override `execute(data_path, checkpoint)` with training logic

    The SDK automatically handles:
    - Dataset export from Synapse (if `dataset` in params)
    - Dataset conversion to target format
    - Step orchestration and progress tracking

    Attributes:
        category: Plugin category (defaults to NEURAL_NET).
        target_format: Dataset format for conversion (e.g., 'yolo', 'coco').
            Set this to enable automatic dataset conversion.

    Example (minimal - recommended):
        >>> class TrainAction(BaseTrainAction[TrainParams]):
        ...     target_format = 'yolo'  # Auto-converts dataset to YOLO format
        ...     result_model = TrainResult
        ...
        ...     def execute(self, data_path: Path, checkpoint: dict) -> TrainResult:
        ...         model = YOLO(checkpoint['path'])
        ...         model.train(data=str(data_path), epochs=self.params.epochs)
        ...         return TrainResult(weights_path='./weights')

    Example (custom steps - advanced):
        >>> class TrainAction(BaseTrainAction[TrainParams]):
        ...     def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        ...         # Full control over step pipeline
        ...         registry.register(MyCustomExportStep())
        ...         registry.register(MyCustomTrainStep())

    Dataset Format Configuration:
        Set `target_format` to automatically convert downloaded datasets:
        - 'yolo': YOLO format with dataset.yaml
        - 'coco': COCO JSON format
        - None: No conversion (use raw Datamaker format)

    Overriding Steps:
        Override `setup_steps()` for full control over the pipeline.
        When overridden, auto-wiring is disabled and you manage all steps.
    """

    category = PluginCategory.NEURAL_NET

    # Dataset format for automatic conversion (e.g., 'yolo', 'coco')
    # Set to None to disable automatic conversion
    target_format: str | None = None

    @classmethod
    def get_log_message_code_class(cls) -> type[TrainLogMessageCode]:
        from synapse_sdk.plugins.actions.train.log_messages import TrainLogMessageCode

        return TrainLogMessageCode

    def autolog(self, framework: str) -> None:
        """Enable automatic logging for an ML framework.

        Call this before creating model objects. The SDK will automatically
        attach callbacks to log progress, metrics, and artifacts.

        Supported frameworks:
            - 'ultralytics': YOLO object detection models

        Args:
            framework: Framework name (e.g., 'ultralytics').

        Raises:
            ValueError: If framework is not recognized.
            ImportError: If framework package is not installed.

        Example:
            >>> def execute(self, data_path, checkpoint):
            ...     self.autolog('ultralytics')
            ...     model = YOLO(checkpoint['path'])
            ...     model.train(epochs=100)
        """
        from synapse_sdk.integrations import autolog as _autolog

        _autolog(framework, self)

    @property
    def client(self) -> BackendClient:
        """Backend client from context.

        Returns:
            BackendClient instance.

        Raises:
            RuntimeError: If no client in context.
        """
        if self.ctx.client is None:
            raise RuntimeError(
                'No client in context. Either provide a client via RuntimeContext '
                'or override the helper methods (get_dataset, create_model, get_model).'
            )
        return self.ctx.client

    def _has_custom_setup_steps(self) -> bool:
        """Check if setup_steps was overridden by subclass."""
        return type(self).setup_steps is not BaseTrainAction.setup_steps

    def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
        """Register workflow steps for step-based execution.

        Override this method for full control over the step pipeline.
        When overridden, automatic step wiring is disabled.

        By default (when not overridden), the SDK auto-wires steps based on:
        - `dataset` in params → adds ExportDatasetStep
        - `target_format` class attribute → adds ConvertDatasetStep
        - Always adds internal step that calls your `execute()` method

        Args:
            registry: StepRegistry to register steps with.

        Example:
            >>> def setup_steps(self, registry: StepRegistry[TrainContext]) -> None:
            ...     from synapse_sdk.plugins.steps import ExportDatasetStep
            ...     registry.register(ExportDatasetStep())
            ...     registry.register(MyCustomPreprocessStep())
            ...     registry.register(MyTrainStep())
        """
        pass  # Default: no custom steps, run() will auto-wire

    def create_context(self) -> TrainContext:
        """Create training context for step-based workflow.

        Override to customize context creation or add additional state.

        Returns:
            TrainContext instance with params and runtime context.
        """
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)
        return TrainContext(
            runtime_ctx=self.ctx,
            params=params_dict,
        )

    def run(self) -> Any:
        """Run the action with automatic step orchestration.

        This method is called by executors. It:
        1. Checks if setup_steps() was overridden
        2. If overridden: uses custom steps
        3. If not overridden: auto-wires export/convert/train steps

        Step proportions are automatically configured by Orchestrator
        based on each step's progress_proportion property.

        Returns:
            Action result (dict or result_model instance).
        """
        from synapse_sdk.plugins.steps import ConvertDatasetStep, ExportDatasetStep

        registry: StepRegistry[TrainContext] = StepRegistry()

        if self._has_custom_setup_steps():
            # User has custom steps - use them
            self.setup_steps(registry)
        else:
            # Auto-wire steps based on params and target_format
            dataset = getattr(self.params, 'dataset', None)

            if dataset is not None:
                registry.register(ExportDatasetStep())
                if self.target_format:
                    registry.register(ConvertDatasetStep(target_format=self.target_format))

            # Add internal step that calls execute()
            registry.register(_TrainExecuteStep(self))

        if not registry:
            raise RuntimeError(
                'No steps registered. Either set target_format class attribute '
                'or override setup_steps() to register custom steps.'
            )

        # Step-based execution
        context = self.create_context()
        orchestrator: Orchestrator[TrainContext] = Orchestrator(
            registry=registry,
            context=context,
            progress_callback=lambda curr, total: self.set_progress(curr, total),
        )
        result = orchestrator.execute()

        # Add context data to result
        if context.model:
            result['model'] = context.model

        return result

    def execute(self, data_path: Path, checkpoint: dict[str, Any] | None) -> Any:
        """Execute training logic.

        Override this method with your training implementation.
        The SDK automatically resolves data_path and checkpoint for you.

        Args:
            data_path: Path to dataset config file (e.g., dataset.yaml for YOLO).
                Resolved from export/convert steps.
            checkpoint: Checkpoint dict with 'path' and 'category' keys, or None.
                Resolved from params.checkpoint or ctx.checkpoint.

        Returns:
            Training result. Can be a dict or result_model instance.

        Example:
            >>> def execute(self, data_path: Path, checkpoint: dict) -> TrainResult:
            ...     self.autolog('ultralytics')
            ...     model = YOLO(checkpoint['path'])
            ...     results = model.train(
            ...         data=str(data_path),
            ...         epochs=self.params.epochs,
            ...     )
            ...     return TrainResult(weights_path='./weights')
        """
        raise NotImplementedError(
            f'{type(self).__name__} must implement execute(data_path, checkpoint). '
            'See BaseTrainAction docstring for examples.'
        )

    def get_dataset(self) -> dict[str, Any]:
        """Fetch training dataset info from backend.

        Default implementation uses params.dataset. Override for custom behavior.

        Returns:
            Dataset metadata dictionary.

        Raises:
            ValueError: If params.dataset is not set.
            RuntimeError: If no client in context.
        """
        dataset = getattr(self.params, 'dataset', None)
        if dataset is None:
            raise ValueError(
                'params.dataset is required for default get_dataset(). '
                'Either set dataset in your params model or override get_dataset().'
            )
        # Return basic info - full data is fetched via ground_truth_events
        return {'id': dataset}

    def create_model(self, path: str, **kwargs: Any) -> dict[str, Any]:
        """Upload trained model to backend.

        Default implementation uploads via client.create_model().
        Override for custom behavior (e.g., MLflow, S3).

        Args:
            path: Local path to model artifacts.
            **kwargs: Additional fields for model creation.

        Returns:
            Created model metadata dictionary.

        Raises:
            RuntimeError: If no client in context.
        """
        return self.client.create_model({
            'file': path,
            **kwargs,
        })

    def get_model(self, model_id: int) -> dict[str, Any]:
        """Retrieve existing model by ID.

        Args:
            model_id: Model identifier.

        Returns:
            Model metadata dictionary.

        Raises:
            RuntimeError: If no client in context.
        """
        return self.client.get_model(model_id)

    def get_checkpoint(self) -> dict[str, Any] | None:
        """Get checkpoint for training.

        Resolves checkpoint in the following order:
        1. If ctx.checkpoint is set (remote mode), returns it directly
        2. If params.checkpoint is set (model ID), fetches and extracts

        Returns:
            Checkpoint dict with 'category', 'path', 'id', 'name', or None.

        Example:
            >>> checkpoint = self.get_checkpoint()
            >>> if checkpoint:
            ...     model_path = checkpoint['path']
        """
        from synapse_sdk.utils.file import extract_archive, get_temp_path

        # If checkpoint is already in context (remote mode), return it
        if self.ctx.checkpoint is not None:
            return self.ctx.checkpoint

        # Check if params has a checkpoint field (model ID)
        checkpoint_id = getattr(self.params, 'checkpoint', None)
        if checkpoint_id is None:
            return None

        # Fetch model from backend
        model = self.get_model(checkpoint_id)

        # The model['file'] is downloaded by the client's url_conversion
        model_file = Path(model['file'])

        # Extract to temp path
        output_path = get_temp_path(f'models/{model_file.stem}')
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
            extract_archive(model_file, output_path)

        # Determine category - base models vs fine-tuned
        category = model.get('category') or 'base'

        return {
            'category': category,
            'path': output_path,
            'id': model.get('id'),
            'name': model.get('name'),
        }


class _TrainExecuteStep(BaseStep[TrainContext]):
    """Internal step that wraps action's execute() method.

    This step is auto-registered when setup_steps() is not overridden.
    It resolves data_path and checkpoint, then calls action.execute().
    """

    def __init__(self, action: BaseTrainAction[Any]) -> None:
        self._action = action

    @property
    def name(self) -> str:
        return 'train'

    @property
    def progress_weight(self) -> float:
        return 0.5

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (75% - training)."""
        return 75

    def execute(self, context: TrainContext) -> StepResult:
        # Resolve data path from context (set by export/convert steps)
        data_path = self._resolve_data_path(context)
        if data_path is None:
            return StepResult(
                success=False,
                error='No data path available. Ensure ExportDatasetStep and ConvertDatasetStep ran successfully.',
            )

        # Resolve checkpoint
        checkpoint = self._action.get_checkpoint()

        # Call action's execute method
        try:
            result = self._action.execute(data_path, checkpoint)
        except Exception as e:
            return StepResult(success=False, error=str(e))

        # Extract result data
        if hasattr(result, 'model_dump'):
            result_data = result.model_dump()
        elif isinstance(result, dict):
            result_data = result
        else:
            result_data = {'result': result}

        # Store model_path in context if available
        weights_path = result_data.get('weights_path')
        if weights_path:
            context.model_path = weights_path

        return StepResult(success=True, data=result_data)

    def _resolve_data_path(self, context: TrainContext) -> Path | None:
        """Resolve data path from context (set by ConvertDatasetStep)."""
        if context.dataset is None:
            return None

        config_path = context.dataset.get('config_path')
        if config_path is not None:
            return Path(config_path)

        path = context.dataset.get('path')
        if path is not None:
            path = Path(path)
            if path.is_dir():
                return path / 'dataset.yaml'
            return path

        return None
