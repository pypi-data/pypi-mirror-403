"""
Bounding Box Tool Processor

Created: 2025-12-11

Conversion Rules (see data-model.md 4.1):
V1 → V2:
  - coordinate.{x, y, width, height} → data[x, y, width, height]
  - coordinate.rotation → attrs[{name:"rotation", value}]
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]

V2 → V1:
  - data[0,1,2,3] → coordinate.{x, y, width, height}
  - attrs.rotation → coordinate.rotation
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value} (excluding special attrs)
"""

from typing import Any


class BoundingBoxProcessor:
    """Bounding Box Tool Processor

    V1 coordinate: {x, y, width, height, rotation?}
    V2 data: [x, y, width, height]
    """

    tool_name = 'bounding_box'

    # V1 meta fields (not stored in attrs)
    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}

    # Fields to restore from V2 attrs to coordinate
    _COORDINATE_ATTRS = {'rotation'}

    # Special attrs not restored to V1 classification (_ prefix)
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 bounding box to V2

        Args:
            v1_annotation: V1 annotations[] item
            v1_data: V1 annotationsData[] item (same ID)

        Returns:
            V2 format bounding box annotation
        """
        coordinate = v1_data.get('coordinate', {})
        classification_obj = v1_annotation.get('classification') or {}

        # V2 data: [x, y, width, height]
        data = [
            coordinate.get('x', 0),
            coordinate.get('y', 0),
            coordinate.get('width', 0),
            coordinate.get('height', 0),
        ]

        # Build V2 attrs
        attrs: list[dict[str, Any]] = []

        # Add rotation to attrs
        if 'rotation' in coordinate:
            attrs.append({'name': 'rotation', 'value': coordinate['rotation']})

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
        """Convert V2 bounding box to V1

        Args:
            v2_annotation: V2 annotation object

        Returns:
            (V1 annotation, V1 annotationData) tuple
        """
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])
        data = v2_annotation.get('data', [0, 0, 0, 0])

        # Build V1 coordinate
        coordinate: dict[str, Any] = {
            'x': data[0] if len(data) > 0 else 0,
            'y': data[1] if len(data) > 1 else 0,
            'width': data[2] if len(data) > 2 else 0,
            'height': data[3] if len(data) > 3 else 0,
        }

        # Build V1 classification
        classification: dict[str, Any] = {'class': classification_str}

        # Restore properties from attrs
        for attr in attrs:
            name = attr.get('name', '')
            value = attr.get('value')

            if name in self._COORDINATE_ATTRS:
                # Add rotation etc. to coordinate
                coordinate[name] = value
            elif not name.startswith(self._INTERNAL_ATTR_PREFIX):
                # Add non-internal attrs to classification
                classification[name] = value

        # V1 annotation (meta info)
        v1_annotation: dict[str, Any] = {
            'id': annotation_id,
            'tool': self.tool_name,
            'classification': classification,
        }

        # V1 annotationData (coordinate info)
        v1_data: dict[str, Any] = {
            'id': annotation_id,
            'coordinate': coordinate,
        }

        return v1_annotation, v1_data
