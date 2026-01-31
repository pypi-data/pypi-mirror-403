---
id: runtime-context
title: RuntimeContext
sidebar_position: 4
---

# RuntimeContext

RuntimeContext is a context object injected during action execution. It provides access to all dependencies required for action execution, including logging, environment variables, clients, and checkpoints.

:::info[Prerequisites]

Understand the [Plugin System Overview](./index.md) and [Defining Actions](./defining-actions.md) before using RuntimeContext.

:::

## Overview

RuntimeContext is used in both function-based and class-based actions.

- **Logging**: Progress, metrics, and event logging
- **Environment Variables**: Configuration access through `PluginEnvironment`
- **Clients**: Backend API and agent clients
- **Checkpoint**: Pretrained model information

## RuntimeContext Structure

RuntimeContext is a dataclass defined in `synapse_sdk/plugins/context/__init__.py`.

```python
from dataclasses import dataclass
from typing import Any

from synapse_sdk.plugins.context import PluginEnvironment

@dataclass
class RuntimeContext:
    logger: BaseLogger
    env: PluginEnvironment
    job_id: str | None = None
    client: BackendClient | None = None
    agent_client: AgentClient | None = None
    checkpoint: dict[str, Any] | None = None
```

| Property | Type | Description |
|----------|------|-------------|
| `logger` | `BaseLogger` | Logger for progress, metrics, and event logging |
| `env` | `PluginEnvironment` | Environment variables and configuration access |
| `job_id` | `str \| None` | Job ID for task tracking |
| `client` | `BackendClient \| None` | Backend API client |
| `agent_client` | `AgentClient \| None` | Ray agent client |
| `checkpoint` | `dict[str, Any] \| None` | Pretrained model information (includes `category`, `path`) |

## Available Methods

### Progress Tracking

Use `set_progress()` to track operation progress. Specify a category to manage progress individually for multi-phase operations.

```python
def set_progress(self, current: int, total: int, category: str | None = None) -> None:
    """Set progress for the current operation.

    Args:
        current: Current progress value (0 to total).
        total: Total progress value.
        category: Optional category name for multi-phase progress.
    """
```

**Example:**

```python
# Single progress
ctx.set_progress(50, 100)

# Category-based progress (multi-phase operations)
ctx.set_progress(10, 100, 'download')
ctx.set_progress(5, 50, 'train')
ctx.set_progress(3, 10, 'export')
```

### Metrics

Use `set_metrics()` to record training metrics or performance indicators.

```python
def set_metrics(self, value: dict[str, Any], category: str) -> None:
    """Set metrics for a category.

    Args:
        value: Dictionary of metric values.
        category: Non-empty category name.
    """
```

**Example:**

```python
# Record training metrics
ctx.set_metrics({
    'loss': 0.1,
    'accuracy': 0.95,
    'learning_rate': 0.001
}, 'training')

# Record inference metrics
ctx.set_metrics({
    'inference_time': 0.05,
    'throughput': 200
}, 'inference')
```

### Logging

Three logging methods are provided.

#### log()

Structured event logging:

```python
def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
    """Log an event with data.

    Args:
        event: Event name/type.
        data: Dictionary of event data.
        file: Optional file path associated with the event.
    """
```

```python
ctx.log('checkpoint_saved', {'epoch': 5, 'path': '/model.pt'})
ctx.log('data_loaded', {'count': 1000}, file='/data/train.csv')
```

#### log_message()

User-facing message logging:

```python
def log_message(self, message: str, context: str = 'info') -> None:
    """Log a user-facing message.

    Args:
        message: Message content.
        context: Message context/level ('info', 'warning', 'danger', 'success').
    """
```

```python
ctx.log_message('Training started', 'info')
ctx.log_message('Low GPU memory detected', 'warning')
ctx.log_message('Training completed successfully', 'success')
ctx.log_message('Failed to load checkpoint', 'danger')
```

