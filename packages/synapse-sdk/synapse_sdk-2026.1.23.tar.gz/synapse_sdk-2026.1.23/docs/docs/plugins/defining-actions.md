---
id: defining-actions
title: Defining Actions
sidebar_position: 3
---

# Defining Actions

Actions are the core building blocks of plugins. Each action represents a discrete unit of work that can be executed, tracked, and composed into pipelines.

:::info[Prerequisites]

Read the [Plugin System Overview](./index.md) to understand core concepts before defining actions.

:::

## Overview

Synapse SDK provides two approaches to define actions:

| Approach | Best For | Features |
|----------|----------|----------|
| **Function-based** (`@action`) | Simple, stateless operations | Minimal boilerplate, direct function call |
| **Class-based** (`BaseAction`) | Complex workflows, multi-step processes | State management, helper methods, step orchestration |

## Function-Based Actions

Use the `@action` decorator for simple, single-function actions that don't require state management.

### Decorator Syntax

```python filename="synapse_sdk/plugins/decorators.py"
@action(
    name: str | None = None,             # Action name (defaults to function name)
    description: str = '',                # Human-readable description
    params: type[BaseModel] | None = None,  # Pydantic model for input validation
    result: type[BaseModel] | None = None,  # Pydantic model for result validation
    category: PluginCategory | None = None, # Plugin category (optional)
)
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | No | Action identifier. Defaults to function name |
| `description` | `str` | No | Human-readable description |
| `params` | `type[BaseModel]` | No | Pydantic model for input validation (recommended) |
| `result` | `type[BaseModel]` | No | Pydantic model for result validation |
| `category` | `PluginCategory` | No | Category for grouping actions |

### Example

```python filename="plugin/actions.py"
from pydantic import BaseModel, Field
from synapse_sdk.plugins import action, RuntimeContext

class ConvertParams(BaseModel):
    input_path: str
    output_format: str = Field(default='yolo', description='Target format')

class ConvertResult(BaseModel):
    output_path: str
    file_count: int

@action(
    name='convert',
    description='Convert dataset to target format',
    params=ConvertParams,
    result=ConvertResult,
)
def convert(params: ConvertParams, ctx: RuntimeContext) -> ConvertResult:
    # Access validated parameters
    source = params.input_path
    target_format = params.output_format

    # Report progress
    ctx.set_progress(0, 100)

    # Your conversion logic here
    output_path = do_conversion(source, target_format)

    ctx.set_progress(100, 100)

    return ConvertResult(output_path=output_path, file_count=42)
```

**Function Signature Requirements:**
- First argument: `params` (Pydantic model instance)
- Second argument: `ctx` (RuntimeContext)

> **Good to know**: The `@action` decorator attaches metadata to the function (`_is_action`, `_action_name`, `_action_params`, etc.) for automatic discovery.

## Class-Based Actions

Use `BaseAction` for complex workflows that require state management, helper methods, or multi-step orchestration.

### Basic Structure

```python filename="plugin/train.py"
from pydantic import BaseModel, Field
from synapse_sdk.plugins import BaseAction
from synapse_sdk.plugins.enums import PluginCategory

class TrainParams(BaseModel):
    epochs: int = Field(default=10, ge=1, le=1000)
    learning_rate: float = Field(default=0.001, gt=0, lt=1)
    batch_size: int = Field(default=32, ge=1)

class TrainResult(BaseModel):
    weights_path: str
    final_loss: float

class TrainAction(BaseAction[TrainParams]):
    """Train a model on the dataset."""

    # Optional: override if not using config.yaml
    action_name = 'train'
    category = PluginCategory.NEURAL_NET

    # Optional: enable result validation
    result_model = TrainResult

    def execute(self) -> TrainResult:
        # Access validated parameters via self.params
        epochs = self.params.epochs
        lr = self.params.learning_rate

        # Log events
        self.log('train_start', {'epochs': epochs, 'lr': lr})

        for epoch in range(epochs):
            # Report progress
            self.set_progress(epoch + 1, epochs, category='train')

            loss = train_one_epoch(epoch, lr)

            # Record metrics
            self.set_metrics({'loss': loss, 'epoch': epoch}, category='train')

        return TrainResult(weights_path='/model/weights.pt', final_loss=loss)
