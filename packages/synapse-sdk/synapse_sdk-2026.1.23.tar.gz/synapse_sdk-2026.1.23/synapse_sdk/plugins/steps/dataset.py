"""Dataset workflow steps for training actions.

Provides reusable steps for dataset operations in training workflows:
- ExportDatasetStep: Download dataset from Synapse backend
- ConvertDatasetStep: Convert dataset between formats
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from synapse_sdk.plugins.steps.base import BaseStep, StepResult

if TYPE_CHECKING:
    from synapse_sdk.plugins.actions.train.context import TrainContext


class ExportDatasetStep(BaseStep['TrainContext']):
    """Download dataset from Synapse backend.

    Reads dataset from context.params and downloads the dataset.
    Stores result in context.dataset with keys:
        - path: Path to downloaded dataset
        - format: Dataset format (e.g., 'dm_v2')
        - is_categorized: Whether dataset has train/valid/test splits
        - count: Number of data units downloaded

    Required params:
        - dataset: int - Ground truth dataset ID to download

    Optional params:
        - splits: dict - Split definitions for categorized download
        - output_dir: str - Custom output directory

    Example:
        >>> registry.register(ExportDatasetStep())
    """

    @property
    def name(self) -> str:
        return 'dataset'

    @property
    def progress_weight(self) -> float:
        return 0.3

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (20% - dataset export)."""
        return 20

    def execute(self, context: TrainContext) -> StepResult:
        from synapse_sdk.plugins.actions.dataset import (
            DatasetAction,
            DatasetOperation,
            DatasetParams,
        )

        dataset = context.params.get('dataset')
        if dataset is None:
            return StepResult(
                success=False,
                error='dataset is required in params',
            )

        splits = context.params.get('splits')
        output_dir = context.params.get('output_dir')

        params = DatasetParams(
            operation=DatasetOperation.DOWNLOAD,
            dataset=dataset,
            splits=splits,
            output_dir=output_dir,
        )

        action = DatasetAction(params, context.runtime_ctx)
        result = action.execute()

        # Store result in context for next step
        context.dataset = {
            'path': result.path,
            'format': result.format,
            'is_categorized': result.is_categorized,
            'count': result.count,
        }

        return StepResult(
            success=True,
            data={
                'path': str(result.path),
                'count': result.count,
            },
        )


class ConvertDatasetStep(BaseStep['TrainContext']):
    """Convert dataset between formats.

    Reads dataset info from context.dataset (set by ExportDatasetStep)
    and converts to the target format. Updates context.dataset with:
        - path: Path to converted dataset
        - config_path: Path to config file (e.g., dataset.yaml)
        - format: Target format
        - is_categorized: Whether dataset has splits
        - source_path: Original source path

    Args:
        target_format: Target format to convert to (default: 'yolo').
        source_format: Source format to convert from (default: 'dm_v2').

    Example:
        >>> registry.register(ConvertDatasetStep(target_format='yolo'))
    """

    def __init__(
        self,
        target_format: str = 'yolo',
        source_format: str = 'dm_v2',
    ) -> None:
        self._target_format = target_format
        self._source_format = source_format

    @property
    def name(self) -> str:
        return 'convert'

    @property
    def progress_weight(self) -> float:
        return 0.2

    @property
    def progress_proportion(self) -> int:
        """Proportion for overall job progress (0% - included in dataset step)."""
        return 0

    def execute(self, context: TrainContext) -> StepResult:
        from synapse_sdk.plugins.actions.dataset import (
            DatasetAction,
            DatasetOperation,
            DatasetParams,
        )

        if context.dataset is None:
            return StepResult(
                success=False,
                error='No dataset in context. ExportDatasetStep must run first.',
            )

        source_path = context.dataset.get('path')
        if source_path is None:
            return StepResult(
                success=False,
                error='No path in context.dataset',
            )

        is_categorized = context.dataset.get('is_categorized', False)

        params = DatasetParams(
            operation=DatasetOperation.CONVERT,
            path=source_path,
            source_format=self._source_format,
            target_format=self._target_format,
            is_categorized=is_categorized,
        )

        action = DatasetAction(params, context.runtime_ctx)
        result = action.execute()

        if result.config_path is None:
            return StepResult(
                success=False,
                error=f'Conversion failed: no config file generated at {result.path}',
            )

        # Update context with converted dataset info
        context.dataset = {
            'path': result.path,
            'config_path': result.config_path,
            'format': result.format,
            'is_categorized': result.is_categorized,
            'source_path': source_path,
        }

        return StepResult(
            success=True,
            data={
                'path': str(result.path),
                'config_path': str(result.config_path),
            },
        )


__all__ = ['ExportDatasetStep', 'ConvertDatasetStep']
