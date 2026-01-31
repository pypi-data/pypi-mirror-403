---
id: export-actions
title: Export Actions
sidebar_position: 3
---

# Export Actions

Export actions transform annotation data into various formats for external use. Use `BaseExportAction` to build custom exporters that convert assignments, ground truth datasets, or tasks into formats like COCO, YOLO, or custom schemas.

## Overview

Export actions provide a structured way to:

- Query filtered annotation results from the backend
- Transform data into target formats (COCO, YOLO, Pascal VOC, CSV, etc.)
- Track export progress with built-in progress reporting
- Handle large datasets efficiently using generators

### At a Glance

| Property          | Value                   |
| ----------------- | ----------------------- |
| Base Class        | `BaseExportAction[P]`   |
| Category          | `PluginCategory.EXPORT` |
| Progress Category | `DATASET_CONVERSION`    |
| Context           | `ExportContext`         |
| Execution Modes   | Simple / Step-Based     |

## BaseExportAction

`BaseExportAction` extends `BaseAction` with export-specific functionality. It provides backend client access and progress tracking out of the box.

```python filename="synapse_sdk/plugins/actions/export/action.py"
from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.enums import PluginCategory

class BaseExportAction(BaseAction[P]):
    category = PluginCategory.EXPORT
```

The generic type `P` represents your params model, which must inherit from `BaseModel`.

### Progress Categories

Export actions support standardized progress tracking:

| Category           | Constant             | Description                                   |
| ------------------ | -------------------- | --------------------------------------------- |
| Dataset Conversion | `DATASET_CONVERSION` | Data transformation and file generation phase |

```python filename="example.py"
# Track conversion progress
self.set_progress(current, total, self.progress.DATASET_CONVERSION)
```

## Key Methods

### `client` Property

Access the backend client for API calls. Raises `RuntimeError` if no client exists in the context.

```python filename="example.py"
# Access backend client
assignments = self.client.get_assignments(filters)
```

> **Good to know**: If you don't need the backend client, override `get_filtered_results()` to fetch data from alternative sources.

### `get_filtered_results()`

Override this abstract method to fetch data for export. Returns a tuple of `(results_iterator, total_count)`.

```python filename="example.py"
def get_filtered_results(self, filters: dict[str, Any]) -> tuple[Any, int]:
    """Fetch filtered results for export.

    Args:
        filters: Filter criteria dict.

    Returns:
        Tuple of (results_iterator, total_count).
    """
    return self.client.get_assignments(filters)
```

### `setup_steps()`

Register workflow steps for step-based execution. If steps are registered, step-based execution takes precedence over `execute()`.

```python filename="example.py"
def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
    registry.register(FetchDataStep())
    registry.register(ConvertFormatStep())
    registry.register(SaveOutputStep())
```

### `create_context()`

Create the export context for step-based workflows. Override to customize context initialization.

```python filename="example.py"
def create_context(self) -> ExportContext:
    params_dict = self.params.model_dump()
    return ExportContext(
        runtime_ctx=self.ctx,
        params=params_dict,
    )
```

## ExportContext

`ExportContext` carries shared state between workflow steps. It extends `BaseStepContext` with export-specific fields.

```python filename="synapse_sdk/plugins/actions/export/context.py"
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.steps import BaseStepContext

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient

@dataclass
class ExportContext(BaseStepContext):
    # Input parameters
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    results: Any | None = None
    total_count: int = 0
    exported_count: int = 0
    output_path: str | None = None

    @property
    def client(self) -> BackendClient:
        """Backend client from runtime context."""
        if self.runtime_ctx.client is None:
            raise RuntimeError('No client in runtime context')
        return self.runtime_ctx.client
```

### Fields

| Field            | Type             | Description                       |
| ---------------- | ---------------- | --------------------------------- |
| `params`         | `dict[str, Any]` | Export parameters from action     |
| `results`        | `Any \| None`    | Fetched data (populated by steps) |
| `total_count`    | `int`            | Total items to export             |
| `exported_count` | `int`            | Successfully exported items       |
| `output_path`    | `str \| None`    | Output file/directory path        |

### Properties

| Property | Type            | Description                                                              |
| -------- | --------------- | ------------------------------------------------------------------------ |
| `client` | `BackendClient` | Backend client from runtime context. Raises `RuntimeError` if no client. |

### Inherited Fields

From `BaseStepContext`:

| Field          | Type               | Description                              |
| -------------- | ------------------ | ---------------------------------------- |
| `runtime_ctx`  | `RuntimeContext`   | Runtime context with logger, client, env |
| `step_results` | `list[StepResult]` | Results from completed steps             |
| `errors`       | `list[str]`        | Accumulated error messages               |
| `current_step` | `str \| None`      | Currently executing step name            |

