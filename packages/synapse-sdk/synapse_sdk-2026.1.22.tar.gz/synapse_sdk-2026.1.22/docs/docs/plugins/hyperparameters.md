---
id: hyperparameters
title: Hyperparameters UI
sidebar_position: 4
---

# Hyperparameters UI

Auto-generate FormKit UI schemas from Pydantic models for training hyperparameters. The SDK automatically converts your `TrainParams` fields to frontend form inputs.

## Overview

When you define a training action with a Pydantic params model, the SDK can automatically generate a FormKit-compatible UI schema. This schema is written to `config.yaml` and used by the frontend to render hyperparameter input forms.

### At a Glance

| Pydantic Feature | FormKit Output |
|------------------|----------------|
| `int` / `float` type | `$formkit: number` |
| `bool` type | `$formkit: checkbox` |
| `str` type | `$formkit: text` |
| `default=50` | `value: 50`, `placeholder: 50` |
| `ge=1` / `le=100` | `min: 1`, `max: 100` |
| `description='...'` | `help: '...'` |
| Field name | `label` (auto-capitalized) |

## Quick Start

### 1. Define TrainParams

```python filename="plugin/train.py"
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.train import BaseTrainAction, BaseTrainParams

class TrainParams(BaseTrainParams):
    epochs: int = Field(default=50, ge=1, le=1000, description='Number of training epochs')
    batch_size: int = Field(default=8, ge=1, le=512, description='Batch size for training')
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1, description='Initial learning rate')
```

### 2. Run update-config

```bash
synapse plugin update-config
```

### 3. Check config.yaml

```yaml filename="config.yaml"
actions:
  train:
    entrypoint: plugin.train.TrainAction
    hyperparameters:
      train_ui_schemas:
      - $formkit: number
        name: epochs
        label: Epochs
        value: 50
        placeholder: 50
        help: Number of training epochs
        min: 1
        max: 1000
        number: true
        required: true
      - $formkit: number
        name: batch_size
        label: Batch Size
        value: 8
        placeholder: 8
        help: Batch size for training
        min: 1
        max: 512
        number: true
        required: true
      - $formkit: number
        name: learning_rate
        label: Learning Rate
        value: 0.001
        placeholder: 0.001
        help: Initial learning rate
        min: 0.0001
        max: 0.1
        number: true
        required: true
```

## Pydantic to FormKit Mapping

### Type Mapping

| Python Type | FormKit Type | Notes |
|-------------|--------------|-------|
| `int` | `number` | Adds `number: true` |
| `float` | `number` | Adds `number: true` |
| `bool` | `checkbox` | |
| `str` | `text` | |
| `Literal[...]` | `select` | Options from literal values |

### Constraint Mapping

| Pydantic Constraint | FormKit Property |
|--------------------|------------------|
| `ge=N` | `min: N` |
| `le=N` | `max: N` |
| `gt=N` | `min: N` (exclusive not supported) |
| `lt=N` | `max: N` (exclusive not supported) |
| `default=V` | `value: V`, `placeholder: V` |
| `description='...'` | `help: '...'` |

### Auto-Generated Properties

These properties are automatically added:

| Property | Value | Condition |
|----------|-------|-----------|
| `required` | `true` | All hyperparameters |
| `number` | `true` | Numeric types (`int`, `float`) |
| `label` | Field name | Auto-capitalized (e.g., `batch_size` → `Batch Size`) |

## Custom UI with json_schema_extra

Override the default FormKit type or add custom properties using `json_schema_extra`.

### Radio Buttons

```python
image_size: int = Field(
    default=640,
    description='Input image size',
    json_schema_extra={
        'formkit': 'radio',
        'options': [320, 416, 512, 608, 640, 1280],
    },
)
```

**Output:**

```yaml
- $formkit: radio
  name: image_size
  label: Image Size
  value: 640
  placeholder: 640
  help: Input image size
  options:
  - 320
  - 416
  - 512
  - 608
  - 640
  - 1280
  required: true
```

### Step for Decimal Inputs

```python
momentum: float = Field(
    default=0.9,
    ge=0.0,
    le=1.0,
    description='SGD momentum',
    json_schema_extra={'step': 0.01},
)
```

