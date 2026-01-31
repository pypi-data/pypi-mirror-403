"""YOLO annotation models.

This module provides Pydantic models for YOLO format:
- YOLOAnnotation: Single annotation with normalized coordinates
- YOLODatasetConfig: dataset.yaml configuration
- YOLOImage: Image with annotations
- YOLODataset: Full dataset structure

Example:
    >>> from synapse_sdk.utils.annotation_models.yolo import (
    ...     YOLOAnnotation,
    ...     YOLODatasetConfig,
    ... )
    >>> # Create a YOLO annotation
    >>> ann = YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3)
    >>> line = ann.to_line()  # "0 0.500000 0.500000 0.200000 0.300000"
"""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.yolo.annotation import YOLOAnnotation
from synapse_sdk.utils.annotation_models.yolo.config import YOLODatasetConfig
from synapse_sdk.utils.annotation_models.yolo.dataset import (
    YOLODataset,
    YOLOImage,
)

__all__ = [
    'YOLOAnnotation',
    'YOLODataset',
    'YOLODatasetConfig',
    'YOLOImage',
]
