"""Plugin architecture for Synapse SDK.

This module provides the core plugin framework including:
- Plugin configuration and discovery
- Action definition (class-based and function-based)
- Execution modes (local, task, job)
- Pipeline patterns (step-based workflows)

Example:
    >>> from synapse_sdk.plugins import action, run_plugin
    >>> from pydantic import BaseModel
    >>>
    >>> class TrainParams(BaseModel):
    ...     epochs: int = 10
    >>>
    >>> @action(params=TrainParams)
    ... def train(params: TrainParams, context) -> dict:
    ...     return {'trained': True}
    >>>
    >>> # Execute the plugin action
    >>> result = run_plugin('my_plugin', 'train', {'epochs': 20})
"""

from synapse_sdk.plugins.action import BaseAction, NoResult, validate_result
from synapse_sdk.plugins.actions import (
    BaseDeploymentAction,
    BaseExportAction,
    BaseInferenceAction,
    BaseServeDeployment,
    BaseTrainAction,
    BaseUploadAction,
    DeploymentContext,
    DeploymentProgressCategories,
    ExportContext,
    InferenceContext,
    InferenceProgressCategories,
    TrainContext,
    UploadContext,
    create_serve_multiplexed_model_id,
)
from synapse_sdk.plugins.config import ActionConfig, PluginConfig
from synapse_sdk.plugins.context import RuntimeContext
from synapse_sdk.plugins.decorators import action
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.errors import (
    ActionNotFoundError,
    ExecutionError,
    PluginError,
    ValidationError,
)
from synapse_sdk.plugins.runner import run_plugin
from synapse_sdk.plugins.schemas import (
    ExportResult,
    InferenceResult,
    MetricsResult,
    TrainResult,
    UploadResult,
    WeightsResult,
)
from synapse_sdk.plugins.steps import (
    BaseStep,
    BaseStepContext,
    LoggingStep,
    Orchestrator,
    StepRegistry,
    StepResult,
    TimingStep,
    ValidationStep,
)
from synapse_sdk.plugins.utils import get_action_ui_schema, pydantic_to_ui_schema

__all__ = [
    # Types
    'PluginCategory',
    # Config
    'ActionConfig',
    'PluginConfig',
    # Context
    'RuntimeContext',
    # Errors
    'ActionNotFoundError',
    'ExecutionError',
    'PluginError',
    'ValidationError',
    # Actions - Base
    'BaseAction',
    'NoResult',
    'validate_result',
    'action',
    # Actions - Train
    'BaseTrainAction',
    'TrainContext',
    # Actions - Export
    'BaseExportAction',
    'ExportContext',
    # Actions - Upload
    'BaseUploadAction',
    'UploadContext',
    # Actions - Inference
    'BaseInferenceAction',
    'InferenceContext',
    'InferenceProgressCategories',
    # Actions - Deployment
    'BaseDeploymentAction',
    'DeploymentContext',
    'DeploymentProgressCategories',
    # Ray Serve
    'BaseServeDeployment',
    'create_serve_multiplexed_model_id',
    # Pipeline Steps
    'BaseStep',
    'BaseStepContext',
    'StepResult',
    'StepRegistry',
    'Orchestrator',
    'LoggingStep',
    'TimingStep',
    'ValidationStep',
    # Runner
    'run_plugin',
    # Schema utilities
    'pydantic_to_ui_schema',
    'get_action_ui_schema',
    # Result types
    'ExportResult',
    'InferenceResult',
    'MetricsResult',
    'TrainResult',
    'UploadResult',
    'WeightsResult',
]
