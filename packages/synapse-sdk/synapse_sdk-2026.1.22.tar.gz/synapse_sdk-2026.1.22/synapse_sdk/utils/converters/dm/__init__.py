"""
DM Schema V1/V2 Bidirectional Converter

"""

from typing import Any

from .types import (
    AnnotationMeta,
    V2AnnotationData,
    V2ConversionResult,
)


def convert_v1_to_v2(v1_data: dict[str, Any]) -> V2ConversionResult:
    """Convert DM Schema V1 data to V2 (separated result)

    Args:
        v1_data: DM Schema V1 format data

    Returns:
        V2ConversionResult: Separated conversion result
            - annotation_data: V2 common annotation structure
            - annotation_meta: Preserved V1 top-level structure
    """
    from .from_v1 import DMV1ToV2Converter

    converter = DMV1ToV2Converter()
    return converter.convert(v1_data)


def convert_v2_to_v1(
    v2_data: V2ConversionResult | dict[str, Any],
    annotation_meta: AnnotationMeta | None = None,
) -> dict[str, Any]:
    """Convert DM Schema V2 data to V1

    Args:
        v2_data: DM Schema V2 format data
        annotation_meta: Optional V1 top-level structure passed separately

    Returns:
        DM Schema V1 format data
    """
    from .to_v1 import DMV2ToV1Converter

    converter = DMV2ToV1Converter()
    return converter.convert(v2_data, annotation_meta)


__all__ = [
    'convert_v1_to_v2',
    'convert_v2_to_v1',
    'V2ConversionResult',
    'V2AnnotationData',
    'AnnotationMeta',
]
