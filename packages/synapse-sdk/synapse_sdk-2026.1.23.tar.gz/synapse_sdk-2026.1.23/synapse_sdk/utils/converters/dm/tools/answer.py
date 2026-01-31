"""
Answer Tool Processor

Created: 2025-12-12

Conversion Rules (see data-model.md 9.11):
V1 → V2:
  - output → data.output
  - model, displayName, generatedBy, promptAnnotationId → preserved in data
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]

V2 → V1:
  - data.output → output
  - Other fields from data → preserved in annotationsData
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value}
"""

from typing import Any


class AnswerProcessor:
    """Answer Tool Processor

    V1 annotationsData: {id, tool, model, output: [{type, value, primaryKey, changeHistory}],
                         displayName, generatedBy, promptAnnotationId}
    V2 data: {output: [...], model, displayName, generatedBy, promptAnnotationId, timestamp?}

    Answer annotation data conversion.
    """

    tool_name = 'answer'

    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}
    _INTERNAL_ATTR_PREFIX = '_'
    # Fields to copy from annotationsData to V2 data
    _DATA_FIELDS = {'output', 'model', 'displayName', 'generatedBy', 'promptAnnotationId', 'timestamp'}

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 answer to V2"""
        classification_obj = v1_annotation.get('classification') or {}

        # Build V2 data (output and other fields)
        data: dict[str, Any] = {}
        for key in self._DATA_FIELDS:
            if key in v1_data:
                data[key] = v1_data[key]

        # Build V2 attrs (all classification properties excluding class)
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
        """Convert V2 answer to V1"""
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

        # Build V1 annotationsData
        v1_data: dict[str, Any] = {
            'id': annotation_id,
            'tool': self.tool_name,
        }

        # Copy fields from data
        for key in self._DATA_FIELDS:
            if key in data:
                v1_data[key] = data[key]

        return v1_annotation, v1_data
