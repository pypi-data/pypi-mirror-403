"""Analyze collection step for upload workflow."""

from __future__ import annotations

from typing import Any

from synapse_sdk.plugins.actions.upload.context import UploadContext
from synapse_sdk.plugins.actions.upload.enums import LogCode
from synapse_sdk.plugins.actions.upload.log_messages import UploadLogMessageCode
from synapse_sdk.plugins.steps import BaseStep, StepResult


class AnalyzeCollectionStep(BaseStep[UploadContext]):
    """Analyze data collection to get file specifications.

    This step:
    1. Retrieves data collection from the API
    2. Extracts file specifications
    3. Stores specifications in context for subsequent steps

    Progress weight: 0.05 (5%)
    """

    @property
    def name(self) -> str:
        """Step identifier."""
        return 'analyze_collection'

    @property
    def progress_weight(self) -> float:
        """Relative progress weight."""
        return 0.05

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (5%)."""
        return 5

    def execute(self, context: UploadContext) -> StepResult:
        """Execute collection analysis step.

        Args:
            context: Upload context with params and client.

        Returns:
            StepResult with file_specifications in data.
        """
        collection_id = context.params.get('data_collection')
        if collection_id is None:
            return StepResult(
                success=False,
                error='Data collection parameter is required',
            )

        try:
            # Set initial progress
            context.set_progress(0, 2)

            # Get collection from client
            collection = context.client.get_data_collection(collection_id)
            context.set_progress(1, 2)

            # Extract file specifications
            file_specifications: list[dict[str, Any]] = collection.get('file_specifications', [])

            # Store in context
            context.data_collection = collection

            # Complete progress
            context.set_progress(2, 2)

            context.log(
                LogCode.STEP_COMPLETED.value,
                {
                    'step': self.name,
                    'specs_count': len(file_specifications),
                },
            )
            context.log_message(UploadLogMessageCode.UPLOAD_COLLECTION_ANALYZED, count=len(file_specifications))

            return StepResult(
                success=True,
                data={'file_specifications': file_specifications},
                rollback_data={'collection_id': collection_id},
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to analyze collection {collection_id}: {e}',
            )

    def can_skip(self, context: UploadContext) -> bool:
        """Collection analysis cannot be skipped."""
        return False

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Rollback collection analysis."""
        context.log(LogCode.ROLLBACK_COLLECTION_ANALYSIS.value, {})
        context.data_collection = None
