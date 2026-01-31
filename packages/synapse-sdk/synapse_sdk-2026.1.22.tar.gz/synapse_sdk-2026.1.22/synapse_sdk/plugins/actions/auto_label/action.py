"""Auto-label action base class for smart tool plugins."""

from __future__ import annotations

import logging
from abc import abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, Field

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.enums import PluginCategory

P = TypeVar('P', bound=BaseModel)

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient

_logger = logging.getLogger(__name__)


class AutoLabelParams(BaseModel):
    """Base parameters for auto-label actions.

    Provides common fields used by smart tool auto-labeling workflows.
    Extend this class to add plugin-specific parameters.

    Attributes:
        plugin: Neural net plugin code to use for inference.
        version: Neural net plugin version.
        model_id: Model ID to use for inference.
        method: Inference method (e.g., 'inference').

    Example:
        >>> class MyAutoLabelParams(AutoLabelParams):
        ...     confidence_threshold: float = 0.5
    """

    plugin: str = Field(description='Neural net plugin code for inference')
    version: str = Field(description='Neural net plugin version')
    model_id: int | None = Field(default=None, description='Model ID for inference')
    method: str = Field(default='inference', description='Inference method name')

    model_config = {'extra': 'allow'}


class AutoLabelResult(BaseModel):
    """Result model for auto-label actions.

    Attributes:
        annotations: List of generated annotations.
        metadata: Optional metadata from the labeling process.
    """

    annotations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AutoLabelProgressCategories:
    """Standard progress category names for auto-label workflows.

    Use these constants with set_progress() to track multi-phase labeling:
        - INPUT_TRANSFORM: Transforming smart tool input to model format
        - INFERENCE: Running model inference
        - OUTPUT_TRANSFORM: Transforming model output to annotation format

    Example:
        >>> self.set_progress(1, 3, self.progress.INPUT_TRANSFORM)
        >>> self.set_progress(2, 3, self.progress.INFERENCE)
        >>> self.set_progress(3, 3, self.progress.OUTPUT_TRANSFORM)
    """

    INPUT_TRANSFORM: str = 'input_transform'
    INFERENCE: str = 'inference'
    OUTPUT_TRANSFORM: str = 'output_transform'


class BaseAutoLabelAction(BaseAction[P]):
    """Base class for smart tool auto-label actions.

    Provides the handle_input/handle_output pattern for transforming data
    between smart tool format and model format. Automatically handles
    inference invocation via the neural net plugin.

    Plugin developers only need to:
    1. Override handle_input() to transform smart tool input to model input
    2. Override handle_output() to transform model output to annotation format

    The SDK automatically handles:
    - Model inference via the neural net plugin
    - Progress tracking and logging
    - Error handling

    Attributes:
        category: Plugin category (defaults to SMART_TOOL).
        progress: Standard progress category names.

    Example (minimal):
        >>> class MyAutoLabel(BaseAutoLabelAction[MyParams]):
        ...     def handle_input(self, input_data: dict) -> dict:
        ...         # Transform smart tool input to model input
        ...         return {'image': input_data['file_url']}
        ...
        ...     def handle_output(self, output_data: dict) -> dict:
        ...         # Transform model output to annotations
        ...         return {'annotations': output_data['predictions']}

    Example (with custom params):
        >>> class MyAutoLabelParams(AutoLabelParams):
        ...     confidence_threshold: float = 0.5
        ...
        >>> class MyAutoLabel(BaseAutoLabelAction[MyAutoLabelParams]):
        ...     def handle_input(self, input_data: dict) -> dict:
        ...         return {
        ...             'image': input_data['file_url'],
        ...             'threshold': self.params.confidence_threshold,
        ...         }
        ...
        ...     def handle_output(self, output_data: dict) -> dict:
        ...         return {'annotations': output_data['predictions']}
    """

    category = PluginCategory.SMART_TOOL
    progress = AutoLabelProgressCategories()

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
                'or override run_inference() with custom inference logic.'
            )
        return self.ctx.client

    @abstractmethod
    def handle_input(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """Transform smart tool input to model input format.

        Override this method to convert the input data from smart tool
        format to the format expected by your model.

        Args:
            input_data: Input data from smart tool (includes params).

        Returns:
            Transformed data ready for model inference.

        Example:
            >>> def handle_input(self, input_data: dict) -> dict:
            ...     return {
            ...         'image': input_data['file_url'],
            ...         'model_id': input_data.get('model_id'),
            ...     }
        """
        ...

    @abstractmethod
    def handle_output(self, output_data: dict[str, Any]) -> dict[str, Any]:
        """Transform model output to smart tool annotation format.

        Override this method to convert the model output to the
        annotation format expected by the smart tool.

        Args:
            output_data: Output data from model inference.

        Returns:
            Transformed data with annotations for smart tool.

        Example:
            >>> def handle_output(self, output_data: dict) -> dict:
            ...     annotations = []
            ...     for pred in output_data.get('predictions', []):
            ...         annotations.append({
            ...             'type': 'bbox',
            ...             'coordinates': pred['box'],
            ...             'label': pred['class'],
            ...             'confidence': pred['score'],
            ...         })
            ...     return {'annotations': annotations}
        """
        ...

    def run_inference(self, model_input: dict[str, Any]) -> dict[str, Any]:
        """Run inference via the neural net plugin.

        Default implementation uses the backend client to invoke the
        neural net plugin's inference action. Override for custom
        inference logic (e.g., local model, different API).

        Args:
            model_input: Input data for model inference.

        Returns:
            Model inference output.

        Raises:
            RuntimeError: If inference fails.
            ValueError: If required params are missing.
        """
        params = self.params
        plugin_code = getattr(params, 'plugin', None)
        version = getattr(params, 'version', None)
        method = getattr(params, 'method', 'inference')

        if not plugin_code or not version:
            raise ValueError(
                'params.plugin and params.version are required for inference. '
                'Set these in your params model or override run_inference().'
            )

        # Add method to input for the inference action
        inference_input = {
            **model_input,
            'method': method,
        }

        # Try to run via backend client
        try:
            # Use the backend's run_plugin endpoint
            result = self.client.run_plugin(
                plugin=plugin_code,
                data={
                    'action': 'inference',
                    'version': version,
                    'params': inference_input,
                },
            )
            return result
        except Exception as e:
            _logger.warning(
                'Failed to run inference via backend client: %s. Override run_inference() for custom inference logic.',
                str(e),
            )
            raise RuntimeError(f'Inference failed: {e}. Override run_inference() to implement custom inference.') from e

    def execute(self) -> dict[str, Any]:
        """Execute the auto-label workflow.

        Orchestrates the handle_input -> inference -> handle_output flow.
        Override for completely custom execution logic.

        Returns:
            Auto-label result with annotations.
        """
        # Get params as dict for input handling
        params_dict = self.params.model_dump() if hasattr(self.params, 'model_dump') else dict(self.params)

        # Step 1: Transform input
        self.set_progress(1, 3, self.progress.INPUT_TRANSFORM)
        model_input = self.handle_input(params_dict)

        if model_input is None:
            model_input = params_dict

        # Step 2: Run inference
        self.set_progress(2, 3, self.progress.INFERENCE)
        model_output = self.run_inference(model_input)

        # Step 3: Transform output
        self.set_progress(3, 3, self.progress.OUTPUT_TRANSFORM)
        result = self.handle_output(model_output)

        if result is None:
            result = model_output

        return result


__all__ = [
    'BaseAutoLabelAction',
    'AutoLabelParams',
    'AutoLabelProgressCategories',
    'AutoLabelResult',
]