```

### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `action_name` | `str \| None` | Action identifier (injected from config.yaml if not set) |
| `category` | `PluginCategory \| None` | Category for grouping |
| `input_type` | `type[DataType] \| None` | Semantic input type for pipeline compatibility |
| `output_type` | `type[DataType] \| None` | Semantic output type for pipeline compatibility |
| `params_model` | `type[BaseModel]` | Auto-extracted from generic parameter |
| `result_model` | `type[BaseModel] \| NoResult` | Result validation schema (default: `NoResult`) |

### Instance Methods

| Method | Description |
|--------|-------------|
| `execute()` | Main logic (abstract, must override) |
| `log(event, data, file)` | Log structured events |
| `set_progress(current, total, category)` | Report progress |
| `set_metrics(value, category)` | Record metrics |
| `autolog(framework)` | Enable ML framework auto-logging |

### Available Base Classes

Synapse SDK provides specialized base classes for common workflow types:

| Base Class | Category | Location | Use Case |
|------------|----------|----------|----------|
| `BaseAction` | Any | `synapse_sdk.plugins` | Generic actions |
| `BaseTrainAction` | `neural_net` | `synapse_sdk.plugins` | Model training |
| `BaseInferenceAction` | `neural_net` | `synapse_sdk.plugins` | Model inference |
| `BaseExportAction` | `export` | `synapse_sdk.plugins` | Data export |
| `BaseUploadAction` | `upload` | `synapse_sdk.plugins` | Data upload |
| `DatasetAction` | - | `synapse_sdk.plugins.actions.dataset` | Dataset operations |

> **Good to know**: Most base classes are re-exported from `synapse_sdk.plugins` for convenience. `DatasetAction` must be imported from `synapse_sdk.plugins.actions.dataset`.

#### BaseTrainAction

Provides helper methods for training workflows:

```python filename="plugin/train.py"
from synapse_sdk.plugins import BaseTrainAction
from synapse_sdk.plugins.actions.train import BaseTrainParams  # Not re-exported from synapse_sdk.plugins

class MyTrainParams(BaseTrainParams):
    epochs: int = 100
    dataset: int  # Required for get_dataset()

class MyTrainAction(BaseTrainAction[MyTrainParams]):
    def execute(self) -> dict:
        # Fetch dataset from backend
        dataset = self.get_dataset()

        # Load checkpoint if resuming
        checkpoint = self.get_checkpoint()

        # Train model...
        model_path = train(dataset, checkpoint)

        # Upload trained model
        model = self.create_model(model_path, name='my-model')

        return {'model_id': model['id']}
```

**Helper Methods:**
- `get_dataset()` - Fetch training dataset (requires `dataset` field in params model)
- `get_checkpoint()` - Load checkpoint model if `params.checkpoint` is set
- `create_model(path, **kwargs)` - Upload trained model to backend
- `get_model(model_id)` - Retrieve model metadata

> **Good to know**: `get_dataset()` requires your params model to have a `dataset: int` field. If not present, a `ValueError` is raised with instructions to either add the field or override `get_dataset()`.

**Progress Categories:**

Access via instance attribute `self.progress`:
- `self.progress.DATASET` - Data loading phase
- `self.progress.TRAIN` - Training iterations
- `self.progress.MODEL_UPLOAD` - Model upload phase

### Result Validation

Enable result validation by setting `result_model`:

```python filename="plugin/export.py"
from pydantic import BaseModel
from synapse_sdk.plugins import BaseAction, NoResult

class ExportResult(BaseModel):
    output_path: str
    record_count: int

class ExportAction(BaseAction[ExportParams]):
    # Enable validation
    result_model = ExportResult

    def execute(self) -> ExportResult:
        # Return validated result
        return ExportResult(output_path='/data/export', record_count=1000)
```

> **Good to know**: If `result_model` is not set (defaults to `NoResult`), result validation is skipped. When set, results are validated but failures only log warnings (non-blocking).

## Parameter Models

Use Pydantic models to define and validate action parameters.

### Field Configuration

```python filename="plugin/params.py"
from pydantic import BaseModel, Field
from typing import Literal

class AugmentationConfig(BaseModel):
    """Nested configuration for data augmentation."""
    flip: bool = True
    rotate: float = Field(default=0.0, ge=0, le=360)

class TrainParams(BaseModel):
    # Required field
    dataset: int

    # With default and constraints
    epochs: int = Field(default=100, ge=1, le=1000, description='Training epochs')

    # With choices
    optimizer: Literal['adam', 'sgd', 'adamw'] = 'adam'

    # Nested model
    augmentation: AugmentationConfig | None = None
```

### Validators

```python filename="plugin/params.py"
from pydantic import BaseModel, field_validator

class InferenceParams(BaseModel):
    confidence: float = 0.5

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v
```

## Discovery Modes

Synapse SDK discovers actions through three mechanisms:

### from_path()

Load plugin configuration from `config.yaml`:

```python filename="example.py"
from synapse_sdk.plugins.discovery import PluginDiscovery

# From directory (auto-finds config.yaml)
discovery = PluginDiscovery.from_path('/path/to/plugin')

# Or explicit path
discovery = PluginDiscovery.from_path('/path/to/plugin/config.yaml')

