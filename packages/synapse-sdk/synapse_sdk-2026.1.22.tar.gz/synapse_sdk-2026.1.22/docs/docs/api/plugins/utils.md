---
id: utils
title: Plugin Utilities
sidebar_position: 3
---

# Plugin Utilities

Utility functions for plugin configuration parsing, action discovery, and UI schema generation.

## Overview

The `synapse_sdk.plugins.utils` module provides functions for working with plugin configurations and generating UI schemas from Pydantic models.

## Configuration Utilities

### get_plugin_actions()

Extract action names from a plugin configuration.

```python
from synapse_sdk.plugins.utils import get_plugin_actions

# From config dictionary
config = {'actions': {'train': {...}, 'inference': {...}}}
actions = get_plugin_actions(config)
# Returns: ['train', 'inference']

# From plugin path (loads config.yaml)
actions = get_plugin_actions('/path/to/plugin')
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config` | `dict \| PluginConfig \| Path \| str` | Yes | Plugin config dict, PluginConfig instance, or path to config.yaml |

**Returns:** `list[str]` - List of action names. Returns empty list on error.

### get_action_method()

Get the execution method for a specific action.

```python
from synapse_sdk.plugins.utils import get_action_method
from synapse_sdk.plugins.enums import RunMethod

method = get_action_method(config, 'train')

if method == RunMethod.JOB:
    # Async execution via Ray Job API
    pass
elif method == RunMethod.TASK:
    # Fast execution via Ray Actor
    pass
elif method == RunMethod.SERVE:
    # Ray Serve deployment
    pass
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config` | `dict \| PluginConfig` | Yes | Plugin configuration |
| `action` | `str` | Yes | Action name |

**Returns:** `RunMethod` enum value. Defaults to `TASK` if not found.

### get_action_config()

Retrieve the full configuration for a specific action.

```python
from synapse_sdk.plugins.utils import get_action_config

action_config = get_action_config(config, 'train')
# Returns: {'entrypoint': 'plugin.train.TrainAction', 'method': 'job', ...}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config` | `dict \| PluginConfig` | Yes | Plugin configuration |
| `action` | `str` | Yes | Action name |

**Returns:** `dict` - Action configuration dictionary.

**Raises:**

- `KeyError`: If action not found in configuration
- `ValueError`: If config type is invalid

## UI Schema Generation

Generate FormKit-compatible UI schemas from Pydantic models for frontend form rendering.

### pydantic_to_ui_schema()

Convert a Pydantic model to FormKit UI schema format.

```python
from pydantic import BaseModel, Field
from synapse_sdk.plugins.utils import pydantic_to_ui_schema

class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000, description="Training epochs")
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)

schema = pydantic_to_ui_schema(TrainParams)
```

**Output:**

```python
[
    {
        '$formkit': 'number',
        'name': 'epochs',
        'label': 'Epochs',
        'value': 50,
        'placeholder': 50,
        'help': 'Training epochs',
        'min': 1,
        'max': 1000,
        'number': True
    },
    {
        '$formkit': 'number',
        'name': 'batch_size',
        'label': 'Batch Size',
        'value': 8,
        'placeholder': 8,
        'min': 1,
        'max': 512,
        'number': True
    },
    # ...
]
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `type[BaseModel]` | Yes | Pydantic model class |

**Returns:** `list[dict]` - List of FormKit schema items.

#### Custom UI via json_schema_extra

Override FormKit type and add custom options:

```python
from pydantic import BaseModel, Field

class Params(BaseModel):
    model_size: str = Field(
        default="medium",
        json_schema_extra={
            "formkit": "select",
            "options": ["small", "medium", "large"],
            "help": "Model size selection"
        }
    )
```

### get_action_ui_schema()

Get UI schema for an action's parameters in API response format.

```python
from synapse_sdk.plugins.utils import get_action_ui_schema

schema = get_action_ui_schema(TrainParams, 'train')
# Returns: {'action': 'train', 'ui_schemas': [...]}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `type[BaseModel]` | Yes | Pydantic model class for parameters |
| `action_name` | `str \| None` | No | Optional action name for response |

**Returns:** `dict` with `action` and `ui_schemas` keys.

## Plugin Execution

### run_plugin()

Execute plugin actions with automatic discovery.

```python
from synapse_sdk.plugins.runner import run_plugin

# Auto-discover from Python module path
result = run_plugin('plugins.yolov8', 'train', {'epochs': 10})

# Auto-discover from config.yaml path
result = run_plugin('/path/to/plugin', 'train', {'epochs': 10})
```

**Execution Modes:**

```python
# Local execution (default) - runs in current process
result = run_plugin('plugin', 'train', params, mode='local')

# Ray Task - fast startup via Ray Actor
result = run_plugin('plugin', 'train', params, mode='task')

# Ray Job - async execution via Ray Job API
job_id = run_plugin('plugin', 'train', params, mode='job')
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `source` | `str` | Yes | - | Plugin module path or filesystem path |
| `action` | `str` | Yes | - | Action name to execute |
| `params` | `dict` | Yes | - | Parameters for the action |
| `mode` | `str` | No | `'local'` | Execution mode: `'local'`, `'task'`, `'job'` |
| `action_cls` | `type` | No | `None` | Explicit action class (skips discovery) |

**Returns:** Action result or job ID (for `'job'` mode).

## PluginDiscovery

Comprehensive plugin introspection from config files or Python modules.

### From Config Path

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

# Load from directory containing config.yaml
discovery = PluginDiscovery.from_path('/path/to/plugin')

# Available methods
discovery.list_actions()           # ['train', 'inference', 'export']
discovery.has_action('train')      # True
discovery.get_action_method('train')  # RunMethod.JOB
discovery.get_action_config('train')  # ActionConfig instance
discovery.get_action_class('train')   # Loads class from entrypoint
```

### From Python Module

```python
from synapse_sdk.plugins.discovery import PluginDiscovery
import my_plugin

# Auto-discover @action decorators and BaseAction subclasses
discovery = PluginDiscovery.from_module(my_plugin)

for action in discovery.list_actions():
    print(f"Action: {action}")
    print(f"  Method: {discovery.get_action_method(action)}")
```

## Defining Actions

### Option 1: @action Decorator

Recommended for Python modules:

```python
from synapse_sdk.plugins.decorators import action
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10
    batch_size: int = 32

@action(name='train', description='Train model', params=TrainParams)
def train(params: TrainParams, ctx):
    return {'accuracy': 0.95}
```

### Option 2: BaseAction Class

Class-based approach with full control:

```python
from synapse_sdk.plugins.action import BaseAction
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10

class TrainAction(BaseAction[TrainParams]):
    action_name = 'train'
    params_model = TrainParams

    def execute(self):
        # self.params contains validated TrainParams
        # self.ctx contains RuntimeContext
        return {'accuracy': 0.95}
```

### Option 3: config.yaml

Recommended for packaged plugins:

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
```

## Best Practices

1. **Use `run_plugin()`** for execution instead of manual discovery
2. **Use `PluginDiscovery`** for introspection instead of direct config parsing
3. **Validate configs** through Pydantic models for type safety
4. **Use absolute paths** when possible for reliability

## Related

- [RuntimeContext](./models.md) - Execution context for actions
- [Plugin Categories](./categories.md) - Available plugin categories
- [Plugin Development](../../plugins/plugin-development.md) - Complete development guide
