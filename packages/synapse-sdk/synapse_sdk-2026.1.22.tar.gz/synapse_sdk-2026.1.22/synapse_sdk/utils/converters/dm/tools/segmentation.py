"""
Segmentation Tool Processor (Image/Video Unified)

Created: 2025-12-12

Conversion Rules (see data-model.md 9.3, 9.4):

Image Segmentation:
V1 → V2:
  - pixel_indices [...] → data [...]

V2 → V1:
  - data [...] → pixel_indices [...]

Video Segmentation:
V1 → V2:
  - section {startFrame, endFrame} → data {startFrame, endFrame}

V2 → V1:
  - data {startFrame, endFrame} → section {startFrame, endFrame}
"""

from typing import Any


class SegmentationProcessor:
    """Segmentation Tool Processor (Image/Video Unified)

    Image Segmentation:
        V1 pixel_indices: [int, ...]
        V2 data: [int, ...]

    Video Segmentation:
        V1 section: {startFrame, endFrame}
        V2 data: {startFrame, endFrame}

    Differentiate image/video by data structure:
    - list: Image segmentation (pixel_indices)
    - dict: Video segmentation (section)
    """

    tool_name = 'segmentation'

    # V1 meta fields (not stored in attrs)
    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}

    # Special attrs not restored to V1 classification (_ prefix)
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 segmentation to V2

        Args:
            v1_annotation: V1 annotations[] item
            v1_data: V1 annotationsData[] item (same ID)

        Returns:
            V2 format segmentation annotation
        """
        classification_obj = v1_annotation.get('classification') or {}

        # Process based on data type
        if 'pixel_indices' in v1_data:
            # Image segmentation
            data = v1_data.get('pixel_indices', [])
        elif 'section' in v1_data:
            # Video segmentation
            section = v1_data.get('section', {})
            data = {
                'startFrame': section.get('startFrame', 0),
                'endFrame': section.get('endFrame', 0),
            }
        else:
            # Default (empty array)
            data = []

        # Build V2 attrs
        attrs: list[dict[str, Any]] = []

        # Add other classification properties to attrs (excluding class)
        for key, value in classification_obj.items():
            if key != 'class':
                attrs.append({'name': key, 'value': value})

        # Build V2 annotation
        return {
            'id': v1_annotation.get('id', ''),
            'classification': classification_obj.get('class', ''),
            'attrs': attrs,
            'data': data,
        }

    def to_v1(self, v2_annotation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Convert V2 segmentation to V1

        Args:
            v2_annotation: V2 annotation object

        Returns:
            (V1 annotation, V1 annotationData) tuple
        """
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])
        data = v2_annotation.get('data', [])

        # Build V1 classification
        classification: dict[str, Any] = {'class': classification_str}

        # Restore properties from attrs
        for attr in attrs:
            name = attr.get('name', '')
            value = attr.get('value')

            if not name.startswith(self._INTERNAL_ATTR_PREFIX):
                classification[name] = value

        # V1 annotation (meta info)
        v1_annotation: dict[str, Any] = {
            'id': annotation_id,
            'tool': self.tool_name,
            'classification': classification,
        }

        # V1 annotationData (coordinate info) - process based on data type
        v1_data: dict[str, Any] = {'id': annotation_id}

        if isinstance(data, list):
            # Image segmentation
            v1_data['pixel_indices'] = data
        elif isinstance(data, dict):
            # Video segmentation
            v1_data['section'] = {
                'startFrame': data.get('startFrame', 0),
                'endFrame': data.get('endFrame', 0),
            }
        else:
            # Default
            v1_data['pixel_indices'] = []

        return v1_annotation, v1_data
