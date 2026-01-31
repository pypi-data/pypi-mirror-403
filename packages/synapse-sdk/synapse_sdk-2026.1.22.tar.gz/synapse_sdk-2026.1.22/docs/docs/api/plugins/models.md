---
id: models
title: Plugin Models
sidebar_position: 1
---

# Plugin Models

Core data models and runtime context for the plugin system.

## RuntimeContext

Execution context injected into plugin actions. Provides access to logging, environment, and client dependencies.

```python
from synapse_sdk.plugins.context import RuntimeContext
```

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `logger` | `BaseLogger` | Logger instance for progress, metrics, and event logging |
| `env` | `PluginEnvironment` | Environment variables and configuration |
| `job_id` | `str \| None` | Optional job identifier for tracking |
| `client` | `BackendClient \| None` | Optional backend client for API access |
| `agent_client` | `AgentClient \| None` | Optional agent client for Ray operations |
| `checkpoint` | `dict \| None` | Checkpoint info with `category` and `path` keys |

### Methods

#### log()

Log an event with associated data.

```python
def execute(self):
    self.ctx.log('checkpoint', {'epoch': 5, 'loss': 0.25})
    self.ctx.log('prediction', {'class': 'cat', 'confidence': 0.95}, file='/data/img.jpg')
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `event` | `str` | Yes | Event name/type |
| `data` | `dict` | Yes | Dictionary of event data |
| `file` | `str \| None` | No | Optional file path associated with the event |

#### set_progress()

Update progress for the current operation.

```python
def execute(self):
    total_items = 100
    for i, item in enumerate(items):
        process(item)
        self.ctx.set_progress(i + 1, total_items)

    # Multi-phase progress with step names
    self.ctx.set_progress(50, 100, step='preprocessing')
    self.ctx.set_progress(100, 100, step='training')
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `current` | `int` | Yes | Current progress value (0 to total) |
| `total` | `int` | Yes | Total progress value |
| `step` | `str \| None` | No | Step name for multi-phase progress |

#### set_metrics()

Record metrics for monitoring and analysis.

```python
def execute(self):
    # Training metrics
    self.ctx.set_metrics({
        'accuracy': 0.95,
        'loss': 0.05,
        'learning_rate': 0.001
    })

    # Metrics with step context
    self.ctx.set_metrics({'mAP': 0.87}, step='validation')
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `value` | `dict` | Yes | Dictionary of metric values |
| `step` | `str \| None` | No | Step name for context |

#### log_message()

Log a user-facing message with context level.

```python
def execute(self):
    self.ctx.log_message('Starting model training...', context='info')
    self.ctx.log_message('GPU memory low, reducing batch size', context='warning')
    self.ctx.log_message('Training completed successfully!', context='success')
    self.ctx.log_message('Failed to load checkpoint', context='danger')
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `message` | `str` | Yes | - | Message content |
| `context` | `str` | No | `'info'` | Message level: `'info'`, `'warning'`, `'success'`, `'danger'` |

#### log_dev_event()

Log development/debug events for plugin developers.

```python
def execute(self):
    # Debug information (not shown to end users by default)
    self.ctx.log_dev_event('Variable state checkpoint', {'variable_x': 42})
    self.ctx.log_dev_event('Processing time recorded', {'duration_ms': 1500})
    self.ctx.log_dev_event('Cache hit rate', {'hits': 95, 'misses': 5})
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | `str` | Yes | Event message |
| `data` | `dict \| None` | No | Optional additional data |

> **Good to know**: Development events are useful for debugging and monitoring but are not displayed to end users by default.

#### end_log()

Signal that plugin execution is complete.

```python
def execute(self):
    try:
        result = process_data()
        return result
    finally:
        self.ctx.end_log()
```

## PluginEnvironment

Environment configuration accessible through `ctx.env`.

```python
def execute(self):
    # Access environment variables
    storage_path = self.ctx.env.storage_path
    api_url = self.ctx.env.api_url

    # Check if running in debug mode
    if self.ctx.env.debug:
        self.ctx.log_dev_event('Debug mode enabled')
```

## Complete Example

```python
from synapse_sdk.plugins.action import BaseAction
from pydantic import BaseModel, Field

class TrainParams(BaseModel):
    epochs: int = Field(default=50, ge=1, le=1000)
    batch_size: int = Field(default=8, ge=1, le=512)
    learning_rate: float = Field(default=0.001)

class TrainAction(BaseAction[TrainParams]):
    action_name = 'train'
    params_model = TrainParams

    def execute(self):
        self.ctx.log_message('Starting training...')

        # Load checkpoint if available
        if self.ctx.checkpoint:
            self.ctx.log('checkpoint_loaded', {
                'category': self.ctx.checkpoint['category'],
                'path': self.ctx.checkpoint['path']
            })

        total_epochs = self.params.epochs
        for epoch in range(total_epochs):
            # Training logic
            loss = train_epoch(self.params.batch_size, self.params.learning_rate)

            # Update progress
            self.ctx.set_progress(epoch + 1, total_epochs, step='training')

            # Log metrics
            self.ctx.set_metrics({
                'epoch': epoch + 1,
                'loss': loss,
                'learning_rate': self.params.learning_rate
            })

            # Debug logging
            self.ctx.log_dev_event('Epoch completed', {
                'epoch': epoch + 1,
                'memory_usage': get_memory_usage()
            })

        self.ctx.log_message('Training completed!', context='success')
        self.ctx.end_log()

        return {'final_loss': loss, 'epochs_trained': total_epochs}
```

## Logger Models

Additional models used by the logging system.

### LogLevel

Log severity levels.

```python
from synapse_sdk.plugins.models.logger import LogLevel

LogLevel.DEBUG    # Development/debug events
LogLevel.INFO     # Standard information
LogLevel.WARNING  # Warnings
LogLevel.ERROR    # Errors
```

### ProgressData

Progress tracking data structure.

| Field | Type | Description |
|-------|------|-------------|
| `current` | `int` | Current progress value |
| `total` | `int` | Total progress value |
| `step` | `str \| None` | Optional step name |

### RunStatus

Execution status values.

```python
from synapse_sdk.plugins.models import RunStatus

RunStatus.PENDING     # Waiting to start
RunStatus.RUNNING     # Currently executing
RunStatus.COMPLETED   # Successfully finished
RunStatus.FAILED      # Execution failed
RunStatus.CANCELLED   # Execution cancelled
```

### ActionStatus

Individual action status within a pipeline.

```python
from synapse_sdk.plugins.models import ActionStatus

ActionStatus.PENDING
ActionStatus.RUNNING
ActionStatus.COMPLETED
ActionStatus.FAILED
ActionStatus.SKIPPED
```

## Related

- [Plugin Utilities](./utils.md) - Configuration and discovery utilities
- [Plugin Categories](./categories.md) - Available plugin categories
- [Plugin Development](../../plugins/plugin-development.md) - Complete development guide
