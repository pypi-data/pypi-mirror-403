"""
DM Schema V1/V2 Converter Type Definitions

Created: 2025-12-11
"""

from typing import Any, TypedDict

# =============================================================================
# V1 Type Definitions
# =============================================================================


class BoundingBoxCoordinate(TypedDict, total=False):
    """V1 Bounding Box Coordinate"""

    x: float
    y: float
    width: float
    height: float
    rotation: float  # In radians, optional


class PolygonPoint(TypedDict):
    """V1 Polygon Individual Point"""

    x: float
    y: float
    id: str


# V1 Polygon Coordinate Type
PolygonCoordinate = list[PolygonPoint]


class AnnotationBase(TypedDict, total=False):
    """V1 Annotation Meta Information"""

    id: str  # 10-character random string
    tool: str  # Tool code (bounding_box, polygon, etc.)
    isLocked: bool  # Edit lock (default: False)
    isVisible: bool  # Display visibility (default: True)
    isValid: bool  # Validity (default: False)
    isDrawCompleted: bool  # Drawing completed
    classification: dict[str, Any] | None  # Classification info
    label: list[str]  # Label array


class AnnotationDataItem(TypedDict, total=False):
    """V1 Annotation Coordinate Data"""

    id: str  # Matches AnnotationBase.id
    coordinate: BoundingBoxCoordinate | PolygonCoordinate | Any


class AnnotatorDataV1(TypedDict, total=False):
    """DM Schema V1 Top-Level Structure"""

    extra: dict[str, Any]  # Per-media metadata
    annotations: dict[str, list[AnnotationBase]]  # Annotation meta
    annotationsData: dict[str, list[AnnotationDataItem]]  # Coordinate data
    relations: dict[str, list[Any]]  # Relations
    annotationGroups: dict[str, list[Any]]  # Groups
    assignmentId: int | str | None  # Task identifier


# =============================================================================
# V2 Type Definitions
# =============================================================================


class V2Attr(TypedDict):
    """V2 Attribute Object"""

    name: str
    value: Any


class V2Annotation(TypedDict, total=False):
    """V2 Annotation Common Structure"""

    id: str  # Unique identifier (10 chars, alphanumeric)
    classification: str  # Class label
    attrs: list[V2Attr]  # Additional attributes array
    data: Any  # Tool-specific data (type varies)


class V2MediaItem(TypedDict, total=False):
    """V2 Media Item (annotation arrays by tool)"""

    bounding_box: list[V2Annotation]
    polygon: list[V2Annotation]
    polyline: list[V2Annotation]
    keypoint: list[V2Annotation]
    # Other tools can be added as needed


class V2AnnotationData(TypedDict, total=False):
    """V2 Common Annotation Structure (annotation_data)"""

    classification: dict[str, list[str]]  # Class labels by tool
    images: list[V2MediaItem]  # Image media
    videos: list[V2MediaItem]  # Video media
    pcds: list[V2MediaItem]  # PCD media
    texts: list[V2MediaItem]  # Text media
    audios: list[V2MediaItem]  # Audio media
    prompts: list[V2MediaItem]  # Prompt media


class AnnotationMeta(TypedDict, total=False):
    """V1 Top-Level Structure Preserved (annotation_meta)

    V1 top-level structure preserved during V1→V2 conversion.
    Combined with annotation_data for complete V1 restoration during V2→V1 conversion.
    """

    extra: dict[str, Any]  # Per-media metadata
    annotations: dict[str, list[AnnotationBase]]  # Annotation meta
    annotationsData: dict[str, list[AnnotationDataItem]]  # Coordinate data
    relations: dict[str, list[Any]]  # Relations
    annotationGroups: dict[str, list[Any]]  # Groups
    assignmentId: int | str | None  # Task identifier


class V2ConversionResult(TypedDict):
    """V1→V2 Conversion Result (separated structure)

    V1→V2 conversion result is separated into two parts:
    - annotation_data: V2 common annotation structure (id, classification, attrs, data)
    - annotation_meta: V1 top-level structure preserved
      (extra, annotations, annotationsData, relations, annotationGroups, assignmentId)

    V2→V1 conversion:
    - If both parts exist, complete V1 restoration is possible
    - If only annotation_data exists, convert to V1 using defaults
    """

    annotation_data: V2AnnotationData
    annotation_meta: AnnotationMeta


# =============================================================================
# Bounding Box V2 Data Types
# =============================================================================

# V2 Bounding Box data: [x, y, width, height]
BoundingBoxData = list[float]

# V2 Polygon data: [[x1, y1], [x2, y2], ...]
PolygonData = list[list[float]]


# =============================================================================
# Media Type Constants
# =============================================================================

SUPPORTED_FILE_TYPES = ('image', 'video', 'pcd', 'text', 'audio', 'prompt')

MEDIA_TYPE_MAP = {
    'image': 'images',
    'video': 'videos',
    'pcd': 'pcds',
    'text': 'texts',
    'audio': 'audios',
    'prompt': 'prompts',
}

MEDIA_TYPE_REVERSE_MAP = {v: k for k, v in MEDIA_TYPE_MAP.items()}
