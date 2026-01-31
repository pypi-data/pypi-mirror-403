"""Pascal VOC annotation component models.

Models for individual components of Pascal VOC XML annotations.
"""

from __future__ import annotations

from pydantic import BaseModel


class PascalSize(BaseModel):
    """Image size information.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.
        depth: Number of channels (typically 3 for RGB).
    """

    width: int
    height: int
    depth: int = 3


class PascalBndBox(BaseModel):
    """Bounding box coordinates.

    Pascal VOC uses absolute pixel coordinates with (xmin, ymin) as top-left
    and (xmax, ymax) as bottom-right.

    Attributes:
        xmin: Minimum x coordinate (left).
        ymin: Minimum y coordinate (top).
        xmax: Maximum x coordinate (right).
        ymax: Maximum y coordinate (bottom).
    """

    xmin: int
    ymin: int
    xmax: int
    ymax: int


class PascalObject(BaseModel):
    """Single object annotation.

    Represents one object instance in the image.

    Attributes:
        name: Class name (e.g., 'person', 'car').
        pose: Object pose (e.g., 'Frontal', 'Left', 'Right', 'Rear', 'Unspecified').
        truncated: Whether object is truncated (0 or 1).
        difficult: Whether object is difficult to recognize (0 or 1).
        bndbox: Bounding box coordinates.
        occluded: Optional occlusion flag (0 or 1).

    Example:
        >>> obj = PascalObject(
        ...     name='person',
        ...     pose='Frontal',
        ...     truncated=0,
        ...     difficult=0,
        ...     bndbox=PascalBndBox(xmin=100, ymin=100, xmax=200, ymax=300),
        ... )
    """

    name: str
    pose: str = 'Unspecified'
    truncated: int = 0
    difficult: int = 0
    bndbox: PascalBndBox
    occluded: int | None = None


class PascalSource(BaseModel):
    """Source information.

    Metadata about the source of the annotation.

    Attributes:
        database: Source database name (e.g., 'The VOC2007 Database').
        annotation: Annotation source.
        image: Image source.
    """

    database: str = 'Unknown'
    annotation: str | None = None
    image: str | None = None


__all__ = [
    'PascalBndBox',
    'PascalObject',
    'PascalSize',
    'PascalSource',
]