### StepResult

`StepResult` is a dataclass representing the result of a workflow step execution.

```python filename="synapse_sdk/plugins/steps/base.py"
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class StepResult:
    success: bool = True
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    rollback_data: dict[str, Any] = field(default_factory=dict)
    skipped: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
```

| Field           | Type             | Description                                               |
| --------------- | ---------------- | --------------------------------------------------------- |
| `success`       | `bool`           | Whether the step completed successfully (default: `True`) |
| `data`          | `dict[str, Any]` | Output data from the step                                 |
| `error`         | `str \| None`    | Error message if step failed                              |
| `rollback_data` | `dict[str, Any]` | Data needed for rollback on failure                       |
| `skipped`       | `bool`           | Whether the step was skipped (default: `False`)           |
| `timestamp`     | `datetime`       | When the step completed                                   |

## Execution Modes

Choose between two execution modes based on complexity.

### Simple Mode

Override `execute()` directly for straightforward export logic.

```python filename="plugins/export/simple_exporter.py"
from typing import Any

from pydantic import BaseModel
from synapse_sdk.plugins.actions.export import BaseExportAction

class ExportParams(BaseModel):
    project_id: int
    output_format: str = "coco"

class SimpleExportAction(BaseExportAction[ExportParams]):
    action_name = "simple_export"
    params_model = ExportParams

    def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
        return self.client.get_assignments(filters)

    def execute(self) -> dict[str, Any]:
        # Fetch data
        results, total = self.get_filtered_results({
            "project": self.params.project_id
        })

        # Initialize progress
        self.set_progress(0, total, self.progress.DATASET_CONVERSION)

        # Process items
        exported = []
        for i, item in enumerate(results, 1):
            exported.append(self._convert_item(item))
            self.set_progress(i, total, self.progress.DATASET_CONVERSION)

        return {
            "format": self.params.output_format,
            "exported_count": len(exported),
            "data": exported
        }

    def _convert_item(self, item: dict) -> dict:
        # Conversion logic here
        return item
```

> **Tip**: Use Simple Mode when your export logic fits in a single method without complex error recovery needs.

### Step-Based Mode

Use `setup_steps()` for complex workflows with multiple phases, progress tracking, and automatic rollback on failure.

```python filename="plugins/export/step_exporter.py"
from pathlib import Path

from synapse_sdk.plugins.actions.export import BaseExportAction, ExportContext
from synapse_sdk.plugins.steps import BaseStep, StepResult, StepRegistry

# Define workflow steps
class FetchDataStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "fetch_data"

    @property
    def progress_weight(self) -> float:
        return 0.2  # 20% of total progress

    def execute(self, context: ExportContext) -> StepResult:
        filters = context.params.get("filters", {})
        context.results, context.total_count = context.client.get_assignments(filters)
        return StepResult(success=True)

class ConvertFormatStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "convert_format"

    @property
    def progress_weight(self) -> float:
        return 0.6  # 60% of total progress

    def execute(self, context: ExportContext) -> StepResult:
        converted = []
        for item in context.results:
            converted.append(self._convert(item))
        context.exported_count = len(converted)
        return StepResult(success=True, data={"converted": converted})

    def _convert(self, item: dict) -> dict:
        return item

class SaveOutputStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "save_output"

    @property
    def progress_weight(self) -> float:
        return 0.2  # 20% of total progress

    def execute(self, context: ExportContext) -> StepResult:
        context.output_path = "/tmp/export_output.json"
        return StepResult(success=True)

    def rollback(self, context: ExportContext, result: StepResult) -> None:
        # Clean up output file on failure
        if context.output_path:
            Path(context.output_path).unlink(missing_ok=True)

# Register steps in action
class StepBasedExportAction(BaseExportAction[ExportParams]):
    action_name = "step_export"
    params_model = ExportParams

    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        registry.register(FetchDataStep())
        registry.register(ConvertFormatStep())
        registry.register(SaveOutputStep())
```

**Step-Based Mode Benefits:**

- **Automatic progress**: Progress calculated from step weights
- **Automatic rollback**: On failure, `rollback()` called in reverse order
- **Reusable steps**: Share steps across multiple export actions
- **Testable units**: Test each step independently

## Export Targets

Export actions support three data targets.

### Assignment

Export annotation work (labeling results, reviews, etc.).

```python filename="plugins/export/assignment_exporter.py"
def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    return self.client.get_assignments(filters)
```

