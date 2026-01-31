"""
DM Schema V1/V2 Converter Utility Functions

Created: 2025-12-11
"""

import random
import string
from typing import Any

from .types import MEDIA_TYPE_MAP, MEDIA_TYPE_REVERSE_MAP


def generate_random_id(length: int = 10) -> str:
    """Generate a random ID compatible with V1 format

    Args:
        length: ID length (default: 10)

    Returns:
        Random alphanumeric string

    Example:
        >>> generate_random_id()
        'Cd1qfFQFI4'
    """
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def extract_media_type_info(media_id: str) -> tuple[str, str]:
    """Extract type information from media ID

    Args:
        media_id: Media ID (e.g., 'image_1', 'video_2')

    Returns:
        (singular, plural) tuple (e.g., ('image', 'images'))

    Raises:
        ValueError: Unknown media type

    Example:
        >>> extract_media_type_info('image_1')
        ('image', 'images')
        >>> extract_media_type_info('video_2')
        ('video', 'videos')
    """
    # Extract type from media ID (e.g., 'image_1' -> 'image')
    for media_type in MEDIA_TYPE_MAP:
        if media_id.startswith(media_type):
            return media_type, MEDIA_TYPE_MAP[media_type]

    raise ValueError(f'Unknown media type: {media_id}')


def detect_file_type(data: dict[str, Any], is_v2: bool = False) -> str:
    """Auto-detect file type from data

    Args:
        data: Input data (V1 or V2)
        is_v2: Whether the format is V2

    Returns:
        Detected file type ('image', 'video', etc.)

    Raises:
        ValueError: Unable to detect file type
    """
    if is_v2:
        # Detect from V2 data (annotation_data or direct data)
        check_data = data.get('annotation_data', data)
        for plural_type in MEDIA_TYPE_REVERSE_MAP:
            if plural_type in check_data and check_data[plural_type]:
                return MEDIA_TYPE_REVERSE_MAP[plural_type]
    else:
        # Detect from V1 data (from annotations or annotationsData keys)
        for key in ['annotations', 'annotationsData']:
            if key in data and data[key]:
                # Extract type from first media ID
                first_media_id = next(iter(data[key].keys()), None)
                if first_media_id:
                    singular, _ = extract_media_type_info(first_media_id)
                    return singular

    raise ValueError('Unable to detect file type')


def get_attr_value(attrs: list[dict[str, Any]], name: str, default: Any = None) -> Any:
    """Extract value for a specific name from attrs list

    Args:
        attrs: V2 attrs list [{"name": "...", "value": ...}, ...]
        name: Attribute name to find
        default: Default value (if not found)

    Returns:
        Found value or default
    """
    for attr in attrs:
        if attr.get('name') == name:
            return attr.get('value', default)
    return default


def set_attr_value(attrs: list[dict[str, Any]], name: str, value: Any) -> list[dict[str, Any]]:
    """Add or update attribute in attrs list

    Args:
        attrs: V2 attrs list
        name: Attribute name
        value: Attribute value

    Returns:
        Updated attrs list
    """
    # Update existing attribute
    for attr in attrs:
        if attr.get('name') == name:
            attr['value'] = value
            return attrs

    # Add new attribute
    attrs.append({'name': name, 'value': value})
    return attrs


def build_v1_annotation_base(
    annotation_id: str,
    tool: str,
    classification: dict[str, Any] | None = None,
    is_locked: bool = False,
    is_visible: bool = True,
    is_valid: bool = False,
    is_draw_completed: bool = True,
    label: list[str] | None = None,
) -> dict[str, Any]:
    """Create V1 AnnotationBase object

    Args:
        annotation_id: Annotation ID
        tool: Tool code
        classification: Classification info
        is_locked: Edit lock
        is_visible: Display visibility
        is_valid: Validity
        is_draw_completed: Drawing completed
        label: Label array

    Returns:
        V1 AnnotationBase dictionary
    """
    return {
        'id': annotation_id,
        'tool': tool,
        'isLocked': is_locked,
        'isVisible': is_visible,
        'isValid': is_valid,
        'isDrawCompleted': is_draw_completed,
        'classification': classification,
        'label': label or [],
    }
