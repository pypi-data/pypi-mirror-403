"""
DM Schema V1/V2 Converter Base Class

Created: 2025-12-11
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from .types import MEDIA_TYPE_MAP, SUPPORTED_FILE_TYPES
from .utils import detect_file_type, extract_media_type_info

if TYPE_CHECKING:
    from .tools import ToolProcessor


class BaseDMConverter(ABC):
    """DM Schema Converter Base Class

    Abstract base class for all DM converters.

    Attributes:
        file_type: File type to process (None for auto-detection)
        SUPPORTED_FILE_TYPES: Tuple of supported file types
        MEDIA_TYPE_MAP: Media type mapping dictionary

    Example:
        >>> class MyConverter(BaseDMConverter):
        ...     def convert(self, data):
        ...         # implementation
        ...         pass
    """

    SUPPORTED_FILE_TYPES = SUPPORTED_FILE_TYPES
    MEDIA_TYPE_MAP = MEDIA_TYPE_MAP

    def __init__(self, file_type: str | None = None) -> None:
        """
        Args:
            file_type: File type to process (None for auto-detection)

        Raises:
            ValueError: Unsupported file type
        """
        if file_type is not None and file_type not in self.SUPPORTED_FILE_TYPES:
            raise ValueError(
                f'Unsupported file type: {file_type}. Supported types: {", ".join(self.SUPPORTED_FILE_TYPES)}'
            )
        self.file_type = file_type
        self._tool_processors: dict[str, 'ToolProcessor'] = {}
        self._setup_tool_processors()

    @abstractmethod
    def _setup_tool_processors(self) -> None:
        """Register tool processors

        Subclasses implement this to register supported tool processors.

        Example:
            >>> def _setup_tool_processors(self):
            ...     from .tools import BoundingBoxProcessor, PolygonProcessor
            ...     self.register_processor(BoundingBoxProcessor())
            ...     self.register_processor(PolygonProcessor())
        """
        ...

    def register_processor(self, processor: 'ToolProcessor') -> None:
        """Register a tool processor

        Use this method to register processors when adding new tool support.
        Allows extension without modifying existing code (AR-001).

        Args:
            processor: ToolProcessor implementation

        Example:
            >>> class KeypointProcessor:
            ...     tool_name = "keypoint"
            ...     def to_v2(self, v1_annotation, v1_data): ...
            ...     def to_v1(self, v2_annotation): ...
            >>> converter.register_processor(KeypointProcessor())
        """
        self._tool_processors[processor.tool_name] = processor

    def get_processor(self, tool_name: str) -> 'ToolProcessor | None':
        """Get a registered tool processor

        Args:
            tool_name: Tool name (e.g., 'bounding_box', 'polygon')

        Returns:
            Registered processor or None
        """
        return self._tool_processors.get(tool_name)

    @abstractmethod
    def convert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Perform data conversion

        Args:
            data: Input data (V1 or V2)

        Returns:
            Converted data (V2 or V1)

        Raises:
            ValueError: Data cannot be converted
        """
        ...

    def _detect_file_type(self, data: dict[str, Any], is_v2: bool = False) -> str:
        """Auto-detect file type from data

        Args:
            data: Input data
            is_v2: Whether the format is V2

        Returns:
            Detected file type ('image', 'video', etc.)

        Raises:
            ValueError: Unable to detect file type
        """
        if self.file_type:
            return self.file_type
        return detect_file_type(data, is_v2)

    def _extract_media_type_info(self, media_id: str) -> tuple[str, str]:
        """Extract type information from media ID

        Args:
            media_id: Media ID (e.g., 'image_1', 'video_2')

        Returns:
            (singular, plural) tuple (e.g., ('image', 'images'))
        """
        return extract_media_type_info(media_id)
