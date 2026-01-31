"""Export action module with optional workflow step support.

Provides the export action classes:
    - BaseExportAction: Base class for export workflows
    - ExportAction: Simple execute-based export (deprecated)
    - DefaultExportAction: 6-step workflow export (recommended)
    - ExportContext: Export-specific context extending BaseStepContext

For step infrastructure (BaseStep, StepRegistry, Orchestrator),
use the steps module:
    from synapse_sdk.plugins.steps import BaseStep, StepRegistry

For export-specific steps:
    from synapse_sdk.plugins.actions.export.steps import (
        InitializeStep,
        FetchResultsStep,
        PrepareExportStep,
        ConvertDataStep,
        SaveFilesStep,
        FinalizeStep,
    )

Example (simple execute - deprecated):
    >>> class MyExportAction(BaseExportAction[MyParams]):
    ...     def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    ...         return self.client.get_assignments(filters)
    ...
    ...     def execute(self) -> dict[str, Any]:
    ...         results, count = self.get_filtered_results(self.params.filter)
    ...         # ... export items ...
    ...         return {'exported': count}

Example (step-based - recommended):
    >>> class MyExportAction(DefaultExportAction):
    ...     action_name = 'my_export'
    ...     # All 6 steps are automatically registered
    >>>
    >>> # Or customize steps:
    >>> class CustomExportAction(BaseExportAction[MyParams]):
    ...     def setup_steps(self, registry) -> None:
    ...         registry.register(InitializeStep())
    ...         registry.register(FetchResultsStep())
    ...         registry.register(PrepareExportStep())
    ...         registry.register(ConvertDataStep())
    ...         registry.register(SaveFilesStep())
    ...         registry.register(FinalizeStep())
"""

from synapse_sdk.plugins.actions.export.action import (
    BaseExportAction,
    DefaultExportAction,
    ExportAction,
)
from synapse_sdk.plugins.actions.export.context import ExportContext
from synapse_sdk.plugins.actions.export.enums import ExportStatus
from synapse_sdk.plugins.actions.export.exporter import (
    BaseExporter,
    ExporterRunAdapter,
    MetricsRecord,
)
from synapse_sdk.plugins.actions.export.handlers import (
    AssignmentExportTargetHandler,
    ExportTargetHandler,
    GroundTruthExportTargetHandler,
    TargetHandlerFactory,
    TaskExportTargetHandler,
)
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.actions.export.models import ExportParams

__all__ = [
    # Action classes
    'BaseExportAction',
    'DefaultExportAction',
    'ExportAction',
    'ExportContext',
    'ExportParams',
    # Log Messages
    'ExportLogMessageCode',
    # Exporter
    'BaseExporter',
    'ExporterRunAdapter',
    'MetricsRecord',
    'ExportStatus',
    # Target handlers
    'ExportTargetHandler',
    'AssignmentExportTargetHandler',
    'GroundTruthExportTargetHandler',
    'TaskExportTargetHandler',
    'TargetHandlerFactory',
]
