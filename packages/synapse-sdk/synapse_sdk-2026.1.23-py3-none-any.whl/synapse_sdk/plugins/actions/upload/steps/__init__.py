"""Upload workflow steps.

Provides the 8-step upload workflow:
    1. InitializeStep: Setup storage and paths
    2. ProcessMetadataStep: Load Excel metadata
    3. AnalyzeCollectionStep: Load file specifications
    4. OrganizeFilesStep: Group files by stem
    5. ValidateFilesStep: Validate against specifications
    6. UploadFilesStep: Upload to storage
    7. GenerateDataUnitsStep: Create data units
    8. CleanupStep: Final cleanup

Example:
    >>> from synapse_sdk.plugins.actions.upload.steps import (
    ...     InitializeStep,
    ...     ProcessMetadataStep,
    ...     AnalyzeCollectionStep,
    ...     OrganizeFilesStep,
    ...     ValidateFilesStep,
    ...     UploadFilesStep,
    ...     GenerateDataUnitsStep,
    ...     CleanupStep,
    ... )
    >>>
    >>> # Register steps in order
    >>> registry.register(InitializeStep())
    >>> registry.register(ProcessMetadataStep())
    >>> # ... etc
"""

from synapse_sdk.plugins.actions.upload.steps.analyze_collection import (
    AnalyzeCollectionStep,
)
from synapse_sdk.plugins.actions.upload.steps.cleanup import CleanupStep
from synapse_sdk.plugins.actions.upload.steps.generate import GenerateDataUnitsStep
from synapse_sdk.plugins.actions.upload.steps.initialize import InitializeStep
from synapse_sdk.plugins.actions.upload.steps.organize import OrganizeFilesStep
from synapse_sdk.plugins.actions.upload.steps.process_metadata import (
    ProcessMetadataStep,
)
from synapse_sdk.plugins.actions.upload.steps.upload import UploadFilesStep
from synapse_sdk.plugins.actions.upload.steps.validate import ValidateFilesStep

__all__ = [
    'InitializeStep',
    'ProcessMetadataStep',
    'AnalyzeCollectionStep',
    'OrganizeFilesStep',
    'ValidateFilesStep',
    'UploadFilesStep',
    'GenerateDataUnitsStep',
    'CleanupStep',
]
