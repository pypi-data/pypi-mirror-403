"""Annotation models for various dataset formats.

This module provides Pydantic models for annotation schemas:
- DataMaker (DM) v1 & v2: Synapse's native annotation format
- YOLO: Popular object detection format
- COCO: Microsoft COCO format
- Pascal VOC: Pascal Visual Object Classes format

All models support:
- Type-safe validation with Pydantic
- Serialization/deserialization (JSON, XML, YAML)
- Helper methods for common operations

Example:
    >>> # DataMaker v2
    >>> from synapse_sdk.utils.annotation_models import DMv2Dataset
    >>> dataset = DMv2Dataset(
    ...     classification={'bounding_box': ['car', 'person']},
    ...     images=[],
    ... )

    >>> # YOLO
    >>> from synapse_sdk.utils.annotation_models import YOLOAnnotation
    >>> ann = YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3)

    >>> # COCO
    >>> from synapse_sdk.utils.annotation_models import COCODataset
    >>> coco = COCODataset(categories=[], images=[], annotations=[])
    >>> json_str = coco.to_json()

    >>> # Pascal VOC
    >>> from synapse_sdk.utils.annotation_models import PascalAnnotation
    >>> pascal = PascalAnnotation(filename='img.jpg', size=..., objects=[])
    >>> xml_str = pascal.to_xml()

Schema Organization:
    annotation_models/
    ├── dm/         # DataMaker v1 & v2 models
    ├── yolo/       # YOLO format models
    ├── coco/       # COCO format models
    └── pascal/     # Pascal VOC models
"""

from __future__ import annotations

# COCO models
from synapse_sdk.utils.annotation_models.coco import (
    COCOAnnotation,
    COCOCategory,
    COCODataset,
    COCOImage,
    COCOInfo,
    COCOLicense,
)

# DataMaker models
from synapse_sdk.utils.annotation_models.dm import (
    # Version & Shared
    DMAttribute,
    # Aliases (V2 defaults)
    DMBoundingBox,
    DMDataset,
    DMGroup,
    DMImageItem,
    DMKeypoint,
    DMPolygon,
    DMPolyline,
    DMRelation,
    # V1 Models
    DMv1AnnotationBase,
    DMv1AnnotationDataItem,
    DMv1AnnotationGroupItem,
    DMv1Classification,
    DMv1Dataset,
    DMv1GroupMemberItem,
    DMv1RelationItem,
    # V2 Models
    DMv2AnnotationBase,
    DMv2BoundingBox,
    DMv2Dataset,
    DMv2Group,
    DMv2ImageItem,
    DMv2Keypoint,
    DMv2Polygon,
    DMv2Polyline,
    DMv2Relation,
    DMVersion,
)

# Pascal VOC models
from synapse_sdk.utils.annotation_models.pascal import (
    PascalAnnotation,
    PascalBndBox,
    PascalObject,
    PascalSize,
    PascalSource,
)

# YOLO models
from synapse_sdk.utils.annotation_models.yolo import (
    YOLOAnnotation,
    YOLODataset,
    YOLODatasetConfig,
    YOLOImage,
)

__all__ = [
    # ==================== DataMaker ====================
    # Version & Shared
    'DMVersion',
    'DMAttribute',
    # V1 Models
    'DMv1AnnotationBase',
    'DMv1AnnotationDataItem',
    'DMv1AnnotationGroupItem',
    'DMv1Classification',
    'DMv1Dataset',
    'DMv1GroupMemberItem',
    'DMv1RelationItem',
    # V2 Models
    'DMv2AnnotationBase',
    'DMv2BoundingBox',
    'DMv2Dataset',
    'DMv2Group',
    'DMv2ImageItem',
    'DMv2Keypoint',
    'DMv2Polygon',
    'DMv2Polyline',
    'DMv2Relation',
    # Aliases (V2 defaults)
    'DMBoundingBox',
    'DMDataset',
    'DMGroup',
    'DMImageItem',
    'DMKeypoint',
    'DMPolygon',
    'DMPolyline',
    'DMRelation',
    # ==================== YOLO ====================
    'YOLOAnnotation',
    'YOLODataset',
    'YOLODatasetConfig',
    'YOLOImage',
    # ==================== COCO ====================
    'COCOAnnotation',
    'COCOCategory',
    'COCODataset',
    'COCOImage',
    'COCOInfo',
    'COCOLicense',
    # ==================== Pascal VOC ====================
    'PascalAnnotation',
    'PascalBndBox',
    'PascalObject',
    'PascalSize',
    'PascalSource',
]
