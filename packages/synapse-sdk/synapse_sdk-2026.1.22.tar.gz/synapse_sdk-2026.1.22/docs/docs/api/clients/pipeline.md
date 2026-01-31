---
id: pipeline
title: PipelineServiceClient
sidebar_position: 8
---

# PipelineServiceClient

Client for the Pipeline Service API. Manages pipelines, runs, progress tracking, checkpoints, and logs.

## Overview

The `PipelineServiceClient` communicates with the pipeline orchestration backend for:

- Creating and managing pipeline definitions
- Creating and monitoring pipeline runs
- Real-time progress reporting and streaming
- Checkpoint management for fault tolerance
- Log collection and retrieval

```python
from synapse_sdk.clients.pipeline import PipelineServiceClient

client = PipelineServiceClient("http://localhost:8100")
```

## Initialization

```python
client = PipelineServiceClient(
    base_url="http://localhost:8100",  # Pipeline service URL
    timeout=30.0,                       # Request timeout in seconds
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `"http://localhost:8100"` | Pipeline service base URL |
| `timeout` | `float` | `30.0` | Request timeout in seconds |

## Context Manager

Use as context manager for automatic cleanup:

```python
with PipelineServiceClient("http://localhost:8100") as client:
    pipeline = client.create_pipeline(...)
    run = client.create_run(pipeline["id"])
```

## Pipeline Management

### create_pipeline()

Create a new pipeline definition.

```python
pipeline = client.create_pipeline(
    name="YOLO Training Pipeline",
    actions=[
        {"name": "download", "entrypoint": "plugin.download.DownloadAction"},
        {"name": "convert", "entrypoint": "plugin.convert.ConvertAction"},
        {"name": "train", "entrypoint": "plugin.train.TrainAction"},
    ],
    description="End-to-end YOLO training pipeline",
)

print(f"Created pipeline: {pipeline['id']}")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | `str` | Yes | Pipeline name |
| `actions` | `list[dict]` | Yes | List of action definitions |
| `description` | `str` | No | Pipeline description |

### get_pipeline()

Get pipeline details by ID.

```python
pipeline = client.get_pipeline("pipeline-123")
```

### list_pipelines()

List all pipelines with pagination.

```python
pipelines = client.list_pipelines(skip=0, limit=100)
for p in pipelines:
    print(f"{p['id']}: {p['name']}")
```

### delete_pipeline()

Delete a pipeline.

```python
client.delete_pipeline("pipeline-123")
```

## Run Management

### create_run()

Create a new run for a pipeline.

```python
run = client.create_run(
    pipeline_id="pipeline-123",
    params={"dataset": 456, "epochs": 100},
    work_dir="/workspace/run-001",
)

print(f"Run ID: {run['id']}")
print(f"Status: {run['status']}")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pipeline_id` | `str` | Yes | Pipeline to run |
| `params` | `dict` | No | Initial parameters |
| `work_dir` | `str` | No | Working directory path |

### get_run()

Get run details by ID.

```python
run = client.get_run("run-456")
print(f"Status: {run['status']}")
print(f"Progress: {run.get('progress')}")
```

### list_runs()

List runs with optional status filter.

```python
# All runs
runs = client.list_runs()

# Filter by status
running = client.list_runs(status="running")
completed = client.list_runs(status="completed")
```

### update_run()

Update run status or result.

```python
# Mark as completed
client.update_run(
    run_id="run-456",
    status="completed",
    result={"accuracy": 0.95, "model_path": "/models/best.pt"},
)

# Mark as failed
client.update_run(
    run_id="run-456",
    status="failed",
    error="Out of memory during training",
)
```

### delete_run()

Delete a run.

```python
client.delete_run("run-456")
```

## Progress Reporting

### report_progress()

Report progress update for a run.

```python
from synapse_sdk.plugins.models.logger import ActionProgress

# Basic progress update
client.report_progress(
    run_id="run-456",
    current_action="train",
    current_action_index=2,
    status="running",
)

# With detailed action progress
client.report_progress(
    run_id="run-456",
    current_action="train",
    action_progress=ActionProgress(
        name="train",
        status="running",
        progress=50,
        total=100,
        metrics={"loss": 0.25, "accuracy": 0.87},
    ),
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `run_id` | `str` | Run identifier |
| `current_action` | `str` | Name of current action |
| `current_action_index` | `int` | Index of current action |
| `status` | `str` | Overall run status |
| `action_progress` | `ActionProgress \| dict` | Detailed action progress |
| `error` | `str` | Error message if any |

### get_progress()

Get current progress for a run.

```python
from synapse_sdk.plugins.models.logger import PipelineProgress

