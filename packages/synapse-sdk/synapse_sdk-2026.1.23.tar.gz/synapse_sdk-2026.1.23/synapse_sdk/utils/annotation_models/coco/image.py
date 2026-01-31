"""COCO image model.

Represents image metadata in COCO format.
"""

from __future__ import annotations

from pydantic import BaseModel


class COCOImage(BaseModel):
    """COCO image metadata.

    Represents metadata for a single image in the COCO dataset.

    Attributes:
        id: Unique image ID.
        file_name: Image file name (e.g., '000000001234.jpg').
        width: Image width in pixels.
        height: Image height in pixels.
        date_captured: Optional datetime when image was captured.
        license: Optional license ID.
        coco_url: Optional COCO dataset URL.
        flickr_url: Optional Flickr URL.

    Example:
        >>> img = COCOImage(
        ...     id=1,
        ...     file_name='image001.jpg',
        ...     width=640,
        ...     height=480,
        ... )
    """

    id: int
    file_name: str
    width: int
    height: int
    date_captured: str | None = None
    license: int | None = None
    coco_url: str | None = None
    flickr_url: str | None = None


__all__ = ['COCOImage']
