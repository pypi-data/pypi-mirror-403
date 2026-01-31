---
id: index
title: Converters
sidebar_position: 1
---

# Converters

The Synapse SDK provides comprehensive data format conversion utilities for computer vision datasets. These converters enable seamless transformation between different annotation formats commonly used in machine learning workflows.

## Overview

The converter system supports bidirectional conversion between:

- **DM Format** - Synapse Data Manager's native annotation format (supports v1 and v2)
- **YOLO Format** - You Only Look Once text-based format
- **COCO Format** - Microsoft Common Objects in Context format (Coming Soon)
- **Pascal VOC Format** - Visual Object Classes XML format (Coming Soon)

All converters support both categorized datasets (with train/valid/test splits) and non-categorized datasets. Additionally, all converters now support single file conversion mode for processing individual files.

## Supported Annotation Types

| Annotation Type | DM | YOLO | COCO | Pascal VOC |
|----------------|----|----|-----------|------|
| Bounding Boxes | ✅ | ✅ | 🔜 | 🔜 |
| Polygons | ✅ | ✅ | 🔜 | 🔜 |
| Segmentation | ✅ | - | 🔜 | 🔜 |
| Keypoints | ✅ | ✅ | 🔜 | 🔜 |
| Classifications | ✅ | - | 🔜 | 🔜 |

- ✅ = Supported
- 🔜 = Coming Soon
- `-` = Not applicable for this format

## YOLO Converters

### FromDMToYOLOConverter

Converts DM format annotations to YOLO format with comprehensive annotation support.

**Features:**
- Supports bounding boxes, polygons, and keypoints
- Creates `dataset.yaml` configuration file
- Normalizes coordinates automatically
- Handles keypoint visibility flags
- Supports both DMv1 and DMv2 schemas

**Usage:**
```python
from synapse_sdk.utils.converters import FromDMToYOLOConverter
from synapse_sdk.utils.annotation_models (formats module removed).dm import DMVersion

# Convert with all annotation types
converter = FromDMToYOLOConverter(
    root_dir='/path/to/dm/dataset',
    is_categorized=True,
    dm_version=DMVersion.V2
)
converted_data = converter.convert()
converter.save_to_folder('/output/yolo/dataset')

# Convert non-categorized dataset
converter = FromDMToYOLOConverter(
    root_dir='/path/to/dm/dataset',
    is_categorized=False,
    dm_version=DMVersion.V2
)
converted_data = converter.convert()
converter.save_to_folder('/output/yolo/dataset')

# Single file conversion
converter = FromDMToYOLOConverter(is_single_conversion=True)
with open('data.json') as f:
    dm_data = json.load(f)
with open('image.jpg', 'rb') as img_file:
    yolo_labels = converter.convert_single_file(dm_data, img_file)
```

**Input Structure (Categorized):**
```
dm_dataset/
├── train/
│   ├── json/
│   │   ├── image1.json
│   │   └── image2.json
│   └── original_files/
│       ├── image1.jpg
│       └── image2.jpg
├── valid/
│   ├── json/
│   └── original_files/
└── test/ (optional)
    ├── json/
    └── original_files/
```

**Output Structure:**
```
yolo_dataset/
├── train/
│   ├── images/
│   │   ├── image1.jpg
│   │   └── image2.jpg
│   └── labels/
│       ├── image1.txt
│       └── image2.txt
├── valid/
├── test/ (if present)
├── dataset.yaml
└── classes.txt
```

**YOLO Label Format Examples:**
```
# Bounding box: class_id center_x center_y width height
0 0.5 0.5 0.3 0.4

# Polygon: class_id x1 y1 x2 y2 x3 y3 x4 y4 ...
0 0.1 0.1 0.9 0.1 0.9 0.9 0.1 0.9

# Keypoints: class_id center_x center_y width height kp1_x kp1_y kp1_v kp2_x kp2_y kp2_v ...
0 0.5 0.5 0.3 0.4 0.45 0.3 2 0.55 0.3 2 0.5 0.7 1
```

### YOLOToDMConverter

Converts YOLO format annotations back to DM format.

**Features:**
- Intelligent parsing of different YOLO annotation types
- Requires `dataset.yaml` or `classes.txt` for class name mapping
- Handles bounding boxes, polygons, and keypoints
- Automatically detects image dimensions
- Outputs either DMv1 or DMv2 schema