progress: PipelineProgress = client.get_progress("run-456")

print(f"Status: {progress.status}")
print(f"Current action: {progress.current_action}")

for action in progress.actions:
    print(f"  {action.name}: {action.progress}/{action.total}")
```

### stream_progress()

Stream progress updates via Server-Sent Events (SSE).

```python
# Synchronous streaming
for progress in client.stream_progress("run-456"):
    print(f"Status: {progress.status}")
    print(f"Action: {progress.current_action}")

    if progress.status in ("completed", "failed"):
        break
```

### stream_progress_async()

Async version for streaming progress.

```python
async for progress in client.stream_progress_async("run-456"):
    print(f"Status: {progress.status}")

    if progress.status in ("completed", "failed"):
        break
```

## Checkpoint Management

### create_checkpoint()

Create a checkpoint for fault tolerance.

```python
checkpoint = client.create_checkpoint(
    run_id="run-456",
    action_name="train",
    action_index=2,
    status="completed",
    params_snapshot={"epochs": 100, "batch_size": 16},
    result={"best_accuracy": 0.95},
    artifacts_path="/workspace/checkpoints/epoch_50",
)
```

### get_checkpoints()

Get all checkpoints for a run.

```python
checkpoints = client.get_checkpoints("run-456")
for cp in checkpoints:
    print(f"{cp['action_name']}: {cp['status']}")
```

### get_latest_checkpoint()

Get the most recent checkpoint.

```python
latest = client.get_latest_checkpoint("run-456")
if latest:
    print(f"Resume from: {latest['action_name']}")
```

### get_checkpoint_by_action()

Get checkpoint for a specific action.

```python
checkpoint = client.get_checkpoint_by_action("run-456", "train")
if checkpoint:
    print(f"Train checkpoint: {checkpoint['artifacts_path']}")
```

## Log Management

### append_logs()

Append log entries to a run.

```python
from synapse_sdk.plugins.models.logger import LogEntry, LogLevel

client.append_logs("run-456", [
    LogEntry(message="Starting training", level=LogLevel.INFO, action_name="train"),
    LogEntry(message="Loaded dataset", level=LogLevel.INFO, action_name="train"),
])
```

### get_logs()

Get logs with optional filters.

```python
# All logs
logs = client.get_logs("run-456")

# Filter by action
train_logs = client.get_logs("run-456", action_name="train")

# Filter by level
errors = client.get_logs("run-456", level="error")

# Logs since timestamp
from datetime import datetime, timedelta
recent = client.get_logs(
    "run-456",
    since=datetime.now() - timedelta(hours=1),
)
```

## Health Check

```python
if client.health_check():
    print("Pipeline service is healthy")
else:
    print("Pipeline service is unavailable")
```

## Complete Example

```python
from synapse_sdk.clients.pipeline import PipelineServiceClient
from synapse_sdk.plugins.models.logger import ActionProgress

with PipelineServiceClient("http://localhost:8100") as client:
    # Create pipeline
    pipeline = client.create_pipeline(
        name="Training Pipeline",
        actions=[
            {"name": "download", "entrypoint": "plugin.download.DownloadAction"},
            {"name": "train", "entrypoint": "plugin.train.TrainAction"},
        ],
    )

    # Start run
    run = client.create_run(
        pipeline["id"],
        params={"dataset": 123, "epochs": 50},
    )

    # Monitor progress
    for progress in client.stream_progress(run["id"], timeout=3600):
        print(f"[{progress.status}] {progress.current_action}")

        if progress.current_action:
            for action in progress.actions:
                if action.name == progress.current_action:
                    print(f"  Progress: {action.progress}/{action.total}")

        if progress.status in ("completed", "failed", "cancelled"):
            break

    # Get final result
    final_run = client.get_run(run["id"])
    if final_run["status"] == "completed":
        print(f"Result: {final_run.get('result')}")
    else:
        print(f"Error: {final_run.get('error')}")
```

## Related

- [BackendClient](./backend.md) - Main backend client
- [Plugin Models](../plugins/models.md) - Progress and logging models
- [Pipelines Guide](../../plugins/pipelines.md) - Pipeline development guide
