---
id: datasets
title: Dataset Formats & Converters
sidebar_position: 4
---

# Dataset Formats & Converters

Pydantic models for dataset formats and bidirectional converters between Datamaker and external formats.

## Overview

The dataset annotation models and converters are now organized as follows:

- **Annotation Models**: `synapse_sdk.utils.annotation_models` - Pydantic models for all formats
- **Converters**: `synapse_sdk.utils.converters` - Bidirectional conversion between formats

- **Format models**: Pydantic models for Datamaker (v1/v2), YOLO, and other formats
- **Converters**: Bidirectional conversion between Datamaker and external formats

```python
# Annotation models
from synapse_sdk.utils.annotation_models import (
    DMVersion,
    DMDataset,
    DMImageItem,
    YOLODataset,
    YOLOImage,
    COCODataset,
    PascalAnnotation,
)

# Converters
from synapse_sdk.utils.converters import (
    DatasetFormat,
    FromDMToYOLOConverter,
    YOLOToDMConverter,
    FromDMToCOCOConverter,
    FromDMToPascalConverter,
    get_converter,
)
```

## Dataset Formats

### DatasetFormat Enum

```python
from synapse_sdk.utils.converters import DatasetFormat

DatasetFormat.DM_V1    # Datamaker v1 format
DatasetFormat.DM_V2    # Datamaker v2 format (default)
DatasetFormat.YOLO     # YOLO format
DatasetFormat.COCO     # COCO format
DatasetFormat.PASCAL   # Pascal VOC format
```

### DMVersion Enum

```python
from synapse_sdk.utils.annotation_models import DMVersion

DMVersion.V1  # Datamaker schema v1
DMVersion.V2  # Datamaker schema v2 (current)
```

## Converting Between Formats

### DM to YOLO

```python
from synapse_sdk.utils.converters import FromDMToYOLOConverter, DMVersion

# Convert categorized dataset (train/valid/test splits)
converter = FromDMToYOLOConverter(
    root_dir='/data/dm_dataset',
    is_categorized=True,
    dm_version=DMVersion.V2,
)

# Run conversion
result = converter.convert()

# Save to output directory
converter.save_to_folder('/data/yolo_output')
```

**Source structure (categorized):**

```
dm_dataset/
├── train/
│   ├── json/
│   │   └── *.json
│   └── original_files/
│       └── *.jpg
├── valid/
│   ├── json/
│   └── original_files/
└── test/
    ├── json/
    └── original_files/
```

**Output structure:**

```
yolo_output/
├── data.yaml
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

### YOLO to DM

```python
from synapse_sdk.utils.converters import YOLOToDMConverter, DMVersion

converter = YOLOToDMConverter(
    root_dir='/data/yolo_dataset',
    is_categorized=True,
    dm_version=DMVersion.V2,
)

result = converter.convert()
converter.save_to_folder('/data/dm_output')
```

### Using get_converter Factory

```python
from synapse_sdk.utils.converters import get_converter, DatasetFormat

# Get appropriate converter
converter = get_converter(
    source_format=DatasetFormat.DM_V2,
    target_format=DatasetFormat.YOLO,
    root_dir='/data/source',
    is_categorized=True,
)

converter.convert()
converter.save_to_folder('/data/output')
```

## Datamaker Format Models

### DMv2 Models (Current)

```python
from synapse_sdk.utils.annotation_models import (
    DMDataset,          # Alias for DMv2Dataset
    DMImageItem,        # Alias for DMv2ImageItem
    DMBoundingBox,
    DMPolygon,
    DMKeypoint,
    DMPolyline,
    DMRelation,
    DMGroup,
    DMAttribute,
)
```

#### DMDataset Structure

```python
from synapse_sdk.utils.annotation_models import DMDataset

# Load from JSON
dataset = DMDataset.model_validate(json_data)

# Access properties
print(dataset.version)      # "2.0"
print(dataset.item.name)    # Image filename
print(dataset.item.width)   # Image width
print(dataset.item.height)  # Image height

# Access annotations
for annotation in dataset.annotations:
    print(annotation.category)  # e.g., "object_detection"
    print(annotation.data)      # Annotation-specific data