**Output:**

```yaml
- $formkit: number
  name: momentum
  label: Momentum
  value: 0.9
  min: 0.0
  max: 1.0
  step: 0.01
  number: true
  required: true
```

### Select Dropdown

```python
optimizer: str = Field(
    default='sgd',
    description='Optimizer type',
    json_schema_extra={
        'formkit': 'select',
        'options': ['sgd', 'adam', 'adamw'],
    },
)
```

### Custom Help Text

```python
epochs: int = Field(
    default=50,
    ge=1,
    le=1000,
    json_schema_extra={'help': 'Number of times to iterate over the dataset'},
)
```

## Supported json_schema_extra Keys

| Key | Type | Description |
|-----|------|-------------|
| `formkit` | `str` | Override FormKit type (`radio`, `select`, `checkbox`, etc.) |
| `options` | `list` | Options for `radio` or `select` inputs |
| `step` | `float` | Step increment for number inputs |
| `help` | `str` | Override help text (defaults to `description`) |
| `required` | `bool` | Override required flag (default: `true` for hyperparameters) |
| `min` | `number` | Override minimum value |
| `max` | `number` | Override maximum value |

## Excluding Fields

Some fields should not appear in the hyperparameters UI (e.g., internal pipeline fields).

### Auto-Excluded Fields

These field names are excluded by default:

- `data_path`
- `dataset_path`
- `checkpoint`
- `model_path`
- `weights_path`
- `output_path`
- `work_dir`

### Manual Exclusion

Exclude a field explicitly using `json_schema_extra`:

```python
class TrainParams(BaseTrainParams):
    # Excluded - internal field
    data_path: str = Field(
        description='Dataset path',
        json_schema_extra={'hyperparameter': False},
    )

    # Excluded - not user-configurable
    internal_flag: bool = Field(
        default=True,
        json_schema_extra={'exclude_from_ui': True},
    )

    # Included - normal hyperparameter
    epochs: int = Field(default=50, ge=1, le=1000)
```

## Supported Actions

Hyperparameters are only generated for specific action types:

| Action | Generated |
|--------|-----------|
| `train` | Yes |
| `tune` | Yes |
| `download` | No |
| `convert` | No |
| `test` | No |
| `inference` | No |

## Complete Example

```python filename="plugin/train.py"
from pathlib import Path
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.train import BaseTrainAction, BaseTrainParams
from synapse_sdk.plugins.types import ModelWeights, YOLODataset


class TrainParams(BaseTrainParams):
    """YOLOv11 training parameters."""

    # Auto-excluded (in DEFAULT_EXCLUDED_FIELDS)
    data_path: str | Path = Field(description='Path to dataset')

    # Standard number inputs
    epochs: int = Field(default=50, ge=1, le=1000, description='Training epochs')
    batch_size: int = Field(default=8, ge=1, le=512, description='Batch size')
    learning_rate: float = Field(default=0.001, ge=0.0001, le=0.1, description='Learning rate')

    # Radio button selection
    image_size: int = Field(
        default=640,
        description='Input image size',
        json_schema_extra={'formkit': 'radio', 'options': [320, 416, 512, 608, 640, 1280]},
    )

    # Number with step
    momentum: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description='SGD momentum',
        json_schema_extra={'step': 0.01},
    )


class TrainAction(BaseTrainAction[TrainParams]):
    action_name = 'train'
    input_type = YOLODataset
    output_type = ModelWeights

    def execute(self):
        # Training implementation
        pass
```

Run `synapse plugin update-config` to generate the UI schema in `config.yaml`.

## CLI Commands

### Generate/Update Hyperparameters

```bash
# Update config.yaml with hyperparameters from code
synapse plugin update-config

# Specify plugin path
synapse plugin update-config -p /path/to/plugin
```

### Verify Configuration

```bash
# Test plugin configuration
synapse plugin test
```

## Related

- [Plugin Development](./plugin-development.md) — Complete plugin development guide
- [Defining Actions](./defining-actions.md) — Action definition patterns
- [Plugin Utilities](../api/plugins/utils.md) — `pydantic_to_ui_schema()` API reference
