from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Generic, TypeVar, get_args, get_origin

from pydantic import BaseModel, ValidationError as PydanticValidationError

from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.log_messages import LogMessageCode
from synapse_sdk.plugins.types import DataType

if TYPE_CHECKING:
    from synapse_sdk.plugins.context import RuntimeContext

P = TypeVar('P', bound=BaseModel)

_logger = logging.getLogger(__name__)


class NoResult:
    """Sentinel indicating no result schema is defined.

    Used as the default for result_model to indicate that an action
    does not have a typed result schema.

    Example:
        >>> class MyAction(BaseAction[MyParams]):
        ...     pass  # result_model defaults to NoResult
        >>>
        >>> class TypedAction(BaseAction[MyParams]):
        ...     result_model = MyResult  # Explicitly set result schema
    """

    pass


class BaseAction(ABC, Generic[P]):
    """Base class for plugin actions with typed params and optional result schema.

    Supports typed input parameters via the generic parameter, and optional
    typed output via the result_model class attribute.

    Class Attributes:
        action_name: Action name used for invocation (optional, from config.yaml).
        category: Category for grouping actions (optional, from config.yaml).
        input_type: DataType subclass declaring expected input (e.g., YOLODataset).
        output_type: DataType subclass declaring produced output (e.g., ModelWeights).
        params_model: Pydantic model class for input validation (auto-extracted from generic).
        result_model: Pydantic model class for output validation (optional, defaults to NoResult).

    Instance Attributes:
        params: Pre-validated parameters (Pydantic model instance).
        ctx: Runtime context with logger, env, etc.

    Example (without result schema):
        >>> class TrainParams(BaseModel):
        ...     epochs: int = 10
        >>>
        >>> class TrainAction(BaseAction[TrainParams]):
        ...     def execute(self) -> dict:
        ...         return {'status': 'completed'}

    Example (with type declarations):
        >>> from synapse_sdk.plugins.types import YOLODataset, ModelWeights
        >>>
        >>> class TrainAction(BaseAction[TrainParams]):
        ...     input_type = YOLODataset
        ...     output_type = ModelWeights
        ...     result_model = TrainResult
        ...
        ...     def execute(self) -> TrainResult:
        ...         return TrainResult(weights_path='/model.pt', final_loss=0.1)
    """

    # Optional: injected from config.yaml during discovery if not set
    action_name: str | None = None
    category: PluginCategory | None = None

    # Semantic types for pipeline compatibility validation
    # Use DataType subclasses for type-safe declarations
    input_type: type[DataType] | None = None
    output_type: type[DataType] | None = None

    # Auto-extracted from generic parameter, can be overridden
    params_model: type[P]

    # Optional: set to a Pydantic model to enable result validation
    result_model: type[BaseModel] | type[NoResult] = NoResult

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Extract params_model from generic type parameter."""
        super().__init_subclass__(**kwargs)

        # Skip if params_model is explicitly set
        if 'params_model' in cls.__dict__:
            return

        # Extract from generic parameter: BaseAction[TrainParams] -> TrainParams
        for base in getattr(cls, '__orig_bases__', ()):
            origin = get_origin(base)
            if origin is None:
                continue

            # Check if this base is BaseAction or a subclass
            if isinstance(origin, type) and issubclass(origin, BaseAction):
                args = get_args(base)
                if args and isinstance(args[0], type) and issubclass(args[0], BaseModel):
                    cls.params_model = args[0]
                    return

    def __init__(self, params: P, ctx: RuntimeContext) -> None:
        """Initialize action with validated params and runtime context.

        Args:
            params: Pre-validated Pydantic model instance.
            ctx: Runtime context with logger, env, etc.
        """
        self.params = params
        self.ctx = ctx

    @abstractmethod
    def execute(self) -> Any:
        """Execute the action.

        Implement this method with your action's main logic.
        Use self.params for input and self.ctx for dependencies.

        Returns:
            Action result (should be serializable).

        Raises:
            ExecutionError: If execution fails.
        """
        ...

    @property
    def logger(self):
        """Access the logger from context."""
        return self.ctx.logger

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event with data.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
        """
        self.ctx.log(event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress for the current operation.

        Args:
            current: Current progress value (0 to total).
            total: Total progress value.
            category: Optional category name for multi-phase progress.
        """
        self.ctx.set_progress(current, total, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        """Set metrics for a category.

        Args:
            value: Dictionary of metric values.
            category: Non-empty category name.
        """
        self.ctx.set_metrics(value, category)

    def log_metric(
        self,
        category: str,
        key: str,
        value: float | int,
        **metrics: Any,
    ) -> None:
        """Log a training metric.

        Sends a log entry with event='metric' to the backend.
        Format: {'category': ..., 'key': ..., 'value': ..., 'metrics': {...}}

        Args:
            category: Metric category (e.g., 'train', 'validation').
            key: Primary metric key (e.g., 'epoch', 'loss').
            value: Primary metric value.
            **metrics: Additional metrics as keyword arguments.

        Example:
            >>> action.log_metric('validation', 'epoch', 3, val_loss=0.015, val_iou=0.25)
        """
        self.ctx.log_metric(category, key, value, **metrics)

    def log_visualization(
        self,
        category: str,
        group: str,
        index: int,
        image: str,
        **meta: Any,
    ) -> None:
        """Log a visualization image.

        Sends a log entry with event='visualization' to the backend.

        Args:
            category: Visualization category (e.g., 'train', 'validation').
            group: Group name/identifier (e.g., epoch number).
            index: Index within the group.
            image: Path to the image file.
            **meta: Additional metadata.

        Example:
            >>> action.log_visualization('validation', 'epoch_5', 0, '/tmp/pred.jpg')
        """
        self.ctx.log_visualization(category, group, index, image, **meta)

    def log_message(
        self,
        message: str | LogMessageCode,
        context: str = 'info',
        **kwargs: Any,
    ) -> None:
        """Log a user-facing message.

        Sends a log entry with event='message' to the backend.
        Format: {'content': ..., 'context': ...}

        Accepts either a plain string or a LogMessageCode enum.
        When a LogMessageCode is used, the message template and level
        are resolved from the global template registry automatically.

        Args:
            message: Message content string or LogMessageCode enum.
            context: Message context/level ('info', 'warning', 'danger', 'success').
                Ignored when message is a LogMessageCode (level comes from template).
            **kwargs: Format parameters for LogMessageCode message templates.

        Example:
            >>> action.log_message('Starting model training.', 'info')
            >>> action.log_message(TrainLogMessageCode.TRAIN_STARTING, epochs=100)
        """
        self.ctx.log_message(message, context, **kwargs)

    @classmethod
    def get_log_message_code_class(cls) -> type[LogMessageCode]:
        """Return the LogMessageCode subclass for this action.

        Each action plugin must override this method to declare which
        LogMessageCode subclass it uses. This ensures log message codes
        are properly scoped to each plugin.

        Returns:
            The LogMessageCode subclass for this action.

        Raises:
            NotImplementedError: If not overridden by subclass.

        Example:
            >>> class MyUploadAction(BaseUploadAction[MyParams]):
            ...     @classmethod
            ...     def get_log_message_code_class(cls):
            ...         return UploadLogMessageCode
        """
        raise NotImplementedError(
            f'{cls.__name__} must implement get_log_message_code_class() to declare its LogMessageCode subclass.'
        )

    def run(self) -> Any:
        """Run the action.

        Default implementation calls execute(). Subclasses with step-based
        workflows override this to add orchestration logic.

        Returns:
            Action result.
        """
        return self.execute()

    @classmethod
    def dispatch(cls, params: dict[str, Any], ctx: RuntimeContext) -> Any:
        """Dispatch action execution.

        Validates params, instantiates the action, and runs it.
        Override in subclasses for custom dispatch behavior (e.g., serve deployments).

        Args:
            params: Raw params dict.
            ctx: Runtime context with logger, env, client.

        Returns:
            Action result.
        """
        params_model = getattr(cls, 'params_model', None)
        if params_model is not None:
            validated_params = params_model.model_validate(params, context={'client': ctx.client})
        else:
            validated_params = params

        action = cls(validated_params, ctx)
        return action.run()


def validate_result(
    result: Any,
    result_model: type[BaseModel] | type[NoResult],
    logger: Any = None,
) -> Any:
    """Validate action result against schema with warning-only mode.

    This function validates the result returned by an action's execute() method
    against its declared result_model schema. If validation fails, it logs a
    warning but still returns the original result (warning-only mode).

    Args:
        result: The raw result from execute().
        result_model: The expected Pydantic model, or NoResult to skip validation.
        logger: Optional logger for warnings. Falls back to module logger if None.

    Returns:
        The original result (unchanged even if validation fails).

    Example:
        >>> class MyResult(BaseModel):
        ...     value: int
        >>>
        >>> result = validate_result({'value': 42}, MyResult)
        >>> # No warning, result passes validation
        >>>
        >>> result = validate_result({'wrong': 'data'}, MyResult)
        >>> # Logs warning, returns {'wrong': 'data'} unchanged
    """
    if result_model is NoResult:
        return result

    log = logger if logger else _logger

    try:
        # If result is already the correct model instance, it's valid
        if isinstance(result, result_model):
            return result

        # If result is a dict, try to validate it against the model
        if isinstance(result, dict):
            result_model.model_validate(result)
        else:
            # Result is neither a model instance nor a dict
            if hasattr(log, 'warning'):
                log.warning(
                    f'Result type mismatch: expected {result_model.__name__} or dict, got {type(result).__name__}'
                )
    except PydanticValidationError as e:
        if hasattr(log, 'warning'):
            log.warning(f'Result validation warning for {result_model.__name__}: {e}')
    except Exception as e:
        if hasattr(log, 'warning'):
            log.warning(f'Result validation failed: {e}')

    return result


__all__ = ['BaseAction', 'NoResult', 'validate_result']