```

#### Annotation Types

```python
from synapse_sdk.utils.annotation_models import (
    DMBoundingBox,
    DMPolygon,
    DMKeypoint,
)

# Bounding box
bbox = DMBoundingBox(
    x=100,
    y=100,
    width=200,
    height=150,
    label="car",
)

# Polygon
polygon = DMPolygon(
    points=[[100, 100], [200, 100], [200, 200], [100, 200]],
    label="building",
)

# Keypoint
keypoint = DMKeypoint(
    x=150,
    y=150,
    label="nose",
    visible=True,
)
```

### DMv1 Models (Legacy)

```python
from synapse_sdk.utils.annotation_models import (
    DMv1Dataset,
    DMv1AnnotationBase,
    DMv1Classification,
)
```

## YOLO Format Models

```python
from synapse_sdk.utils.annotation_models import (
    YOLODataset,
    YOLODatasetConfig,
    YOLOImage,
    YOLOAnnotation,
)
```

### YOLODatasetConfig

```python
from synapse_sdk.utils.annotation_models import YOLODatasetConfig

config = YOLODatasetConfig(
    path='/data/yolo_dataset',
    train='train/images',
    val='valid/images',
    test='test/images',
    names=['person', 'car', 'bicycle'],
)

# Save to data.yaml
config.save('/data/yolo_dataset/data.yaml')
```

### YOLOAnnotation

```python
from synapse_sdk.utils.annotation_models import YOLOAnnotation

# Standard YOLO format: class_id x_center y_center width height (normalized)
annotation = YOLOAnnotation(
    class_id=0,
    x_center=0.5,
    y_center=0.5,
    width=0.3,
    height=0.2,
)

# Convert to YOLO line format
line = annotation.to_line()  # "0 0.5 0.5 0.3 0.2"
```

## BaseConverter Class

All converters extend `BaseConverter` with common functionality.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `root_dir` | `Path` | Root directory containing source data |
| `is_categorized` | `bool` | Whether dataset has train/valid/test splits |
| `is_single_conversion` | `bool` | Whether converting single files |
| `converted_data` | `Any` | Holds converted data after `convert()` |

### Methods

#### convert()

Convert data in-memory.

```python
result = converter.convert()
```

#### save_to_folder()

Save converted data to output directory.

```python
converter.save_to_folder('/output/path')
```

#### convert_single_file()

Convert a single data object (requires `is_single_conversion=True`).

```python
converter = FromDMToYOLOConverter(is_single_conversion=True)
result = converter.convert_single_file(dm_json, image_file)
```

### Utility Methods

```python
# Ensure directory exists
path = converter.ensure_dir('/some/path')

# Get image dimensions
width, height = converter.get_image_size('/path/to/image.jpg')

# Find image for label file
image_path = converter.find_image_for_label('image001', image_dir)
```

## Pipeline Integration

Use with `DatasetAction` for automated workflows:

```python
from synapse_sdk.plugins.actions import DatasetAction, DatasetParams
from synapse_sdk.plugins.pipelines import ActionPipeline

# Pipeline: Download -> Convert -> Train
pipeline = ActionPipeline([
    DatasetAction,    # Download dataset
    DatasetAction,    # Convert to YOLO
    TrainAction,      # Train model
])
```

## Supported Formats

| Source | Target | Converter Class | Status |
|--------|--------|-----------------|--------|
| DM v1/v2 | YOLO | `FromDMToYOLOConverter` | Stable |
| YOLO | DM v1/v2 | `YOLOToDMConverter` | Stable |
| DM v1/v2 | COCO | `FromDMToCOCOConverter` | Stable |
| COCO | DM v1/v2 | `COCOToDMConverter` | Stable |
| DM v1/v2 | Pascal VOC | `FromDMToPascalConverter` | Stable |
| Pascal VOC | DM v1/v2 | `PascalToDMConverter` | Stable |

> **Note**: All converters now return Pydantic models for type safety. See [MIGRATION-DATASETS.md](../../../MIGRATION-DATASETS.md) for migration guide.

## Related

- [Plugin Utilities](./utils.md) - Configuration utilities
- [Plugin Models](./models.md) - Runtime context
- [Dataset Actions](../../plugins/action-types/dataset-actions.md) - Dataset download and conversion actions
