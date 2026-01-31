# Dataset Converters

Convert between different annotation formats for computer vision datasets.

## Overview

This module provides converters for transforming annotations between various formats:

- **DM (DataMaker)** ↔ COCO, Pascal VOC, YOLO
- **COCO** ↔ DM
- **Pascal VOC** ↔ DM
- **YOLO** ↔ DM
- **DM v1** ↔ DM v2

All converters support both single-file and batch conversion modes.

## Quick Start

### COCO ↔ DM

```python
from synapse_sdk.utils.converters import FromDMToCOCOConverter, COCOToDMConverter

# Convert DM to COCO
converter = FromDMToCOCOConverter(
    root_dir="./dm_dataset",
    is_categorized=True  # Has train/valid/test splits
)
coco_dataset = converter.convert()  # Returns COCODataset model

# Save to folder
converter.save_to_folder("./coco_output")

# Convert COCO to DM
converter = COCOToDMConverter(
    root_dir="./coco_dataset",
    is_categorized=True
)
dm_data = converter.convert()  # Returns dict mapping filenames to (dm_json, img_path)
converter.save_to_folder("./dm_output")
```

### Pascal VOC ↔ DM

```python
from synapse_sdk.utils.converters import FromDMToPascalConverter, PascalToDMConverter

# Convert DM to Pascal VOC
converter = FromDMToPascalConverter(root_dir="./dm_dataset")
pascal_data = converter.convert()  # Returns list of (PascalAnnotation, xml_filename, img_src, img_name)
converter.save_to_folder("./pascal_output")

# Convert Pascal VOC to DM
converter = PascalToDMConverter(root_dir="./pascal_dataset")
dm_data = converter.convert()
converter.save_to_folder("./dm_output")
```

### YOLO ↔ DM

```python
from synapse_sdk.utils.converters import FromDMToYOLOConverter, YOLOToDMConverter

# Convert DM to YOLO
converter = FromDMToYOLOConverter(root_dir="./dm_dataset")
yolo_data = converter.convert()
converter.save_to_folder("./yolo_output")  # Creates dataset.yaml

# Convert YOLO to DM
converter = YOLOToDMConverter(root_dir="./yolo_dataset")
dm_data = converter.convert()
converter.save_to_folder("./dm_output")
```

### DM v1 ↔ DM v2

```python
from synapse_sdk.utils.converters.dm import DMv1ToV2Converter, DMv2ToV1Converter

# Convert v1 to v2
converter = DMv1ToV2Converter()
v2_data = converter.convert(v1_data)

# Convert v2 to v1
converter = DMv2ToV1Converter()
v1_data = converter.convert(v2_data)
```

## Dataset Structure

### Expected Directory Structure

#### DM Format

```
dm_dataset/
├── json/
│   ├── image1.json
│   └── image2.json
└── original_files/
    ├── image1.jpg
    └── image2.jpg
```

Or with splits:

```
dm_dataset/
├── train/
│   ├── json/
│   └── original_files/
├── valid/
│   ├── json/
│   └── original_files/
└── test/           # Optional
    ├── json/
    └── original_files/
```

#### COCO Format

```
coco_dataset/
├── annotations.json
├── image1.jpg
└── image2.jpg
```

Or with splits:

```
coco_dataset/
├── train/
│   ├── annotations.json
│   └── images...
├── valid/
│   ├── annotations.json
│   └── images...
└── test/           # Optional
    ├── annotations.json
    └── images...
```

#### Pascal VOC Format

```
pascal_dataset/
├── Annotations/
│   ├── image1.xml
│   └── image2.xml
└── JPEGImages/     # or Images/
    ├── image1.jpg
    └── image2.jpg
```

#### YOLO Format

```
yolo_dataset/
├── dataset.yaml
├── images/
│   ├── image1.jpg
│   └── image2.jpg
└── labels/
    ├── image1.txt
    └── image2.txt
```

Or with splits:

```
yolo_dataset/
├── dataset.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/           # Optional
    ├── images/
    └── labels/
```

## Features

### Batch Conversion

Convert entire datasets at once:

```python
from synapse_sdk.utils.converters import FromDMToCOCOConverter

converter = FromDMToCOCOConverter(
    root_dir="./dm_dataset",
    is_categorized=True
)

# Convert all splits
result = converter.convert()
# Returns: {'train': COCODataset, 'valid': COCODataset, 'test': COCODataset}

# Save to output directory
converter.save_to_folder("./coco_output")
```

### Single File Conversion

Convert individual files without filesystem operations:

```python
from synapse_sdk.utils.converters import COCOToDMConverter

converter = COCOToDMConverter(is_single_conversion=True)

with open("annotations.json", "r") as f:
    coco_data = json.load(f)

with open("image.jpg", "rb") as img_file:
    result = converter.convert_single_file(
        data=coco_data,
        original_file=img_file,
        original_image_name="image.jpg"
    )

# Returns: {'dm_json': {...}, 'image_path': '...', 'image_name': '...'}
```

### Pydantic Model Support

Converters work with Pydantic models for type safety:

```python
from synapse_sdk.utils.converters import FromDMToCOCOConverter
from synapse_sdk.utils.annotation_models.coco import COCODataset

converter = FromDMToCOCOConverter(root_dir="./dm_dataset")
coco_dataset = converter.convert()  # Returns COCODataset (Pydantic model)

# Type-safe access
for image in coco_dataset.images:
    print(f"Image: {image.file_name} ({image.width}x{image.height})")

# Serialize to JSON
json_str = coco_dataset.to_json(indent=2)
coco_dataset.to_file("output.json")
```

