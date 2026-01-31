"""DataMaker V2 schema models (collection-based, organized by media type).

DMv2 uses a collection-based structure organized by media type with typed annotation arrays.
Supports bounding boxes, polygons, polylines, keypoints, relations, and groups.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from synapse_sdk.utils.annotation_models.dm.common import DMAttribute


class DMv2AnnotationBase(BaseModel):
    """V2 base annotation with id, classification, and attrs.

    Attributes:
        id: Unique annotation ID (alphanumeric, typically 10 chars).
        classification: Class label for this annotation.
        attrs: Optional list of attributes.
    """

    id: str = Field(pattern=r'^[a-zA-Z0-9_-]+$')
    classification: str
    attrs: list[DMAttribute] = Field(default_factory=list)


class DMv2BoundingBox(DMv2AnnotationBase):
    """V2 bounding box annotation.

    Attributes:
        data: [x, y, width, height] in absolute pixel coordinates.
    """

    data: tuple[float, float, float, float]


class DMv2Polygon(DMv2AnnotationBase):
    """V2 polygon annotation.

    Attributes:
        data: List of [x, y] points forming the polygon.
    """

    data: list[tuple[float, float]]


class DMv2Polyline(DMv2AnnotationBase):
    """V2 polyline annotation (open path).

    Attributes:
        data: List of [x, y] points forming the polyline.
    """

    data: list[tuple[float, float]]


class DMv2Keypoint(DMv2AnnotationBase):
    """V2 single keypoint annotation.

    Attributes:
        data: [x, y] coordinate.
    """

    data: tuple[float, float]


class DMv2Relation(DMv2AnnotationBase):
    """V2 relation annotation linking two annotations.

    Attributes:
        data: [from_id, to_id] annotation IDs.
    """

    data: tuple[str, str]


class DMv2Group(DMv2AnnotationBase):
    """V2 group annotation containing multiple annotation IDs.

    Attributes:
        data: List of annotation IDs in the group.
    """

    data: list[str]


class DMv2ImageItem(BaseModel):
    """V2 container for 2D image annotations.

    Groups all annotation types for a single image.
    """

    bounding_box: list[DMv2BoundingBox] = Field(default_factory=list)
    polygon: list[DMv2Polygon] = Field(default_factory=list)
    polyline: list[DMv2Polyline] = Field(default_factory=list)
    keypoint: list[DMv2Keypoint] = Field(default_factory=list)
    relation: list[DMv2Relation] = Field(default_factory=list)
    group: list[DMv2Group] = Field(default_factory=list)


class DMv2Dataset(BaseModel):
    """DataMaker V2 dataset schema (collection-based).

    Organized by media type with typed annotation arrays.

    Attributes:
        classification: Mapping of tool types to available class labels.
        images: List of image annotation containers.

    Example:
        >>> dataset = DMv2Dataset(
        ...     classification={'bounding_box': ['car', 'person']},
        ...     images=[DMv2ImageItem(bounding_box=[...])],
        ... )
        >>> class_names = dataset.get_class_names('bounding_box')
    """

    classification: dict[str, list[str]] = Field(default_factory=dict)
    images: list[DMv2ImageItem] = Field(default_factory=list)

    def get_class_names(self, tool: str = 'bounding_box') -> list[str]:
        """Get class names for a specific annotation tool.

        Args:
            tool: Tool type (e.g., 'bounding_box', 'polygon').

        Returns:
            List of class names for the tool.
        """
        return self.classification.get(tool, [])

    def get_all_class_names(self) -> list[str]:
        """Get all unique class names across all tools.

        Returns:
            Sorted list of unique class names.
        """
        all_classes: set[str] = set()
        for classes in self.classification.values():
            all_classes.update(classes)
        return sorted(all_classes)


__all__ = [
    'DMv2AnnotationBase',
    'DMv2BoundingBox',
    'DMv2Dataset',
    'DMv2Group',
    'DMv2ImageItem',
    'DMv2Keypoint',
    'DMv2Polygon',
    'DMv2Polyline',
    'DMv2Relation',
]
