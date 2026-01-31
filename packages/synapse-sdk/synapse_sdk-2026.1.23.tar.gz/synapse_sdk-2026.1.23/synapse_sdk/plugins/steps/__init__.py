"""Step workflow module for Synapse SDK.

This module provides the core abstractions for building step-based workflows.
Classes here are not pipeline-specific and can be used standalone for any
action-based workflow.

Classes:
    BaseStep: Abstract base class for implementing individual steps.
    StepResult: Data class representing the result of a step execution.
    BaseStepContext: Context shared between steps during execution.
    StepRegistry: Registry for managing step registration and ordering.
    Orchestrator: Executes steps in order and handles rollback on failure.

Utility Steps:
    LoggingStep: Wrapper that adds logging to step execution.
    TimingStep: Wrapper that adds timing measurement to step execution.
    ValidationStep: Wrapper that adds pre-execution validation to steps.

Example:
    >>> from synapse_sdk.plugins.steps import (
    ...     BaseStep,
    ...     BaseStepContext,
    ...     Orchestrator,
    ...     StepRegistry,
    ...     StepResult,
    ... )
    >>>
    >>> @dataclass
    ... class MyContext(BaseStepContext):
    ...     data: list[str] = field(default_factory=list)
    >>>
    >>> class LoadStep(BaseStep[MyContext]):
    ...     @property
    ...     def name(self) -> str:
    ...         return 'load'
    ...
    ...     @property
    ...     def progress_weight(self) -> float:
    ...         return 0.3
    ...
    ...     def execute(self, context: MyContext) -> StepResult:
    ...         context.data.append('loaded')
    ...         return StepResult(success=True)
"""

from synapse_sdk.plugins.steps.base import BaseStep, StepResult
from synapse_sdk.plugins.steps.context import BaseStepContext
from synapse_sdk.plugins.steps.dataset import ConvertDatasetStep, ExportDatasetStep
from synapse_sdk.plugins.steps.orchestrator import Orchestrator
from synapse_sdk.plugins.steps.registry import StepRegistry
from synapse_sdk.plugins.steps.utils import LoggingStep, TimingStep, ValidationStep

__all__ = [
    # Core
    'BaseStep',
    'BaseStepContext',
    'Orchestrator',
    'StepRegistry',
    'StepResult',
    # Dataset steps
    'ConvertDatasetStep',
    'ExportDatasetStep',
    # Utilities
    'LoggingStep',
    'TimingStep',
    'ValidationStep',
]
