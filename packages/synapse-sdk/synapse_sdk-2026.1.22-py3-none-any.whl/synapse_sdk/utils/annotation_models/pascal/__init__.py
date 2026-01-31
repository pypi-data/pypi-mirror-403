"""Pascal VOC annotation models.

This module provides Pydantic models for Pascal VOC XML format:
- PascalSize: Image size information
- PascalBndBox: Bounding box coordinates
- PascalObject: Single object annotation
- PascalSource: Source metadata
- PascalAnnotation: Complete annotation structure

Example:
    >>> from synapse_sdk.utils.annotation_models.pascal import (
    ...     PascalAnnotation,
    ...     PascalObject,
    ...     PascalBndBox,
    ...     PascalSize,
    ... )
    >>> # Create a Pascal VOC annotation
    >>> ann = PascalAnnotation(
    ...     filename='image001.jpg',
    ...     size=PascalSize(width=640, height=480, depth=3),
    ...     objects=[
    ...         PascalObject(
    ...             name='person',
    ...             bndbox=PascalBndBox(xmin=100, ymin=100, xmax=200, ymax=300)
    ...         )
    ...     ],
    ... )
    >>> # Serialize to XML
    >>> xml_str = ann.to_xml()
    >>> # Deserialize from XML
    >>> loaded = PascalAnnotation.from_xml(xml_str)
"""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.pascal.annotation import (
    PascalBndBox,
    PascalObject,
    PascalSize,
    PascalSource,
)
from synapse_sdk.utils.annotation_models.pascal.dataset import PascalAnnotation

__all__ = [
    'PascalAnnotation',
    'PascalBndBox',
    'PascalObject',
    'PascalSize',
    'PascalSource',
]
