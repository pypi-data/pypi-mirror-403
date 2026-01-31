---
id: pre-annotation-actions
title: Pre-Annotation Actions
sidebar_position: 6
---

# Pre-Annotation Actions

Pre-annotation actions prepare task data before human annotation. Use `AddTaskDataAction` to add or transform task data with either file-based inputs or inference outputs.

## Overview

`AddTaskDataAction` handles:

- Task discovery with filters
- Data collection and file specification validation
- File-based annotation ingestion
- Inference-based annotation via pre-processor plugins
- Progress and metrics tracking

## AddTaskDataAction

### Subclassing

Override the conversion hooks to map your data format into task data.

```python filename="plugins/my_plugin/add_task_data.py"
from synapse_sdk.plugins.actions.add_task_data import AddTaskDataAction


class AddTaskData(AddTaskDataAction):
    action_name = 'add_task_data'

    def convert_data_from_file(self, primary_file_url, primary_file_name, data_file_url, data_file_name, task_data=None):
        # TODO: Parse data_file_url and return task data payload.
        return {}

    def convert_data_from_inference(self, inference_data, task_data=None):
        # TODO: Convert inference output to task data payload.
        return inference_data
```

### Conversion Methods

Override these methods to transform your data into task data format:

| Method | Description | Parameters | Returns |
|--------|-------------|------------|---------|
| `convert_data_from_file()` | Parse file-based annotation data | `primary_file_url`, `primary_file_name`, `data_file_url`, `data_file_name`, `task_data` (optional) | `dict[str, Any]` - Task data payload |
| `convert_data_from_inference()` | Convert inference output to task data | `inference_data`, `task_data` (optional) | `dict[str, Any]` - Task data payload |

Both methods receive an optional `task_data` parameter containing the full task payload for additional context.

### Config.yaml

Define the action entrypoint in your plugin `config.yaml`:

```yaml
actions:
  add_task_data:
    entrypoint: plugin.add_task_data.AddTaskData
    method: job
```

### Parameters

The base params model supports both file and inference workflows:

- `name`: Action job name (required)
- `description`: Optional description for the action job
- `project`: Project ID
- `agent`: Agent ID
- `task_filters`: Task query filters (optional, default: `{}`)
- `method`: Annotation method - `file` or `inference` (default: `file`)
- `target_specification_name`: File spec name (required for file method)
- `pre_processor`: Pre-processor release ID (required for inference method)
- `model`: Model ID (required for inference method)
- `pre_processor_params`: Extra parameters for inference (optional, default: `{}`)

### Result

The action returns an `AddTaskDataResult` with the following fields:

- `status`: Job completion status (`SUCCEEDED`, `FAILED`, etc.)
- `message`: Summary message describing the outcome
- `total_tasks`: Total number of tasks processed
- `success_count`: Number of successfully annotated tasks
- `failed_count`: Number of tasks that failed to annotate
- `failures`: List of failure records, each containing:
  - `task_id`: ID of the failed task
  - `error`: Error message describing what went wrong