#### log_dev_event()

Developer debug event logging (not displayed to end users):

```python
def log_dev_event(self, message: str, data: dict[str, Any] | None = None) -> None:
    """Log a development/debug event.

    Args:
        message: Event message.
        data: Optional additional data.
    """
```

```python
ctx.log_dev_event('Model architecture initialized', {'layers': 12})
ctx.log_dev_event('Batch processing started')
```

### Environment Variables

Access environment variables through `PluginEnvironment`. Type-safe methods are provided.

```python
# Basic access
value = ctx.env.get('MY_VAR', 'default')

# Type-specific methods
api_key = ctx.env.get_str('API_KEY')
batch_size = ctx.env.get_int('BATCH_SIZE', default=32)
learning_rate = ctx.env.get_float('LEARNING_RATE', default=0.001)
debug_mode = ctx.env.get_bool('DEBUG', default=False)
gpu_ids = ctx.env.get_list('GPU_IDS', default=['0'])  # Converts comma-separated string to list
```

**PluginEnvironment Methods:**

| Method | Return Type | Description |
|--------|-------------|-------------|
| `get(key, default)` | `Any` | Returns raw value |
| `get_str(key, default)` | `str \| None` | Converts to string |
| `get_int(key, default)` | `int \| None` | Converts to integer |
| `get_float(key, default)` | `float \| None` | Converts to float |
| `get_bool(key, default)` | `bool \| None` | Converts to boolean (handles `'true'`, `'1'`, `'yes'`) |
| `get_list(key, default)` | `list \| None` | Converts comma-separated string to list |

### Backend Client

Access datasets, models, and more through the backend API client.

:::warning[Important]
`ctx.client` can be `None`. Always check before use.
:::

```python
# Check for None before use
if ctx.client:
    dataset = ctx.client.get_data_collection(dataset)
    model_info = ctx.client.get_model(model_id)

# Or use assertion
assert ctx.client is not None, "Backend client is required"
dataset = ctx.client.get_data_collection(dataset)
```

### Checkpoint (Pretrained Model)

Access pretrained model information. The checkpoint is a dictionary containing `category` and `path`.

```python
if ctx.checkpoint:
    category = ctx.checkpoint.get('category')  # 'base' or fine-tuned model name
    model_path = ctx.checkpoint.get('path')    # Model file path

    if category == 'base':
        print(f'Using base model from {model_path}')
    else:
        print(f'Using fine-tuned model: {category}')
```

## Action-Specific Contexts

In step-based workflows, use action-specific contexts that inherit from `BaseStepContext` instead of extending `RuntimeContext` directly. These contexts access `RuntimeContext` through the `runtime_ctx` property.

```python
from dataclasses import dataclass, field
from typing import Any

from synapse_sdk.plugins.steps import BaseStepContext

@dataclass
class MyStepContext(BaseStepContext):
    # BaseStepContext includes runtime_ctx: RuntimeContext
    params: dict[str, Any] = field(default_factory=dict)
    results: list[Any] = field(default_factory=list)
```

**Available Action-Specific Contexts:**

| Context | Location | Description |
|---------|----------|-------------|
| `TrainContext` | `synapse_sdk.plugins.actions.train` | Training workflow state (dataset, model_path, etc.) |
| `InferenceContext` | `synapse_sdk.plugins.actions.inference` | Inference workflow state (requests, results, etc.) |
| `ExportContext` | `synapse_sdk.plugins.actions.export` | Export workflow state (output_path, etc.) |
| `UploadContext` | `synapse_sdk.plugins.actions.upload` | Upload workflow state (organized_files, etc.) |
| `DeploymentContext` | `synapse_sdk.plugins.actions.inference` | Deployment workflow state (serve_app_name, etc.) |

**Accessing RuntimeContext from Step Context:**