### Ground Truth

Export curated ground truth datasets for ML training.

```python filename="plugins/export/ground_truth_exporter.py"
def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    events = self.client.list_ground_truth_events(
        params=filters,
        list_all=True
    )
    return events, len(events)
```

### Task

Export task metadata and configurations.

```python filename="plugins/export/task_exporter.py"
def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    return self.client.get_tasks(filters)
```

## Examples

### Example: COCO Format Exporter

A complete example exporting annotations to COCO format.

```python filename="plugins/export/coco_exporter.py"
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.export import BaseExportAction
from typing import Any

class CocoExportParams(BaseModel):
    project_id: int = Field(..., description="Project ID to export")
    include_images: bool = Field(True, description="Include image metadata")

class CocoExportAction(BaseExportAction[CocoExportParams]):
    action_name = "coco_export"
    params_model = CocoExportParams

    def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
        return self.client.get_assignments(filters)

    def execute(self) -> dict[str, Any]:
        results, total = self.get_filtered_results({
            "project": self.params.project_id
        })

        self.set_progress(0, total, self.progress.DATASET_CONVERSION)

        coco_data = {
            "info": {"description": "Exported from Synapse"},
            "images": [],
            "annotations": [],
            "categories": []
        }

        annotation_id = 0
        category_map = {}

        for i, assignment in enumerate(results, 1):
            # Add image
            data_unit = assignment.get("data_unit", {})
            image_id = data_unit.get("id")

            if self.params.include_images:
                coco_data["images"].append({
                    "id": image_id,
                    "file_name": data_unit.get("name", ""),
                    "width": data_unit.get("width", 0),
                    "height": data_unit.get("height", 0)
                })

            # Add annotations
            for ann in assignment.get("data", {}).get("annotations", []):
                category = ann.get("category", "default")
                if category not in category_map:
                    cat_id = len(category_map)
                    category_map[category] = cat_id
                    coco_data["categories"].append({
                        "id": cat_id,
                        "name": category
                    })

                coco_data["annotations"].append({
                    "id": annotation_id,
                    "image_id": image_id,
                    "category_id": category_map[category],
                    "bbox": ann.get("bbox", []),
                    "area": ann.get("area", 0),
                    "iscrowd": 0
                })
                annotation_id += 1

            self.set_progress(i, total, self.progress.DATASET_CONVERSION)

        return {
            "format": "coco",
            "exported_count": len(coco_data["images"]),
            "annotation_count": len(coco_data["annotations"]),
            "data": coco_data
        }
```

### Example: Multi-Format Exporter with Steps

A flexible exporter supporting multiple output formats.

```python filename="plugins/export/multi_format_exporter.py"
from enum import Enum
from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.export import BaseExportAction, ExportContext
from synapse_sdk.plugins.steps import BaseStep, StepResult, StepRegistry

class OutputFormat(str, Enum):
    COCO = "coco"
    YOLO = "yolo"
    CSV = "csv"

class MultiFormatParams(BaseModel):
    project_id: int
    output_format: OutputFormat = OutputFormat.COCO
    output_dir: str = Field("/tmp/export", description="Output directory")

class FetchStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "fetch"

    @property
    def progress_weight(self) -> float:
        return 0.3

    def execute(self, context: ExportContext) -> StepResult:
        project_id = context.params["project_id"]
        context.results, context.total_count = context.client.get_assignments({
            "project": project_id
        })
        return StepResult(success=True)

class ConvertStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "convert"

    @property
    def progress_weight(self) -> float:
        return 0.5

    def execute(self, context: ExportContext) -> StepResult:
        output_format = context.params["output_format"]

        if output_format == OutputFormat.COCO:
            converted = self._to_coco(context.results)
        elif output_format == OutputFormat.YOLO:
            converted = self._to_yolo(context.results)
        else:
            converted = self._to_csv(context.results)

        context.exported_count = context.total_count
        return StepResult(success=True, data={"output": converted})

    def _to_coco(self, results) -> dict:
        # COCO conversion logic
        return {"format": "coco", "images": [], "annotations": []}

    def _to_yolo(self, results) -> list:
        # YOLO conversion logic
        return []

    def _to_csv(self, results) -> str:
        # CSV conversion logic
        return "id,label,x,y,width,height\n"

class SaveStep(BaseStep[ExportContext]):
    @property
    def name(self) -> str:
        return "save"

    @property
    def progress_weight(self) -> float:
        return 0.2

    def execute(self, context: ExportContext) -> StepResult:
        from pathlib import Path
        import json

        output_dir = Path(context.params["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        output_format = context.params["output_format"]
        output_data = context.step_results[-1].data["output"]

        if output_format in (OutputFormat.COCO,):
            output_path = output_dir / "annotations.json"
            output_path.write_text(json.dumps(output_data, indent=2))
        else:
            output_path = output_dir / f"output.{output_format}"
            output_path.write_text(str(output_data))

        context.output_path = str(output_path)
        return StepResult(success=True)

class MultiFormatExportAction(BaseExportAction[MultiFormatParams]):
    action_name = "multi_format_export"
    params_model = MultiFormatParams

    def setup_steps(self, registry: StepRegistry[ExportContext]) -> None:
        registry.register(FetchStep())
        registry.register(ConvertStep())
        registry.register(SaveStep())
```

