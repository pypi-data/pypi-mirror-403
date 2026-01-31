"""DataMaker annotation models for v1 and v2 schemas.

This module provides Pydantic models for both DataMaker schema versions:
- DMv1: Event-based, per-assignment structure
- DMv2: Collection-based, organized by media type

Example:
    >>> from synapse_sdk.utils.annotation_models.dm import (
    ...     DMv2Dataset,
    ...     DMv2BoundingBox,
    ...     DMVersion,
    ... )
    >>> # Create a DMv2 dataset
    >>> dataset = DMv2Dataset(
    ...     classification={'bounding_box': ['car', 'person']},
    ...     images=[],
    ... )
"""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.dm.common import (
    DMAttribute,
    DMVersion,
)
from synapse_sdk.utils.annotation_models.dm.v1 import (
    DMv1AnnotationBase,
    DMv1AnnotationDataItem,
    DMv1AnnotationGroupItem,
    DMv1Classification,
    DMv1Dataset,
    DMv1GroupMemberItem,
    DMv1RelationItem,
)
from synapse_sdk.utils.annotation_models.dm.v2 import (
    DMv2AnnotationBase,
    DMv2BoundingBox,
    DMv2Dataset,
    DMv2Group,
    DMv2ImageItem,
    DMv2Keypoint,
    DMv2Polygon,
    DMv2Polyline,
    DMv2Relation,
)

# =============================================================================
# Aliases for backward compatibility / convenience
# =============================================================================

# Default to V2 models for convenience
DMBoundingBox = DMv2BoundingBox
DMPolygon = DMv2Polygon
DMPolyline = DMv2Polyline
DMKeypoint = DMv2Keypoint
DMRelation = DMv2Relation
DMGroup = DMv2Group
DMImageItem = DMv2ImageItem
DMDataset = DMv2Dataset


__all__ = [
    # Version enum
    'DMVersion',
    # Shared
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
    # Aliases (default to V2)
    'DMBoundingBox',
    'DMDataset',
    'DMGroup',
    'DMImageItem',
    'DMKeypoint',
    'DMPolygon',
    'DMPolyline',
    'DMRelation',
]
