# Annotation Models

Type-safe Pydantic models for various annotation formats used in computer vision and machine learning.

## Overview

This module provides Pydantic models for working with different annotation formats:

- **DM (DataMaker)**: Synapse's native annotation format
- **COCO**: Microsoft COCO dataset format
- **Pascal VOC**: Pascal Visual Object Classes format
- **YOLO**: YOLO object detection format

All models include validation, serialization, and conversion utilities.

## Quick Start

### DM Models

```python
from synapse_sdk.utils.annotation_models import DMv2Dataset, DMAttribute

# Create a DM dataset
dataset = DMv2Dataset(
    classification={
        "bounding_box": ["person", "car"],
        "keypoint": ["nose", "eye"]
    },
    images=[{
        "bounding_box": [
            {
                "id": "bbox_1",
                "classification": "person",
                "data": [100, 100, 50, 50],
                "attrs": []
            }
        ],
        "keypoint": [],
        "relation": [],
        "group": []
    }]
)
```

### COCO Models

```python
from synapse_sdk.utils.annotation_models.coco import (
    COCODataset,
    COCOImage,
    COCOAnnotation,
    COCOCategory
)

# Load from JSON
dataset = COCODataset.from_file("annotations.json")

# Access data
for image in dataset.images:
    anns = dataset.get_annotations_by_image_id(image.id)
    for ann in anns:
        category = dataset.get_category_by_id(ann.category_id)
        print(f"Found {category.name} at {ann.bbox}")

# Save to JSON
dataset.to_file("output.json", indent=2)
```

### Pascal VOC Models

```python
from synapse_sdk.utils.annotation_models.pascal import PascalAnnotation

# Load from XML
annotation = PascalAnnotation.from_file("annotation.xml")

# Access objects
for obj in annotation.objects:
    print(f"{obj.name}: ({obj.bndbox.xmin}, {obj.bndbox.ymin}) to ({obj.bndbox.xmax}, {obj.bndbox.ymax})")

# Save to XML
annotation.to_file("output.xml")
```

### YOLO Models

```python
from synapse_sdk.utils.annotation_models.yolo import YOLODataset, YOLODatasetConfig

# Create dataset config
config = YOLODatasetConfig(
    names=["person", "car", "dog"],
    nc=3,
    train="train/images",
    val="val/images"
)

# Save to YAML
config.to_yaml("dataset.yaml")

# Load from YAML
config = YOLODatasetConfig.from_yaml("dataset.yaml")
```

## Module Structure

```
annotation_models/
├── __init__.py          # Main exports
├── base.py              # Base utilities
├── dm/                  # DM format models
│   ├── common.py        # DMVersion, DMAttribute
│   ├── v1.py            # DMv1 models (event-based)
│   └── v2.py            # DMv2 models (collection-based)
├── coco/                # COCO format models
│   ├── annotation.py    # COCOAnnotation
│   ├── category.py      # COCOCategory
│   ├── image.py         # COCOImage
│   └── dataset.py       # COCODataset, COCOInfo, COCOLicense
├── yolo/                # YOLO format models
│   ├── annotation.py    # YOLOAnnotation
│   ├── config.py        # YOLODatasetConfig
│   └── dataset.py       # YOLOImage, YOLODataset
└── pascal/              # Pascal VOC format models
    ├── annotation.py    # Pascal components (BndBox, Object, etc.)
    └── dataset.py       # PascalAnnotation
```

## Features

### Type Safety

All models use Pydantic for runtime validation:

```python
from synapse_sdk.utils.annotation_models.coco import COCOAnnotation

# Validates all fields
ann = COCOAnnotation(
    id=1,
    image_id=1,
    category_id=1,
    bbox=[10, 20, 30, 40],  # [x, y, width, height]
    area=1200,
    iscrowd=0
)

# Type error - will raise ValidationError
ann = COCOAnnotation(
    id="not_an_int",  # Error: id must be int
    # ...
)
```

### Serialization

Built-in JSON and XML serialization:

```python
# COCO: JSON serialization
coco_dataset = COCODataset(...)
json_str = coco_dataset.to_json(indent=2)
coco_dataset.to_file("output.json")
loaded = COCODataset.from_json(json_str)

# Pascal VOC: XML serialization
pascal_ann = PascalAnnotation(...)
xml_str = pascal_ann.to_xml()
pascal_ann.to_file("output.xml")
loaded = PascalAnnotation.from_xml(xml_str)

# YOLO: YAML serialization
yolo_config = YOLODatasetConfig(...)
yaml_str = yolo_config.to_yaml()
yolo_config.to_yaml_file("dataset.yaml")
loaded = YOLODatasetConfig.from_yaml(yaml_str)
```

### Helper Methods

Utility methods for common operations:

```python
# COCO: Get annotations for an image
dataset = COCODataset(...)
annotations = dataset.get_annotations_by_image_id(image_id=123)
category = dataset.get_category_by_id(category_id=1)
image = dataset.get_image_by_id(image_id=123)

# YOLO: Convert between formats
ann = YOLOAnnotation(class_id=0, x_center=0.5, y_center=0.5, width=0.2, height=0.3)
abs_coords = ann.to_absolute_coords(img_width=640, img_height=480)
```

## Model Details

### DM Models

Two versions:
- **DMv1**: Event-based structure (legacy)
- **DMv2**: Collection-based structure (current)

Both support:
- Bounding boxes
- Polygons
- Polylines
- Keypoints
- Segmentation
- Relations
- Groups
- 3D annotations

### COCO Models

Standard COCO format with support for:
- Object detection (bounding boxes)
- Instance segmentation (polygons, RLE)
- Keypoint detection (pose estimation)
- Categories with hierarchies
- Image metadata
- Licensing information

### Pascal VOC Models

XML-based format for:
- Object detection (bounding boxes)
- Image metadata (size, source)
- Object properties (pose, truncated, difficult)
- Segmentation flag

### YOLO Models

YOLO format for:
- Object detection (normalized coordinates)
- Keypoint detection
- Dataset configuration (YAML)
- Train/val/test splits

## Migration

If you're migrating from the old `synapse_sdk.plugins.datasets` module:

```python
# Old (no longer works)
from synapse_sdk.plugins.datasets import DMv2Dataset, COCODataset

# New (correct)
from synapse_sdk.utils.annotation_models import DMv2Dataset, COCODataset
```

See [MIGRATION-DATASETS.md](../../../MIGRATION-DATASETS.md) for full migration guide.

## Related Modules

- [converters](../converters/): Convert between annotation formats
- [plugins.datasets](../../plugins/datasets/): Dataset handling plugins

## API Reference

For detailed API documentation, see the docstrings in each model file or visit the [API docs](../../../docs/docs/api/).