```python
from synapse_sdk.plugins.actions.train import TrainContext
from synapse_sdk.plugins.steps import BaseStep, StepResult

# Usage within a Step
class LoadDataStep(BaseStep[TrainContext]):
    def execute(self, context: TrainContext) -> StepResult:
        # Access RuntimeContext methods through runtime_ctx
        context.runtime_ctx.set_progress(0, 100, 'load')
        context.runtime_ctx.log_message('Loading dataset...', 'info')

        # Or use BaseStepContext convenience methods
        context.set_progress(50, 100)  # Category auto-set
        context.log('data_loaded', {'count': 1000})

        return StepResult(success=True)
```

## Usage in Function-Based Actions

In function-based actions, use the `@action` decorator and receive `RuntimeContext` as the second argument.

```python
from pydantic import BaseModel
from synapse_sdk.plugins import action, RuntimeContext

class TrainParams(BaseModel):
    epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 0.001

@action(params=TrainParams, description='Train a model')
def train(params: TrainParams, ctx: RuntimeContext) -> dict:
    ctx.log_message('Training started', 'info')

    for epoch in range(params.epochs):
        ctx.set_progress(epoch + 1, params.epochs, 'train')
        ctx.set_metrics({'epoch': epoch, 'loss': 0.1}, 'training')

    ctx.log_message('Training completed', 'success')
    return {'status': 'completed', 'epochs': params.epochs}
```

## Usage in Class-Based Actions

In class-based actions, inherit from `BaseAction` and access `RuntimeContext` through `self.ctx`. Helper methods are also provided for convenience.

```python
from pydantic import BaseModel
from synapse_sdk.plugins import BaseAction, RuntimeContext

class TrainParams(BaseModel):
    epochs: int = 10

class TrainAction(BaseAction[TrainParams]):
    def execute(self) -> dict:
        # Access RuntimeContext through self.ctx
        self.ctx.log_message('Training started', 'info')

        for epoch in range(self.params.epochs):
            # Use helper methods (equivalent to self.ctx.set_progress)
            self.set_progress(epoch + 1, self.params.epochs, 'train')
            self.set_metrics({'epoch': epoch, 'loss': 0.1}, 'training')

        return {'status': 'completed'}
```

**BaseAction Helper Methods:**

| Method | Description |
|--------|-------------|
| `self.log(event, data, file)` | Equivalent to `self.ctx.log()` |
| `self.set_progress(current, total, category)` | Equivalent to `self.ctx.set_progress()` |
| `self.set_metrics(value, category)` | Equivalent to `self.ctx.set_metrics()` |
| `self.logger` | Property to access `self.ctx.logger` |

## Best Practices

### Progress Updates

Update progress in meaningful units. Overly frequent updates can impact performance.

```python
# Good: Update per epoch
for epoch in range(100):
    train_one_epoch()
    ctx.set_progress(epoch + 1, 100, 'train')

# Bad: Update every batch
for batch in dataloader:  # Called thousands of times
    process_batch(batch)
    ctx.set_progress(batch_idx, total_batches)  # Excessive calls
```

### Use Appropriate Log Levels

```python
# info: General progress
ctx.log_message('Starting data preprocessing', 'info')

# warning: Requires attention but can continue
ctx.log_message('GPU memory usage high (90%)', 'warning')

# success: Operation completed
ctx.log_message('Model training completed', 'success')

# danger: Error occurred (unrecoverable)
ctx.log_message('Failed to save checkpoint', 'danger')
```

### Avoid Logging Sensitive Information

Never include sensitive information such as API keys or passwords in logs.

```python
# Bad
ctx.log('config_loaded', {'api_key': api_key})

# Good
ctx.log('config_loaded', {'api_key_set': bool(api_key)})
```

### Check for None

`client`, `agent_client`, `checkpoint`, and similar properties can be `None`. Always check before use.

```python
# Recommended
if ctx.client:
    data = ctx.client.fetch_data()
else:
    ctx.log_message('Backend client not available', 'warning')
    data = load_local_data()
```
