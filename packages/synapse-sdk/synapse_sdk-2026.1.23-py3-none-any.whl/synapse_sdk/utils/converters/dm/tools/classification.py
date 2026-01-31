"""
Classification Tool Processor

Created: 2025-12-12

Conversion Rules (see data-model.md 9.8):
V1 → V2:
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]
  - annotationsData contains only id

V2 → V1:
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value}
  - data is empty object {}
"""

from typing import Any


class ClassificationProcessor:
    """Classification Tool Processor

    V1: All properties in annotations, only id in annotationsData
    V2: data is empty object, all properties stored in attrs
    """

    tool_name = 'classification'

    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 classification to V2"""
        classification_obj = v1_annotation.get('classification') or {}

        # Build V2 attrs (all properties excluding class)
        attrs: list[dict[str, Any]] = []
        for key, value in classification_obj.items():
            if key != 'class':
                attrs.append({'name': key, 'value': value})

        return {
            'id': v1_annotation.get('id', ''),
            'classification': classification_obj.get('class', ''),
            'attrs': attrs,
            'data': {},  # Empty object
        }

    def to_v1(self, v2_annotation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        """Convert V2 classification to V1"""
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])

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

        # annotationsData contains only id
        v1_data: dict[str, Any] = {
            'id': annotation_id,
        }

        return v1_annotation, v1_data
