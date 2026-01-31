---
id: categories
title: Plugin Categories
sidebar_position: 2
---

# Plugin Categories

Plugin categories organize plugins by their primary functionality.

## PluginCategory Enum

```python
from synapse_sdk.plugins.enums import PluginCategory
```

| Category | Value | Description |
|----------|-------|-------------|
| `NEURAL_NET` | `'neural_net'` | Machine learning model operations including training, inference, and deployment |
| `EXPORT` | `'export'` | Data export and transformation operations |
| `UPLOAD` | `'upload'` | File and data upload functionality |
| `SMART_TOOL` | `'smart_tool'` | Intelligent automation tools and utilities |
| `POST_ANNOTATION` | `'post_annotation'` | Post-processing workflows after data annotation |
| `PRE_ANNOTATION` | `'pre_annotation'` | Pre-processing workflows before data annotation |
| `DATA_VALIDATION` | `'data_validation'` | Data quality checks and validation operations |
| `CUSTOM` | `'custom'` | Custom plugins that don't fit other categories |

## Usage

### In config.yaml

```yaml filename="config.yaml"
name: My Training Plugin
code: my-training-plugin
version: 1.0.0
category: neural_net

actions:
  train:
    entrypoint: plugin.train.TrainAction
    method: job
```

### In Python Code

```python
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.action import BaseAction

class TrainAction(BaseAction):
    category = PluginCategory.NEURAL_NET
    action_name = 'train'

    def execute(self):
        return {'status': 'completed'}
```

### With @action Decorator

```python
from synapse_sdk.plugins.decorators import action
from synapse_sdk.plugins.enums import PluginCategory

@action(name='process', category=PluginCategory.SMART_TOOL)
def process_data(params, ctx):
    return {'processed': True}
```

## Category-Specific Features

### NEURAL_NET

Plugins for machine learning workflows.

**Common actions:**
- `train` - Model training
- `inference` - Model inference/prediction
- `export` - Model export to various formats
- `tune` - Hyperparameter tuning
- `deployment` - Model deployment

**Example:**

```yaml filename="config.yaml"
name: YOLOv8 Plugin
code: yolov8
version: 1.0.0
category: neural_net

actions:
  train:
    entrypoint: plugin.train.TrainAction
    method: job
    description: Train YOLOv8 model

  infer:
    entrypoint: plugin.inference.InferAction
    method: task
    description: Run inference on images
```

### SMART_TOOL

Interactive and automatic annotation tools.

**Common actions:**
- `annotate` - Automatic annotation
- `suggest` - Annotation suggestions
- `validate` - Annotation validation

```python
from synapse_sdk.plugins.enums import SmartToolType, AnnotationType

class AutoAnnotateAction(BaseAction):
    category = PluginCategory.SMART_TOOL
    tool_type = SmartToolType.AUTOMATIC
    annotation_type = AnnotationType.BBOX
```

### DATA_VALIDATION

Data quality and validation plugins.

**Common actions:**
- `validate` - Validate data against rules
- `check` - Run quality checks
- `report` - Generate validation reports

## Related Enums

### RunMethod

Execution methods for plugin actions.

```python
from synapse_sdk.plugins.enums import RunMethod

RunMethod.JOB    # Async execution via Ray Job API
RunMethod.TASK   # Fast execution via Ray Actor
RunMethod.SERVE  # Ray Serve deployment
```

### DataType

Data types handled by plugins.

```python
from synapse_sdk.plugins.enums import DataType

DataType.IMAGE   # Image data
DataType.TEXT    # Text data
DataType.VIDEO   # Video data
DataType.PCD     # Point cloud data
DataType.AUDIO   # Audio data
```

### AnnotationCategory

Annotation categories for smart tools.

```python
from synapse_sdk.plugins.enums import AnnotationCategory

AnnotationCategory.OBJECT_DETECTION  # Object detection
AnnotationCategory.CLASSIFICATION    # Image classification
AnnotationCategory.SEGMENTATION      # Semantic segmentation
AnnotationCategory.KEYPOINT          # Keypoint detection
AnnotationCategory.TEXT              # Text annotation
```

### AnnotationType

Annotation types for smart tools.

```python
from synapse_sdk.plugins.enums import AnnotationType

AnnotationType.BBOX     # Bounding box
AnnotationType.POLYGON  # Polygon
AnnotationType.POINT    # Point
AnnotationType.LINE     # Line/polyline
AnnotationType.MASK     # Segmentation mask
AnnotationType.LABEL    # Classification label
```

### SmartToolType

Smart tool implementation types.

```python
from synapse_sdk.plugins.enums import SmartToolType

SmartToolType.INTERACTIVE      # User-interactive tool
SmartToolType.AUTOMATIC        # Fully automatic
SmartToolType.SEMI_AUTOMATIC   # Semi-automatic with user input
```

## Related

- [Plugin Models](./models.md) - Runtime context and data models
- [Plugin Utilities](./utils.md) - Configuration utilities
- [Plugin Development](../../plugins/plugin-development.md) - Complete development guide