### Format Support

| Feature | DM | COCO | Pascal VOC | YOLO |
|---------|----|----|-----------|------|
| Bounding Boxes | ✓ | ✓ | ✓ | ✓ |
| Polygons | ✓ | ✓ | ✗ | ✗ |
| Keypoints | ✓ | ✓ | ✗ | ✓ |
| Segmentation | ✓ | ✓ | Flag only | ✗ |
| Relations | ✓ | ✗ | ✗ | ✗ |
| Groups | ✓ | ✗ | ✗ | ✗ |
| Attributes | ✓ | ✗ | ✗ | ✗ |
| 3D Data | ✓ | ✗ | ✗ | ✗ |

## Advanced Usage

### Custom Info and Licenses (COCO)

```python
from synapse_sdk.utils.converters import FromDMToCOCOConverter
from synapse_sdk.utils.annotation_models.coco import COCOInfo, COCOLicense

info = COCOInfo(
    description="My Dataset",
    version="1.0",
    year=2024,
    contributor="My Team",
    date_created="2024-01-01"
)

licenses = [
    COCOLicense(id=1, name="CC BY 4.0", url="https://creativecommons.org/licenses/by/4.0/")
]

converter = FromDMToCOCOConverter(
    root_dir="./dm_dataset",
    info=info,
    licenses=licenses
)
```

### Progress Tracking

Converters use tqdm for progress bars:

```python
from synapse_sdk.utils.converters import FromDMToCOCOConverter

converter = FromDMToCOCOConverter(root_dir="./dm_dataset")
result = converter.convert()  # Shows progress bar
```

### Error Handling

Converters handle errors gracefully:

```python
from synapse_sdk.utils.converters import COCOToDMConverter

converter = COCOToDMConverter(root_dir="./coco_dataset")

try:
    result = converter.convert()
except FileNotFoundError as e:
    print(f"Missing file: {e}")
except ValueError as e:
    print(f"Invalid data: {e}")
```

## Module Structure

```
converters/
├── __init__.py          # Main exports
├── base.py              # Base converter classes
├── coco/
│   ├── from_dm.py       # DM → COCO
│   └── to_dm.py         # COCO → DM
├── pascal/
│   ├── from_dm.py       # DM → Pascal VOC
│   └── to_dm.py         # Pascal VOC → DM
├── yolo/
│   ├── from_dm.py       # DM → YOLO
│   └── to_dm.py         # YOLO → DM
└── dm/
    ├── v1_to_v2.py      # DM v1 → v2
    └── v2_to_v1.py      # DM v2 → v1
```

## Converter Classes

### From DM Converters
- `FromDMToCOCOConverter`: Convert DM to COCO format
- `FromDMToPascalConverter`: Convert DM to Pascal VOC format
- `FromDMToYOLOConverter`: Convert DM to YOLO format

### To DM Converters
- `COCOToDMConverter`: Convert COCO to DM format
- `PascalToDMConverter`: Convert Pascal VOC to DM format
- `YOLOToDMConverter`: Convert YOLO to DM format

### DM Internal Converters
- `DMv1ToV2Converter`: Convert DM v1 to v2 format
- `DMv2ToV1Converter`: Convert DM v2 to v1 format

## Migration

If you're migrating from the old `synapse_sdk.plugins.datasets` module:

```python
# Old (no longer works)
from synapse_sdk.plugins.datasets import FromDMToCOCOConverter

# New (correct)
from synapse_sdk.utils.converters import FromDMToCOCOConverter
```

See [MIGRATION-DATASETS.md](../../../MIGRATION-DATASETS.md) for full migration guide.

## Important Changes

### Converter Return Types

Converters now return Pydantic models instead of raw dictionaries:

```python
# COCO converter
from synapse_sdk.utils.converters import FromDMToCOCOConverter

converter = FromDMToCOCOConverter(root_dir="./data")
result = converter.convert()
# Old: result was dict
# New: result is COCODataset (Pydantic model)

# You can still convert to dict if needed:
result_dict = result.to_dict()
result_json = result.to_json()
```

```python
# Pascal VOC converter
from synapse_sdk.utils.converters import FromDMToPascalConverter

converter = FromDMToPascalConverter(root_dir="./data")
result = converter.convert()
# Old: result was list of (xml_tree, filename, img_src, img_name)
# New: result is list of (PascalAnnotation, filename, img_src, img_name)

# You can convert to XML if needed:
for pascal_annotation, xml_filename, img_src, img_name in result:
    xml_content = pascal_annotation.to_xml()
```

## Performance

Converters are optimized for:
- Large datasets (thousands of images)
- Memory efficiency (streaming processing)
- Fast I/O (batch operations)

Typical performance:
- 1000 images: ~5-10 seconds
- 10000 images: ~50-100 seconds

## Related Modules

- [annotation_models](../annotation_models/): Annotation format models
- [plugins.datasets](../../plugins/datasets/): Dataset handling plugins

## API Reference

For detailed API documentation, see the docstrings in each converter file or visit the [API docs](../../../docs/docs/api/).

## Examples

See the [examples directory](../../../examples/converters/) for complete working examples.

## Testing

Run converter tests:

```bash
# All converter tests
pytest tests/utils/converters/

# Specific format
pytest tests/utils/converters/test_coco_from_dm.py
pytest tests/utils/converters/test_pascal_to_dm.py
pytest tests/utils/converters/test_yolo_from_dm.py

# DM version conversion
pytest tests/utils/converters/dm/
```
