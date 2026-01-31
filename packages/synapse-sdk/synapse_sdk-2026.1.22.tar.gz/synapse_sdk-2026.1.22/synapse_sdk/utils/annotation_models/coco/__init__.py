"""COCO annotation models.

This module provides Pydantic models for COCO format:
- COCOInfo: Dataset metadata
- COCOLicense: License information
- COCOImage: Image metadata
- COCOCategory: Category/class definition
- COCOAnnotation: Single object annotation
- COCODataset: Complete dataset container

Example:
    >>> from synapse_sdk.utils.annotation_models.coco import (
    ...     COCODataset,
    ...     COCOImage,
    ...     COCOCategory,
    ...     COCOAnnotation,
    ... )
    >>> # Create a COCO dataset
    >>> dataset = COCODataset(
    ...     categories=[COCOCategory(id=1, name='person', supercategory='human')],
    ...     images=[COCOImage(id=1, file_name='img.jpg', width=640, height=480)],
    ...     annotations=[
    ...         COCOAnnotation(
    ...             id=1, image_id=1, category_id=1,
    ...             bbox=[100, 100, 50, 50], area=2500
    ...         )
    ...     ],
    ... )
    >>> # Serialize to JSON
    >>> json_str = dataset.to_json(indent=2)
    >>> # Deserialize from JSON
    >>> loaded = COCODataset.from_json(json_str)
"""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.coco.annotation import COCOAnnotation
from synapse_sdk.utils.annotation_models.coco.category import COCOCategory
from synapse_sdk.utils.annotation_models.coco.dataset import (
    COCODataset,
    COCOInfo,
    COCOLicense,
)
from synapse_sdk.utils.annotation_models.coco.image import COCOImage

__all__ = [
    'COCOAnnotation',
    'COCOCategory',
    'COCODataset',
    'COCOImage',
    'COCOInfo',
    'COCOLicense',
]