## Best Practices

### Memory-Efficient Processing

Use generators for large datasets to avoid loading everything into memory.

```python filename="example.py"
def get_filtered_results(self, filters: dict) -> tuple[Any, int]:
    # Return a generator, not a list
    results = self.client.get_assignments_stream(filters)
    count = self.client.count_assignments(filters)
    return results, count

def execute(self) -> dict[str, Any]:
    results, total = self.get_filtered_results(self.params.filters)

    for i, item in enumerate(results, 1):  # Iterate without loading all
        self._process_item(item)
        self.set_progress(i, total, self.progress.DATASET_CONVERSION)
```

### Progress Reporting

Report progress at meaningful intervals, not on every item.

```python filename="example.py"
def execute(self) -> dict[str, Any]:
    results, total = self.get_filtered_results(filters)
    report_interval = max(1, total // 100)  # Report every 1%

    for i, item in enumerate(results, 1):
        self._process(item)
        if i % report_interval == 0 or i == total:
            self.set_progress(i, total, self.progress.DATASET_CONVERSION)
```

### Error Recovery

Handle partial failures gracefully in step-based workflows.

```python filename="example.py"
class ConvertStep(BaseStep[ExportContext]):
    def execute(self, context: ExportContext) -> StepResult:
        converted = []
        errors = []

        for item in context.results:
            try:
                converted.append(self._convert(item))
            except ValueError as e:
                errors.append(f"Item {item['id']}: {e}")

        context.exported_count = len(converted)

        if errors:
            context.errors.extend(errors)
            # Continue with partial results
            return StepResult(
                success=True,
                data={"converted": converted, "errors": errors}
            )

        return StepResult(success=True, data={"converted": converted})
```

> **Warning**: Always validate output format compliance before returning results. Invalid exports can cause downstream failures in ML pipelines.

## Template-Based Export with BaseExporter

For plugin developers who want a simpler, template-based approach to building exporters, `BaseExporter` provides a familiar interface with pre-built file handling utilities.

### Overview

`BaseExporter` is designed for export plugins that need:

- Original file downloading and saving
- JSON data export with error tracking
- Progress and metrics reporting
- Customizable data conversion pipeline

### BaseExporter Class

```python filename="synapse_sdk/plugins/actions/export/exporter.py"
from synapse_sdk.plugins.actions.export import BaseExporter

class BaseExporter:
    def __init__(
        self,
        ctx: RuntimeContext,
        export_items: Generator,
        path_root: Path,
        **params
    ):
        self.ctx = ctx
        self.export_items = export_items
        self.path_root = Path(path_root)
        self.params = params
        self.run = ExporterRunAdapter(ctx.logger)  # Legacy compatibility
```

### Template Methods

Override these methods to customize export behavior:

| Method                                              | Description                        |
| --------------------------------------------------- | ---------------------------------- |
| `convert_data(data)`                                | Transform data during export       |
| `before_convert(data)`                              | Pre-process data before conversion |
| `after_convert(data)`                               | Post-process data after conversion |
| `save_original_file(result, base_path, error_list)` | Save original files                |
| `save_as_json(result, base_path, error_list)`       | Save data as JSON                  |
| `setup_output_directories(path, save_original)`     | Customize directory structure      |
| `process_file_saving(...)`                          | Custom file saving logic           |
| `additional_file_saving(path)`                      | Post-export file operations        |

### ExporterRunAdapter

The `run` attribute provides logging and progress tracking methods:

```python filename="example.py"
# Log messages
self.run.log_message("Processing item...")

# Track progress
self.run.set_progress(current, total, category="dataset_conversion")

# Log metrics
record = self.run.MetricsRecord(stand_by=100, success=0, failed=0)
self.run.log_metrics(record, category="original_file")

# Log file export status
self.run.export_log_original_file(item_id, file_info, ExportStatus.SUCCESS, "")
self.run.export_log_data_file(item_id, file_info, ExportStatus.SUCCESS, "")
```

