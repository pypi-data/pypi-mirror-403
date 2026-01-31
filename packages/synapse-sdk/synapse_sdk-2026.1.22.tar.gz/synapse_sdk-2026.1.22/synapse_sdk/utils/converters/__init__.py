"""Dataset format converters.

Provides converters between Datamaker format and common dataset formats (YOLO, COCO, Pascal VOC).

Structure:
- base.py: BaseConverter, FromDMConverter, ToDMConverter, DatasetFormat
- coco/: COCO format converters (DM <-> COCO)
- pascal/: Pascal VOC format converters (DM <-> Pascal)
- yolo/: YOLO format converters (DM <-> YOLO)
- dm/: DM utilities and annotation tools
- dm_legacy/: Legacy DM v1 converters

Example:
    >>> from synapse_sdk.utils.converters import get_converter
    >>>
    >>> # Convert DM to YOLO
    >>> converter = get_converter('dm_v2', 'yolo', root_dir='/data/dm_dataset')
    >>> converter.convert()
    >>> converter.save_to_folder('/data/yolo_output')
    >>>
    >>> # Convert YOLO to DM
    >>> converter = get_converter('yolo', 'dm_v2', root_dir='/data/yolo_dataset')
    >>> converter.convert()
    >>> converter.save_to_folder('/data/dm_output')
"""

from __future__ import annotations

from synapse_sdk.utils.converters.base import (
    BaseConverter,
    DatasetFormat,
    FromDMConverter,
    ToDMConverter,
)
from synapse_sdk.utils.converters.coco import (
    COCOToDMConverter,
    FromDMToCOCOConverter,
)
from synapse_sdk.utils.converters.imagefolder import (
    FromDMToImageFolderConverter,
)
from synapse_sdk.utils.converters.pascal import (
    FromDMToPascalConverter,
    PascalToDMConverter,
)
from synapse_sdk.utils.converters.yolo import (
    FromDMToYOLOConverter,
    YOLOToDMConverter,
)


def get_converter(
    source: DatasetFormat | str,
    target: DatasetFormat | str,
    **kwargs,
) -> BaseConverter:
    """Get converter for source -> target format conversion.

    Args:
        source: Source dataset format ('dm_v1', 'dm_v2', 'yolo', 'coco', 'pascal').
        target: Target dataset format ('dm_v1', 'dm_v2', 'yolo', 'coco', 'pascal').
        **kwargs: Additional arguments passed to converter constructor:
            - root_dir: Source dataset root directory
            - is_categorized: Whether dataset has train/valid/test splits
            - dm_version: DMVersion for DM converters (default: V2)

    Returns:
        Converter instance for the specified format pair.

    Raises:
        ValueError: If no converter exists for the format pair.

    Example:
        >>> # DM to YOLO with splits
        >>> converter = get_converter('dm_v2', 'yolo',
        ...                          root_dir='/data/dm',
        ...                          is_categorized=True)
        >>> converter.convert()
        >>> converter.save_to_folder('/data/yolo')
        >>>
        >>> # YOLO to DM without splits
        >>> converter = get_converter('yolo', 'dm_v2',
        ...                          root_dir='/data/yolo',
        ...                          is_categorized=False)
        >>> result = converter.convert()
        >>> converter.save_to_folder('/data/dm')
    """
    source = DatasetFormat(source)
    target = DatasetFormat(target)

    # Map format pairs to converter classes
    converters: dict[tuple[DatasetFormat, DatasetFormat], type[BaseConverter]] = {
        # DM -> YOLO
        (DatasetFormat.DM_V1, DatasetFormat.YOLO): FromDMToYOLOConverter,
        (DatasetFormat.DM_V2, DatasetFormat.YOLO): FromDMToYOLOConverter,
        # YOLO -> DM
        (DatasetFormat.YOLO, DatasetFormat.DM_V1): YOLOToDMConverter,
        (DatasetFormat.YOLO, DatasetFormat.DM_V2): YOLOToDMConverter,
        # DM -> COCO
        (DatasetFormat.DM_V1, DatasetFormat.COCO): FromDMToCOCOConverter,
        (DatasetFormat.DM_V2, DatasetFormat.COCO): FromDMToCOCOConverter,
        # COCO -> DM
        (DatasetFormat.COCO, DatasetFormat.DM_V1): COCOToDMConverter,
        (DatasetFormat.COCO, DatasetFormat.DM_V2): COCOToDMConverter,
        # DM -> Pascal
        (DatasetFormat.DM_V1, DatasetFormat.PASCAL): FromDMToPascalConverter,
        (DatasetFormat.DM_V2, DatasetFormat.PASCAL): FromDMToPascalConverter,
        # Pascal -> DM
        (DatasetFormat.PASCAL, DatasetFormat.DM_V1): PascalToDMConverter,
        (DatasetFormat.PASCAL, DatasetFormat.DM_V2): PascalToDMConverter,
        # DM -> ImageFolder
        (DatasetFormat.DM_V1, DatasetFormat.IMAGEFOLDER): FromDMToImageFolderConverter,
        (DatasetFormat.DM_V2, DatasetFormat.IMAGEFOLDER): FromDMToImageFolderConverter,
    }

    converter_cls = converters.get((source, target))
    if converter_cls is None:
        available_pairs = [f'{s.value} -> {t.value}' for s, t in converters.keys()]
        raise ValueError(
            f'No converter available for {source.value} -> {target.value}. '
            f'Available pairs: {", ".join(available_pairs)}'
        )

    return converter_cls(**kwargs)


__all__ = [
    # Base classes
    'BaseConverter',
    'DatasetFormat',
    'FromDMConverter',
    'ToDMConverter',
    # COCO converters
    'FromDMToCOCOConverter',
    'COCOToDMConverter',
    # ImageFolder converters
    'FromDMToImageFolderConverter',
    # Pascal converters
    'FromDMToPascalConverter',
    'PascalToDMConverter',
    # YOLO converters
    'FromDMToYOLOConverter',
    'YOLOToDMConverter',
    # Factory function
    'get_converter',
]
