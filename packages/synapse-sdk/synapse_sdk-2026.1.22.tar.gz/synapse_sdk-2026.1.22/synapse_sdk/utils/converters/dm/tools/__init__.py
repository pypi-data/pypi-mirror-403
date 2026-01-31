"""
DM Schema V1/V2 Tool-Specific Processors

Created: 2025-12-11

Implement and register processors in this module when adding new tool support.
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ToolProcessor(Protocol):
    """Tool-Specific Conversion Processor Interface

    Implement this protocol when adding new tool support.

    Attributes:
        tool_name: Tool name (e.g., 'bounding_box', 'polygon')

    Example:
        >>> class KeypointProcessor:
        ...     tool_name = "keypoint"
        ...
        ...     def to_v2(self, v1_annotation, v1_data):
        ...         # V1 → V2 conversion logic
        ...         return {...}
        ...
        ...     def to_v1(self, v2_annotation):
        ...         # V2 → V1 conversion logic
        ...         return ({...}, {...})
    """

    @property
    def tool_name(self) -> str:
        """Tool name (e.g., 'bounding_box', 'polygon')"""
        ...

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 annotation to V2 format

        Args:
            v1_annotation: V1 annotations[] item
            v1_data: V1 annotationsData[] item (same ID)

        Returns:
            V2 format annotation object (id, classification, attrs, data)

        Raises:
            ValueError: Data cannot be converted
        """
        ...

    def to_v1(self, v2_annotation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Convert V2 annotation to V1 format

        Args:
            v2_annotation: V2 annotation object

        Returns:
            (V1 annotation, V1 annotationData) tuple

        Raises:
            ValueError: Data cannot be converted
        """
        ...


# =============================================================================
# Processor Registry
# =============================================================================

# Global registry storing registered processors
_PROCESSOR_REGISTRY: dict[str, ToolProcessor] = {}


def register_tool_processor(processor: ToolProcessor) -> None:
    """Register a tool processor to the global registry

    Args:
        processor: ToolProcessor implementation
    """
    _PROCESSOR_REGISTRY[processor.tool_name] = processor


def get_tool_processor(tool_name: str) -> ToolProcessor | None:
    """Get a tool processor from the global registry

    Args:
        tool_name: Tool name

    Returns:
        Registered processor or None
    """
    return _PROCESSOR_REGISTRY.get(tool_name)


def get_all_processors() -> dict[str, ToolProcessor]:
    """Return all registered processors

    Returns:
        Tool name → processor dictionary
    """
    return _PROCESSOR_REGISTRY.copy()


# =============================================================================
# Processor Import and Auto-Registration
# =============================================================================

# Auto-registered when processor modules are imported
# Note: Actual processors are imported later to prevent circular imports


def _register_default_processors() -> None:
    """Register default processors

    Called on module load to register default processors.
    """
    try:
        from .bounding_box import BoundingBoxProcessor

        register_tool_processor(BoundingBoxProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .polygon import PolygonProcessor

        register_tool_processor(PolygonProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .polyline import PolylineProcessor

        register_tool_processor(PolylineProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .keypoint import KeypointProcessor

        register_tool_processor(KeypointProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .bounding_box_3d import BoundingBox3DProcessor

        register_tool_processor(BoundingBox3DProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .segmentation import SegmentationProcessor

        register_tool_processor(SegmentationProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .named_entity import NamedEntityProcessor

        register_tool_processor(NamedEntityProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .segmentation_3d import Segmentation3DProcessor

        register_tool_processor(Segmentation3DProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .classification import ClassificationProcessor

        register_tool_processor(ClassificationProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .relation import RelationProcessor

        register_tool_processor(RelationProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .prompt import PromptProcessor

        register_tool_processor(PromptProcessor())
    except ImportError:
        pass  # Not yet implemented

    try:
        from .answer import AnswerProcessor

        register_tool_processor(AnswerProcessor())
    except ImportError:
        pass  # Not yet implemented


# Attempt to register default processors on module load
_register_default_processors()


__all__ = [
    'ToolProcessor',
    'register_tool_processor',
    'get_tool_processor',
    'get_all_processors',
]
