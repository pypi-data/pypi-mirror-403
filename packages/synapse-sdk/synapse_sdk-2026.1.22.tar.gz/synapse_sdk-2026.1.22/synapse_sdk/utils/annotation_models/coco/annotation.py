"""COCO annotation model.

Represents a single COCO annotation with bounding box and/or segmentation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class COCOAnnotation(BaseModel):
    """Single COCO annotation.

    Represents an object instance annotation in COCO format.
    Supports bounding boxes, segmentation masks, and keypoints.

    Attributes:
        id: Unique annotation ID.
        image_id: ID of the image this annotation belongs to.
        category_id: ID of the category/class.
        bbox: Bounding box [x, y, width, height] in absolute pixels.
        segmentation: Segmentation mask (list of polygons or RLE).
        area: Area of the annotation in pixels.
        iscrowd: Whether this is a crowd annotation (0 or 1).
        keypoints: List of keypoint coordinates [x1, y1, v1, x2, y2, v2, ...] where v is visibility.
        num_keypoints: Number of labeled keypoints (v > 0).
        score: Optional confidence score (for predictions).

    Example:
        >>> ann = COCOAnnotation(
        ...     id=1,
        ...     image_id=1,
        ...     category_id=1,
        ...     bbox=[100, 100, 50, 50],
        ...     segmentation=[[100, 100, 150, 100, 150, 150, 100, 150]],
        ...     area=2500,
        ...     iscrowd=0,
        ... )
    """

    id: int
    image_id: int
    category_id: int
    bbox: list[float] = Field(min_length=4, max_length=4)
    segmentation: list[list[float]] | dict | None = None  # Polygon or RLE
    area: float
    iscrowd: int = Field(ge=0, le=1, default=0)
    keypoints: list[float] | None = None  # [x1, y1, v1, x2, y2, v2, ...]
    num_keypoints: int | None = None
    score: float | None = Field(None, ge=0, le=1)  # For predictions


__all__ = ['COCOAnnotation']