**Usage:**
```python
from synapse_sdk.utils.converters import YOLOToDMConverter
from synapse_sdk.utils.annotation_models (formats module removed).dm import DMVersion

converter = YOLOToDMConverter(
    root_dir='/path/to/yolo/dataset',
    is_categorized=True,
    dm_version=DMVersion.V2
)
converted_data = converter.convert()
converter.save_to_folder('/output/dm/dataset')

# Single file conversion with explicit class names
converter = YOLOToDMConverter(
    is_single_conversion=True,
    class_names=['person', 'car', 'bicycle']
)
label_lines = ['0 0.5 0.5 0.3 0.4']
with open('image.jpg', 'rb') as img_file:
    result = converter.convert_single_file(label_lines, img_file)
```

## Pascal VOC Converters

:::info Coming Soon
Pascal VOC converters are currently under development. The following documentation describes the planned API.
:::

### FromDMToPascalConverter

Converts DM format annotations to Pascal VOC XML format.

**Planned Features:**
- Converts bounding box annotations and segmentation masks
- Creates standard Pascal VOC directory structure
- Generates `classes.txt` file automatically
- Supports both categorized and non-categorized datasets

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import FromDMToPascalConverter

# Convert categorized dataset
converter = FromDMToPascalConverter(
    root_dir='/path/to/dm/dataset',
    is_categorized=True
)
converted_data = converter.convert()
converter.save_to_folder('/output/pascal/dataset')
```

**Output Structure:**
```
pascal_dataset/
├── train/
│   ├── Annotations/
│   │   ├── image1.xml
│   │   └── image2.xml
│   └── Images/
│       ├── image1.jpg
│       └── image2.jpg
├── valid/
├── test/ (if present)
└── classes.txt
```

### PascalToDMConverter

Converts Pascal VOC XML annotations to DM format.

**Planned Features:**
- Parses Pascal VOC XML files
- Flexible directory naming (supports Annotations/annotations, Images/images/JPEGImages)
- Extracts bounding box annotations and segmentation information
- Maintains class information

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import PascalToDMConverter

# Convert Pascal VOC dataset
converter = PascalToDMConverter(
    root_dir='/path/to/pascal/dataset',
    is_categorized=True
)
converted_data = converter.convert()
converter.save_to_folder('/output/dm/dataset')
```

## COCO Converters

:::info Coming Soon
COCO converters are currently under development. The following documentation describes the planned API.
:::

### FromDMToCOCOConverter

Converts DM format to COCO format with full metadata support.

**Planned Features:**
- Comprehensive COCO metadata (info, licenses, categories)
- Supports bounding boxes, polygons, segmentation, and keypoints
- Dynamic category management
- Extensible for different data types

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import FromDMToCOCOConverter

# Basic conversion
converter = FromDMToCOCOConverter(
    root_dir='/path/to/dm/dataset',
    is_categorized=True
)
converted_data = converter.convert()
converter.save_to_folder('/output/coco/dataset')

# With custom metadata
info_dict = {
    "description": "My Custom Dataset",
    "version": "1.0",
    "contributor": "My Organization"
}

licenses_list = [{
    "id": 1,
    "name": "Custom License",
    "url": "https://example.com/license"
}]

converter = FromDMToCOCOConverter(
    root_dir='/path/to/dm/dataset',
    info_dict=info_dict,
    licenses_list=licenses_list,
    is_categorized=True
)
```

**Output Structure:**
```
coco_dataset/
├── train/
│   ├── annotations.json
│   ├── image1.jpg
│   └── image2.jpg
├── valid/
│   ├── annotations.json
│   └── images...
└── test/ (if present)
```

### COCOToDMConverter

Converts COCO format annotations to DM format.

**Planned Features:**
- Parses COCO JSON annotations
- Handles image datasets
- Maintains keypoint groupings through DM groups
- Supports bounding boxes and keypoints

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import COCOToDMConverter

converter = COCOToDMConverter(
    root_dir='/path/to/coco/dataset',
    is_categorized=True
)
converted_data = converter.convert()
converter.save_to_folder('/output/dm/dataset')
```

## DM Version Converter

:::info Coming Soon
DM version converters are currently under development. The following documentation describes the planned API.
:::

### DMV1ToV2Converter

Migrates legacy DM v1 datasets to the current v2 format.

**Planned Features:**
- Comprehensive migration for all annotation types
- Handles data structure changes between versions
- Supports images and videos
- Maintains annotation tool integrity

**Supported Tools:**
- Bounding boxes
- Named entities
- Classifications with attributes
- Polylines and polygons
- Keypoints
- 3D bounding boxes
- Segmentation
- Relations and groups

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import DMV1ToV2Converter

converter = DMV1ToV2Converter(
    root_dir='/path/to/dm/v1/dataset',
    is_categorized=True
)
converted_data = converter.convert()
converter.save_to_folder('/output/dm/v2/dataset')
```

### DMV2ToV1Converter

Converts DM v2 datasets back to the legacy v1 format for compatibility with older systems.

**Planned Features:**
- Reverse migration from DM v2 to v1 format
- Preserves all annotation types and metadata
- Maintains coordinate integrity across formats
- Generates appropriate v1 structure with annotations and annotationsData

**Planned Usage:**
```python
# NOTE: This API is planned but not yet implemented.
# The following shows the expected interface once available.

