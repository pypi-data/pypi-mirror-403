"""Category-specific action base classes.

Provides specialized base classes for common action types:
    - DatasetAction: Download and convert dataset workflows
    - BaseTrainAction: Training workflows with dataset/model helpers
    - BaseExportAction: Export workflows with step-based execution (6 built-in steps)
    - DefaultExportAction: Export workflows with all 6 steps pre-registered
    - BaseUploadAction: Upload workflows with step-based execution (7 built-in steps)
    - BaseInferenceAction: Inference workflows with model loading
    - BaseDeploymentAction: Ray Serve deployment workflows
    - BaseServeDeployment: Ray Serve inference endpoint with model multiplexing
    - AddTaskDataAction: Pre-annotation workflows for task data preparation
    - BaseAutoLabelAction: Smart tool auto-label with handle_input/handle_output pattern

Each base class provides:
    - Standard progress category names
    - Helper methods with sensible defaults
    - Override points for custom behavior
    - Optional step-based workflow execution
    - Built-in step implementations for complex workflows (Export, Upload, AddTaskData)

Action Registry for dynamic action discovery:
    - ActionRegistry: Singleton registry for action metadata
    - ActionSpec: Action specification with type information
    - ActionType: Action type enumeration

For pipeline orchestration, use the pipelines module:
    from synapse_sdk.plugins.pipelines import ActionPipeline
"""

from synapse_sdk.plugins.action_registry import (
    ActionRegistry,
    ActionSpec,
    ActionType,
    get_action_registry,
)
from synapse_sdk.plugins.actions.add_task_data import (
    AddTaskDataAction,
    AddTaskDataContext,
    AddTaskDataMethod,
    AddTaskDataParams,
    AddTaskDataProgressCategories,
    AddTaskDataResult,
)
from synapse_sdk.plugins.actions.auto_label import (
    AutoLabelParams,
    AutoLabelProgressCategories,
    AutoLabelResult,
    BaseAutoLabelAction,
)
from synapse_sdk.plugins.actions.dataset import (
    DatasetAction,
    DatasetOperation,
    DatasetParams,
    DatasetResult,
)
from synapse_sdk.plugins.actions.export import (
    BaseExportAction,
    DefaultExportAction,
    ExportContext,
)
from synapse_sdk.plugins.actions.inference import (
    BaseDeploymentAction,
    BaseInferenceAction,
    BaseServeDeployment,
    DeploymentContext,
    DeploymentProgressCategories,
    InferenceContext,
    InferenceProgressCategories,
    create_serve_multiplexed_model_id,
)
from synapse_sdk.plugins.actions.train import (
    BaseTrainAction,
    TrainContext,
)
from synapse_sdk.plugins.actions.upload import (
    BaseUploadAction,
    UploadContext,
)

__all__ = [
    # Dataset
    'DatasetAction',
    'DatasetOperation',
    'DatasetParams',
    'DatasetResult',
    # Train
    'BaseTrainAction',
    'TrainContext',
    # Export
    'BaseExportAction',
    'DefaultExportAction',
    'ExportContext',
    # Upload
    'BaseUploadAction',
    'UploadContext',
    # Pre-Annotation
    'AddTaskDataAction',
    'AddTaskDataContext',
    'AddTaskDataMethod',
    'AddTaskDataParams',
    'AddTaskDataProgressCategories',
    'AddTaskDataResult',
    # Inference
    'BaseInferenceAction',
    'InferenceContext',
    'InferenceProgressCategories',
    # Deployment
    'BaseDeploymentAction',
    'DeploymentContext',
    'DeploymentProgressCategories',
    # Serve
    'BaseServeDeployment',
    'create_serve_multiplexed_model_id',
    # Smart Tool / Auto-Label
    'BaseAutoLabelAction',
    'AutoLabelParams',
    'AutoLabelProgressCategories',
    'AutoLabelResult',
    # Action Registry
    'ActionRegistry',
    'ActionSpec',
    'ActionType',
    'get_action_registry',
]