# List available actions (returns keys from config.yaml's actions section)
actions = discovery.list_actions()  # e.g., ['train', 'infer', 'export']

# Get action class
action_cls = discovery.get_action_class('train')
```

> **Good to know**: `list_actions()` returns the action names defined in `config.yaml`. The actual list depends on your plugin's configuration.

### from_module()

Discover actions by introspecting a Python module:

```python filename="example.py"
import my_plugin
from synapse_sdk.plugins.discovery import PluginDiscovery
from synapse_sdk.plugins.enums import PluginCategory

# Auto-discover @action functions and BaseAction subclasses
discovery = PluginDiscovery.from_module(my_plugin)

# Optional: specify name and category
discovery = PluginDiscovery.from_module(
    my_plugin,
    name='my-plugin',
    category=PluginCategory.NEURAL_NET,
)
```

> **Good to know**: `from_module()` scans for functions with `_is_action=True` attribute (from `@action`) and classes that subclass `BaseAction`.

### discover_actions()

Static analysis of source files (AST parsing):

```python filename="example.py"
from synapse_sdk.plugins.discovery import PluginDiscovery

# Discover without importing modules
actions = PluginDiscovery.discover_actions('/path/to/plugin')
# Returns: {'train': {'entrypoint': '...', 'input_type': '...', 'output_type': '...'}}
```

## config.yaml Configuration

Define plugin metadata and actions in `config.yaml`:

### Basic Structure

```yaml filename="config.yaml"
# Plugin metadata
name: YOLOv8 Training Plugin
code: yolov8
version: 0.1.0
category: neural_net

# Description
description: Train and deploy YOLOv8 object detection models
readme: README.md

# Data configuration
data_type: image
tasks:
  - image.object_detection
  - image.instance_segmentation

# Dependencies
package_manager: pip  # or 'uv'
wheels_dir: wheels

# Environment variables
env:
  LOG_LEVEL: INFO

# Actions
actions:
  train:
    entrypoint: plugin.train:TrainAction
    method: job
    description: Train a YOLOv8 model

  infer:
    entrypoint: plugin.inference:InferenceAction
    method: task
    description: Run inference on images
```

### Actions Section

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `entrypoint` | `str` | Yes | Module path to action (`module.path:ClassName`) |
| `method` | `str` | No | Execution method: `job`, `task`, or `serve` |
| `description` | `str` | No | Human-readable description |
| `input_type` | `str` | No | Semantic input type (auto-synced from code) |
| `output_type` | `str` | No | Semantic output type (auto-synced from code) |

### Execution Methods

| Method | Startup | Isolation | Use Case |
|--------|---------|-----------|----------|
| `task` | Under 1 second | Process-level | Quick parallel tasks (default) |
| `job` | ~30 seconds | Full isolation | Long-running, heavy workloads |
| `serve` | Variable | Container | HTTP inference endpoints |

### Complete Example

```yaml filename="config.yaml"
name: Image Classification Plugin
code: image-classifier
version: 1.0.0
category: neural_net
description: Train and deploy image classification models

data_type: image
tasks:
  - image.classification

package_manager: pip
package_manager_options: []
wheels_dir: wheels

env:
  CUDA_VISIBLE_DEVICES: '0'
  LOG_LEVEL: INFO

runtime_env:
  py_modules:
    - ./plugin

actions:
  train:
    entrypoint: plugin.train:TrainAction
    method: job
    description: Train classification model
    input_type: dm_v2_dataset
    output_type: model_weights

  infer:
    entrypoint: plugin.inference:InferenceAction
    method: task
    description: Classify images
    input_type: image_file
    output_type: predictions

  export:
    entrypoint: plugin.export:ExportAction
    method: task
    description: Export model to ONNX
    input_type: model_weights
    output_type: onnx_model
```

## What to Use and When

| Situation | Recommended Approach | Why |
|-----------|---------------------|-----|
| Simple data transformation | Function-based (`@action`) | Minimal boilerplate, single function |
| Stateless utility operations | Function-based (`@action`) | No state management needed |
| Model training workflow | Class-based (`BaseTrainAction`) | Built-in dataset/model helpers |
| Model inference | Class-based (`BaseInferenceAction`) | Model loading helpers |
| Multi-step orchestration | Class-based with `setup_steps()` | Step registry, rollback support |
| Progress tracking with phases | Class-based | Progress categories |
| Shared state across methods | Class-based | Instance attributes |

> **Tip**: Start with function-based actions for simple tasks. Migrate to class-based when you need state management, helper methods, or step orchestration.

## Related

- [RuntimeContext](/plugins/runtime-context) - Context API reference
- [Steps & Workflow](/plugins/steps-workflow) - Multi-step workflows
