"""
3D Segmentation Tool Processor

Created: 2025-12-12

Conversion Rules (see data-model.md 9.7):
V1 → V2:
  - points [...] → data {points: [...]}
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]

V2 → V1:
  - data {points: [...]} → points [...]
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value}
"""

from typing import Any


class Segmentation3DProcessor:
    """3D Segmentation Tool Processor

    V1 annotationData: {points: list[int]}
    V2 data: {points: list[int]}

    Used with pcd media type.
    """

    tool_name = '3d_segmentation'

    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 3D segmentation to V2"""
        classification_obj = v1_annotation.get('classification') or {}

        # V2 data: {points: [...]}
        data = {
            'points': v1_data.get('points', []),
        }

        # Build V2 attrs
        attrs: list[dict[str, Any]] = []
        for key, value in classification_obj.items():
            if key != 'class':
                attrs.append({'name': key, 'value': value})

        return {
            'id': v1_annotation.get('id', ''),
            'classification': classification_obj.get('class', ''),
            'attrs': attrs,
            'data': data,
        }

    def to_v1(self, v2_annotation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Convert V2 3D segmentation to V1"""
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])
        data = v2_annotation.get('data', {})

        # Build V1 classification
        classification: dict[str, Any] = {'class': classification_str}
        for attr in attrs:
            name = attr.get('name', '')
            value = attr.get('value')
            if not name.startswith(self._INTERNAL_ATTR_PREFIX):
                classification[name] = value

        v1_annotation: dict[str, Any] = {
            'id': annotation_id,
            'tool': self.tool_name,
            'classification': classification,
        }

        v1_data: dict[str, Any] = {
            'id': annotation_id,
            'points': data.get('points', []),
        }

        return v1_annotation, v1_data
