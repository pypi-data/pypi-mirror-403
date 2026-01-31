"""
DM Schema V2 → V1 Converter

Created: 2025-12-11

V2→V1 conversion:
- If both annotation_data and annotation_meta exist, complete V1 restoration
- If only annotation_data exists, convert to V1 using defaults
"""

from typing import Any

from .base import BaseDMConverter
from .types import (
    MEDIA_TYPE_REVERSE_MAP,
    AnnotationMeta,
    V2ConversionResult,
)


class DMV2ToV1Converter(BaseDMConverter):
    """Converter from DM Schema V2 to V1

    V2→V1 conversion:
    - If both annotation_data and annotation_meta exist, complete V1 restoration
    - If only annotation_data exists, convert to V1 using defaults

    Example:
        >>> converter = DMV2ToV1Converter()
        >>> # Complete conversion
        >>> v1_data = converter.convert(v2_result)
        >>> # Convert with annotation_data only
        >>> v1_data = converter.convert({"annotation_data": annotation_data})
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

    def convert(
        self,
        v2_data: V2ConversionResult | dict[str, Any],
        annotation_meta: AnnotationMeta | None = None,
    ) -> dict[str, Any]:
        """Convert V2 data to V1 format

        Args:
            v2_data: DM Schema V2 format data
            annotation_meta: Optional V1 top-level structure passed separately

        Returns:
            DM Schema V1 format data

        Raises:
            ValueError: Missing required fields or invalid format
        """
        # Extract annotation_data
        if 'annotation_data' in v2_data:
            annotation_data = v2_data['annotation_data']
            # Extract annotation_meta (use from v2_data if present, else use parameter)
            meta = v2_data.get('annotation_meta') or annotation_meta
        else:
            # annotation_data passed directly
            annotation_data = v2_data
            meta = annotation_meta

        # Input validation
        if not annotation_data:
            raise ValueError("V2 data requires 'annotation_data'")

        # Build V1 data
        return self._merge_data_and_meta(annotation_data, meta)

    def _merge_data_and_meta(
        self,
        annotation_data: dict[str, Any],
        annotation_meta: AnnotationMeta | None,
    ) -> dict[str, Any]:
        """Merge annotation_data and annotation_meta to create V1 format

        Args:
            annotation_data: V2 common annotation structure
            annotation_meta: V1 top-level structure (restores meta info if present)

        Returns:
            Merged V1 format data
        """
        annotations: dict[str, list[dict[str, Any]]] = {}
        annotations_data: dict[str, list[dict[str, Any]]] = {}

        # Process by media type
        media_index_by_type: dict[str, int] = {}

        for plural_type in ['images', 'videos', 'pcds', 'texts', 'audios', 'prompts']:
            if plural_type not in annotation_data:
                continue

            singular_type = MEDIA_TYPE_REVERSE_MAP.get(plural_type, plural_type.rstrip('s'))
            media_index_by_type[singular_type] = 0

            for media_item in annotation_data[plural_type]:
                # Generate media ID
                media_index_by_type[singular_type] += 1
                media_id = f'{singular_type}_{media_index_by_type[singular_type]}'

                # Convert by tool
                ann_list, data_list = self._convert_media_item(media_item, media_id, annotation_meta)

                if ann_list:
                    annotations[media_id] = ann_list
                if data_list:
                    annotations_data[media_id] = data_list

        # Build V1 result
        result: dict[str, Any] = {
            'annotations': annotations,
            'annotationsData': annotations_data,
        }

        # Restore additional fields if annotation_meta exists
        if annotation_meta:
            result['extra'] = annotation_meta.get('extra', {})
            result['relations'] = annotation_meta.get('relations', {})
            result['annotationGroups'] = annotation_meta.get('annotationGroups', {})
            result['assignmentId'] = annotation_meta.get('assignmentId')
        else:
            # Default values
            result['extra'] = {}
            result['relations'] = {}
            result['annotationGroups'] = {}
            result['assignmentId'] = None

        return result

    def _convert_media_item(
        self,
        media_item: dict[str, Any],
        media_id: str,
        annotation_meta: AnnotationMeta | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Convert V2 media item to V1 annotations/annotationsData

        Args:
            media_item: V2 media item
            media_id: Media ID to generate
            annotation_meta: V1 top-level structure (for meta info restoration)

        Returns:
            (V1 annotations list, V1 annotationsData list)
        """
        annotations: list[dict[str, Any]] = []
        annotations_data: list[dict[str, Any]] = []

        # Process by tool
        for tool_name, v2_annotations in media_item.items():
            processor = self.get_processor(tool_name)
            if not processor:
                continue

            for v2_ann in v2_annotations:
                # Convert to V1
                v1_ann, v1_data = processor.to_v1(v2_ann)

                # Restore meta info from annotation_meta
                if annotation_meta:
                    v1_ann = self._restore_meta_fields(v1_ann, annotation_meta, v2_ann.get('id', ''), media_id)
                else:
                    # Set default values
                    v1_ann.setdefault('isLocked', False)
                    v1_ann.setdefault('isVisible', True)
                    v1_ann.setdefault('isValid', False)
                    v1_ann.setdefault('isDrawCompleted', True)
                    v1_ann.setdefault('label', [])

                annotations.append(v1_ann)
                annotations_data.append(v1_data)

        return annotations, annotations_data

    def _restore_meta_fields(
        self,
        v1_annotation: dict[str, Any],
        annotation_meta: AnnotationMeta,
        annotation_id: str,
        media_id: str,
    ) -> dict[str, Any]:
        """Restore V1 annotation meta fields from annotation_meta

        Args:
            v1_annotation: Base converted V1 annotation
            annotation_meta: V1 top-level structure
            annotation_id: Annotation ID
            media_id: Media ID

        Returns:
            V1 annotation with restored meta fields
        """
        # Find annotation in annotation_meta
        meta_annotations = annotation_meta.get('annotations', {})

        # Try to find by media_id
        source_media_id = None
        for mid in meta_annotations:
            for ann in meta_annotations[mid]:
                if ann.get('id') == annotation_id:
                    source_media_id = mid
                    break
            if source_media_id:
                break

        if not source_media_id:
            # Use defaults if not found
            v1_annotation.setdefault('isLocked', False)
            v1_annotation.setdefault('isVisible', True)
            v1_annotation.setdefault('isValid', False)
            v1_annotation.setdefault('isDrawCompleted', True)
            v1_annotation.setdefault('label', [])
            return v1_annotation

        # Restore meta info from the found annotation
        for meta_ann in meta_annotations[source_media_id]:
            if meta_ann.get('id') == annotation_id:
                # Restore meta fields
                v1_annotation['isLocked'] = meta_ann.get('isLocked', False)
                v1_annotation['isVisible'] = meta_ann.get('isVisible', True)
                v1_annotation['isValid'] = meta_ann.get('isValid', False)
                v1_annotation['isDrawCompleted'] = meta_ann.get('isDrawCompleted', True)
                v1_annotation['label'] = meta_ann.get('label', [])

                # Merge classification if present in meta
                meta_classification = meta_ann.get('classification')
                if meta_classification:
                    # Keep existing class from classification and merge other fields
                    current_class = v1_annotation.get('classification', {}).get('class')
                    v1_annotation['classification'] = meta_classification.copy()
                    if current_class:
                        v1_annotation['classification']['class'] = current_class

                break

        return v1_annotation