from synapse_sdk.utils.converters import DMV2ToV1Converter

# Load v2 data and convert to v1
with open('dm_v2_data.json', 'r') as f:
    v2_data = json.load(f)

converter = DMV2ToV1Converter(v2_data)
v1_data = converter.convert()

# Save or use the converted v1 data
with open('dm_v1_data.json', 'w') as f:
    json.dump(v1_data, f, indent=2)
```

## Common Parameters

All converters share these common parameters:

### `root_dir` (str)
Path to the root directory containing the dataset. Not required when using single file conversion mode.

### `is_categorized` (bool)
- `True`: Dataset has train/valid/test splits in separate subdirectories
- `False`: Dataset is in a single directory without splits

### `is_single_conversion` (bool)
- `True`: Enable single file conversion mode for processing individual files
- `False`: Process entire dataset directories (default behavior)

### `dm_version` (DMVersion)
Target or source DM schema version. Available values:
- `DMVersion.V1`: Legacy DM v1 format
- `DMVersion.V2`: Current DM v2 format (default)

### Common Methods

#### `convert()`
Performs in-memory conversion and returns the converted data structure.

#### `convert_single_file(data, original_file, **kwargs)`
Available when `is_single_conversion=True`. Converts a single data object and corresponding original file.

#### `save_to_folder(output_dir)`
Saves the converted data to the specified output directory, creating the appropriate file structure for the target format.

## Programmatic Converter Selection

You can use the `get_converter` factory function to select converters programmatically:

```python
from synapse_sdk.utils.converters import get_converter, DatasetFormat

# Get DM -> YOLO converter
converter = get_converter(
    source=DatasetFormat.DM_V2,
    target=DatasetFormat.YOLO,
    root_dir='/path/to/dataset',
    is_categorized=True
)

# Or use string format names
converter = get_converter(
    source='dm_v2',
    target='yolo',
    root_dir='/path/to/dataset',
    is_categorized=True
)

converter.convert()
converter.save_to_folder('/output')
```

## Error Handling

All converters include robust error handling:

- **File Validation**: Checks for required files and directories
- **Format Validation**: Validates annotation format correctness
- **Graceful Degradation**: Warns about unsupported annotations instead of failing
- **Progress Tracking**: Shows progress for large dataset conversions

## Best Practices

1. **Backup Original Data**: Always keep backups before conversion
2. **Validate Results**: Check converted annotations for accuracy
3. **Test on Small Datasets**: Test conversion on small samples first
4. **Check Requirements**: Ensure all required files (dataset.yaml, classes.txt, etc.) are present
5. **Monitor Warnings**: Pay attention to conversion warnings for data quality issues

## Examples

### Converting Between YOLO and DM

```python
from synapse_sdk.utils.converters import (
    FromDMToYOLOConverter,
    YOLOToDMConverter,
)
from synapse_sdk.utils.annotation_models (formats module removed).dm import DMVersion

# 1. Convert DM to YOLO
dm_to_yolo = FromDMToYOLOConverter(
    root_dir='/data/dm_dataset',
    is_categorized=True,
    dm_version=DMVersion.V2
)
dm_to_yolo.convert()
dm_to_yolo.save_to_folder('/data/yolo_output')

# 2. Convert YOLO back to DM
yolo_to_dm = YOLOToDMConverter(
    root_dir='/data/yolo_output',
    is_categorized=True,
    dm_version=DMVersion.V2
)
yolo_to_dm.convert()
yolo_to_dm.save_to_folder('/data/dm_roundtrip')

# Coming Soon:
# - Pascal VOC <-> DM conversion
# - COCO <-> DM conversion
# - DM v1 <-> v2 migration
```

### Single File Conversion Example

```python
import json
from synapse_sdk.utils.converters import FromDMToYOLOConverter

# Initialize converter for single file processing
converter = FromDMToYOLOConverter(is_single_conversion=True)

# Load DM format data
with open('annotation.json', 'r') as f:
    dm_data = json.load(f)

# Convert single file
with open('image.jpg', 'rb') as img_file:
    result = converter.convert_single_file(dm_data, img_file)

# result contains:
# - label_lines: YOLO format label lines
# - class_names: List of class names
# - class_map: Mapping of class name to index
print(result['label_lines'])
```

This converter system provides a complete solution for dataset format transformation, enabling seamless integration between different machine learning workflows and annotation tools.
