"""
3D Bounding Box Tool Processor

Created: 2025-12-12

Conversion Rules (see data-model.md 9.6):
V1 → V2:
  - psr {position, scale, rotation} → data {position, scale, rotation}
  - classification.class → classification
  - classification.{other} → attrs[{name, value}]

V2 → V1:
  - data {position, scale, rotation} → psr {position, scale, rotation}
  - classification → classification.class
  - attrs[{name, value}] → classification.{name: value} (excluding special attrs)
"""

from typing import Any


class BoundingBox3DProcessor:
    """3D Bounding Box Tool Processor

    V1 psr: {position, scale, rotation} each {x, y, z}
    V2 data: {position, scale, rotation} each {x, y, z}

    PSR structure is identical, only key name changes (psr → data).
    Used with pcd (point cloud) media type.
    """

    tool_name = '3d_bounding_box'

    # V1 meta fields (not stored in attrs)
    _META_FIELDS = {'isLocked', 'isVisible', 'isValid', 'isDrawCompleted', 'label', 'id', 'tool'}

    # Special attrs not restored to V1 classification (_ prefix)
    _INTERNAL_ATTR_PREFIX = '_'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        """Convert V1 3D bounding box to V2

        Args:
            v1_annotation: V1 annotations[] item
            v1_data: V1 annotationsData[] item (same ID)

        Returns:
            V2 format 3D bounding box annotation
        """
        psr = v1_data.get('psr', {})
        classification_obj = v1_annotation.get('classification') or {}

        # V2 data: copy psr structure as-is
        data = {
            'position': psr.get('position', {'x': 0, 'y': 0, 'z': 0}),
            'scale': psr.get('scale', {'x': 0, 'y': 0, 'z': 0}),
            'rotation': psr.get('rotation', {'x': 0, 'y': 0, 'z': 0}),
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
        """Convert V2 3D bounding box to V1

        Args:
            v2_annotation: V2 annotation object

        Returns:
            (V1 annotation, V1 annotationData) tuple
        """
        annotation_id = v2_annotation.get('id', '')
        classification_str = v2_annotation.get('classification', '')
        attrs = v2_annotation.get('attrs', [])
        data = v2_annotation.get('data', {})

        # Build V1 psr: copy data structure as-is
        psr: dict[str, Any] = {
            'position': data.get('position', {'x': 0, 'y': 0, 'z': 0}),
            'scale': data.get('scale', {'x': 0, 'y': 0, 'z': 0}),
            'rotation': data.get('rotation', {'x': 0, 'y': 0, 'z': 0}),
        }

        # Build V1 classification
        classification: dict[str, Any] = {'class': classification_str}

        # Restore properties from attrs
        for attr in attrs:
            name = attr.get('name', '')
            value = attr.get('value')

            if not name.startswith(self._INTERNAL_ATTR_PREFIX):
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
            'psr': psr,
        }

        return v1_annotation, v1_data
