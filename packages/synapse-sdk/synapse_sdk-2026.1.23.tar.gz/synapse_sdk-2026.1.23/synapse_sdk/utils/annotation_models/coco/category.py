"""COCO category model.

Represents a category/class definition in COCO format.
"""

from __future__ import annotations

from pydantic import BaseModel


class COCOCategory(BaseModel):
    """COCO category/class definition.

    Represents a single category in the COCO dataset.

    Attributes:
        id: Unique category ID.
        name: Category name (e.g., 'person', 'car').
        supercategory: Parent category name (e.g., 'animal', 'vehicle').
        keypoints: List of keypoint names for this category (for keypoint detection).
        skeleton: List of keypoint pairs that define limbs/connections (for keypoint detection).

    Example:
        >>> cat = COCOCategory(id=1, name='person', supercategory='human')
        >>> cat_with_keypoints = COCOCategory(
        ...     id=2,
        ...     name='person',
        ...     supercategory='human',
        ...     keypoints=['nose', 'left_eye', 'right_eye'],
        ...     skeleton=[[0, 1], [0, 2]]
        ... )
    """

    id: int
    name: str
    supercategory: str = ''
    keypoints: list[str] | None = None
    skeleton: list[list[int]] | None = None


__all__ = ['COCOCategory']