### MetricsRecord

Track export progress with `MetricsRecord`:

```python filename="example.py"
from synapse_sdk.plugins.actions.export import MetricsRecord

record = MetricsRecord(stand_by=100, success=0, failed=0)

# Update as items are processed
record.stand_by -= 1
record.success += 1

# Log metrics
self.run.log_metrics(record, category="data_file")

# Convert to dict
print(record.to_dict())  # {'stand_by': 99, 'success': 1, 'failed': 0}
```

### ExportStatus Enum

Track file export status:

```python filename="example.py"
from synapse_sdk.plugins.actions.export import ExportStatus

ExportStatus.SUCCESS   # 'success'
ExportStatus.FAILED    # 'failed'
ExportStatus.STAND_BY  # 'stand_by'
```

### Example: Custom Exporter Plugin

A complete example using `BaseExporter` with `ExportAction`:

```python filename="plugins/export/custom_exporter.py"
from pathlib import Path
from typing import Any, Generator

from synapse_sdk.plugins.actions.export import BaseExporter, ExportAction

class MyExporter(BaseExporter):
    """Custom exporter with data transformation."""

    def convert_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Transform annotation data to custom format."""
        return {
            "id": data.get("id"),
            "filename": data.get("files", {}).get("file_name_original"),
            "annotations": self._transform_annotations(data.get("data", {}))
        }

    def _transform_annotations(self, data: dict) -> list:
        # Custom transformation logic
        return data.get("annotations", [])

    def additional_file_saving(self, unique_export_path: Path) -> None:
        """Save metadata file after export."""
        import json
        metadata = {
            "export_name": self.params.get("name"),
            "total_items": self.params.get("count"),
            "format_version": "1.0"
        }
        with (unique_export_path / "metadata.json").open("w") as f:
            json.dump(metadata, f, indent=2)


class MyExportAction(ExportAction):
    """Export action using custom exporter."""

    action_name = "my_export"

    @property
    def entrypoint(self):
        return MyExporter
```

### Plugin Configuration

Configure the action in `config.yaml`:

```yaml filename="config.yaml"
name: my_export_plugin
code: my_export_plugin
version: 1.0.0
category: export

actions:
  export:
    entrypoint: plugin.export.MyExportAction
    annotation_types:
      - image
      - video
```

### Running Locally

Test your export plugin:

```bash
synapse plugin run --mode local export --params '{
  "storage": 1,
  "name": "My Export",
  "save_original_file": true,
  "path": "exports/my-export",
  "target": "task",
  "filter": {"project": 123},
  "extra_params": {}
}'
```

## Target Handlers

`ExportAction` uses target handlers to fetch data from different sources.

### TargetHandlerFactory

```python filename="synapse_sdk/plugins/actions/export/handlers.py"
from synapse_sdk.plugins.actions.export import TargetHandlerFactory

# Get handler for target type
handler = TargetHandlerFactory.get_handler("assignment")
handler = TargetHandlerFactory.get_handler("ground_truth")
handler = TargetHandlerFactory.get_handler("task")
```

### Available Handlers

| Handler                          | Target         | Description                   |
| -------------------------------- | -------------- | ----------------------------- |
| `AssignmentExportTargetHandler`  | `assignment`   | Export annotation assignments |
| `GroundTruthExportTargetHandler` | `ground_truth` | Export ground truth datasets  |
| `TaskExportTargetHandler`        | `task`         | Export task data              |

### Custom Target Handler

Implement `ExportTargetHandler` for custom data sources:

```python filename="example.py"
from synapse_sdk.plugins.actions.export import ExportTargetHandler

class CustomTargetHandler(ExportTargetHandler):
    def get_results(self, client, filters: dict) -> tuple[Any, int]:
        # Fetch data from custom source
        results = client.custom_api_call(filters)
        return iter(results), len(results)

    def validate_filter(self, filters: dict, client) -> dict:
        # Validate filter parameters
        if "required_field" not in filters:
            raise ValueError("required_field is required")
        return filters

    def get_export_item(self, results) -> Generator:
        # Transform results for export
        for item in results:
            yield self._transform(item)
```

## Related

- [Defining Actions](/plugins/defining-actions) - Action definition basics
- [RuntimeContext](/plugins/runtime-context) - Context API reference
- [Steps Workflow](/plugins/steps-workflow) - Step-based workflow guide
- [Dataset Conversion](/plugins/dataset-conversion) - Format conversion utilities
