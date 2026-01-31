"""
DM Schema V1 → V2 Converter

Created: 2025-12-11

V1→V2 conversion separates the result into annotation_data and annotation_meta.
"""

from typing import Any

from .base import BaseDMConverter
from .types import (
    AnnotationMeta,
    V2AnnotationData,
    V2ConversionResult,
)


class DMV1ToV2Converter(BaseDMConverter):
    """Converter from DM Schema V1 to V2

    V1→V2 conversion separates the result into annotation_data and annotation_meta.

    Example:
        >>> converter = DMV1ToV2Converter()
        >>> result = converter.convert(v1_data)
        >>> annotation_data = result["annotation_data"]
        >>> annotation_meta = result["annotation_meta"]
    """

    def _setup_tool_processors(self) -> None:
        """Register tool processors"""
        from .tools.bounding_box import BoundingBoxProcessor

        self.register_processor(BoundingBoxProcessor())

        # polygon to be added later
        try:
            from .tools.polygon import PolygonProcessor

            self.register_processor(PolygonProcessor())
        except ImportError:
            pass

        try:
            from .tools.polyline import PolylineProcessor

            self.register_processor(PolylineProcessor())
        except ImportError:
            pass

        try:
            from .tools.keypoint import KeypointProcessor

            self.register_processor(KeypointProcessor())
        except ImportError:
            pass

        try:
            from .tools.bounding_box_3d import BoundingBox3DProcessor

            self.register_processor(BoundingBox3DProcessor())
        except ImportError:
            pass

        try:
            from .tools.segmentation import SegmentationProcessor

            self.register_processor(SegmentationProcessor())
        except ImportError:
            pass

        try:
            from .tools.named_entity import NamedEntityProcessor

            self.register_processor(NamedEntityProcessor())
        except ImportError:
            pass

        try:
            from .tools.segmentation_3d import Segmentation3DProcessor

            self.register_processor(Segmentation3DProcessor())
        except ImportError:
            pass

        try:
            from .tools.classification import ClassificationProcessor

            self.register_processor(ClassificationProcessor())
        except ImportError:
            pass

        try:
            from .tools.relation import RelationProcessor

            self.register_processor(RelationProcessor())
        except ImportError:
            pass

        try:
            from .tools.prompt import PromptProcessor

            self.register_processor(PromptProcessor())
        except ImportError:
            pass

        try:
            from .tools.answer import AnswerProcessor

            self.register_processor(AnswerProcessor())
        except ImportError:
            pass

    def convert(self, v1_data: dict[str, Any]) -> V2ConversionResult:
        """Convert V1 data to V2 format (separated result)

        Args:
            v1_data: DM Schema V1 format data

        Returns:
            V2ConversionResult: Separated conversion result
                - annotation_data: V2 common annotation structure
                - annotation_meta: Preserved V1 top-level structure

        Raises:
            ValueError: Missing required fields or invalid format
        """
        # Input validation
        if 'annotations' not in v1_data:
            raise ValueError("V1 data requires 'annotations' field")
        if 'annotationsData' not in v1_data:
            raise ValueError("V1 data requires 'annotationsData' field")

        # Create annotation_data
        annotation_data = self._build_annotation_data(v1_data)

        # Create annotation_meta (preserve V1 top-level structure)
        annotation_meta = self._build_annotation_meta(v1_data)

        return {
            'annotation_data': annotation_data,
            'annotation_meta': annotation_meta,
        }

    def _build_annotation_data(self, v1_data: dict[str, Any]) -> V2AnnotationData:
        """Create annotation_data (V2 common structure) from V1 data

        Args:
            v1_data: V1 data

        Returns:
            V2 common annotation structure
        """
        annotations = v1_data.get('annotations', {})
        annotations_data = v1_data.get('annotationsData', {})

        # Build classification map
        classification_map = self._build_classification_map(annotations)

        # Convert annotations by media type
        result: V2AnnotationData = {
            'classification': classification_map,
        }

        # Process by media ID
        for media_id, ann_list in annotations.items():
            # Detect media type
            singular_type, plural_type = self._extract_media_type_info(media_id)

            # Initialize media type array
            if plural_type not in result:
                result[plural_type] = []

            # Convert media item
            media_item = self._convert_media_item(media_id, ann_list, annotations_data.get(media_id, []))

            result[plural_type].append(media_item)

        return result

    def _build_annotation_meta(self, v1_data: dict[str, Any]) -> AnnotationMeta:
        """Create annotation_meta (V1 top-level structure) from V1 data

        Args:
            v1_data: Complete V1 data

        Returns:
            V1 top-level structure (preserved as-is)
        """
        return {
            'extra': v1_data.get('extra', {}),
            'annotations': v1_data.get('annotations', {}),
            'annotationsData': v1_data.get('annotationsData', {}),
            'relations': v1_data.get('relations', {}),
            'annotationGroups': v1_data.get('annotationGroups', {}),
            'assignmentId': v1_data.get('assignmentId'),
        }

    def _build_classification_map(self, annotations: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
        """Build classification map from annotations

        Args:
            annotations: V1 annotations data

        Returns:
            Class label map by tool
            e.g., {"bounding_box": ["person", "car"], "polygon": ["road"]}
        """
        classification_map: dict[str, set[str]] = {}

        for media_id, ann_list in annotations.items():
            for ann in ann_list:
                tool = ann.get('tool', '')
                classification_obj = ann.get('classification') or {}
                class_label = classification_obj.get('class', '')

                if tool and class_label:
                    if tool not in classification_map:
                        classification_map[tool] = set()
                    classification_map[tool].add(class_label)

        # Convert set to list
        return {tool: sorted(list(labels)) for tool, labels in classification_map.items()}

    def _convert_media_item(
        self,
        media_id: str,
        annotations: list[dict[str, Any]],
        annotations_data: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        """Convert annotations for a single media item

        Args:
            media_id: Media ID
            annotations: V1 annotations for this media
            annotations_data: V1 annotationsData for this media

        Returns:
            V2 annotations grouped by tool
        """
        # Create ID → annotationData mapping
        data_by_id = {item['id']: item for item in annotations_data if 'id' in item}

        # Group by tool
        result: dict[str, list[dict[str, Any]]] = {}

        for ann in annotations:
            ann_id = ann.get('id', '')
            tool = ann.get('tool', '')

            if not tool:
                continue

            # Get processor
            processor = self.get_processor(tool)
            if not processor:
                # Raise error for unsupported tool
                supported_tools = list(self._tool_processors.keys())
                raise ValueError(f"Unsupported tool: '{tool}'. Supported tools: {', '.join(sorted(supported_tools))}")

            # Find annotationData for this ID
            ann_data = data_by_id.get(ann_id, {})

            # Convert to V2
            v2_annotation = processor.to_v2(ann, ann_data)

            # Group by tool
            if tool not in result:
                result[tool] = []
            result[tool].append(v2_annotation)

        return result
