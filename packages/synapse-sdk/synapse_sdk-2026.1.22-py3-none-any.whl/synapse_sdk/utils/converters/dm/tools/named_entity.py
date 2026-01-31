"""
Named Entity Tool Processor

Created: 2025-12-12

Conversion Rules (see data-model.md 9.5):
V1 → V2:
  - ranges, content → data {ranges, content}
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]

V2 → V1:
  - data {ranges, content} → ranges, content
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value} (excluding special attrs)
"""

from typing import Any


class NamedEntityProcessor:
    """Named Entity Tool Processor

    V1 annotationData: {ranges: [...], content: str}
    V2 data: {ranges: [...], content: str}

    Used with text media type.
    """

    tool_name = 'named_entity'

    # V1 meta fields (not stored in attrs)
    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}

    # Special attrs not restored to V1 classification (_ prefix)
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 named entity to V2

        Args:
            v1_annotation: V1 annotations[] item
            v1_data: V1 annotationsData[] item (same ID)

        Returns:
            V2 format named entity annotation
        """
        classification_obj = v1_annotation.get('classification') or {}

        # V2 data: {ranges, content}
        data = {
            'ranges': v1_data.get('ranges', []),
            'content': v1_data.get('content', ''),
        }

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
        """Convert V2 named entity to V1

        Args:
            v2_annotation: V2 annotation object

        Returns:
            (V1 annotation, V1 annotationData) tuple
        """
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])
        data = v2_annotation.get('data', {})

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

        # V1 annotationData (ranges, content)
        v1_data: dict[str, Any] = {
            'id': annotation_id,
            'ranges': data.get('ranges', []),
            'content': data.get('content', ''),
        }

        return v1_annotation, v1_data
