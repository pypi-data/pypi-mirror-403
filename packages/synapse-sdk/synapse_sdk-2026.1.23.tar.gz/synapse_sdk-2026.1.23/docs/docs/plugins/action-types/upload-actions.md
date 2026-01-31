---
id: upload-actions
title: Upload Actions
sidebar_position: 4
---

# Upload Actions

Upload actions handle file upload workflows with built-in step orchestration, progress tracking, and automatic rollback support.

## Overview

`BaseUploadAction` is a specialized action base class designed for multi-step upload workflows. It enforces a step-based architecture where each phase of the upload process is defined as a separate step.

### At a Glance

| Feature | Description |
|---------|-------------|
| **Step-based** | Must override `setup_steps()` to register workflow steps |
| **Automatic rollback** | On failure, executes `rollback()` on completed steps in reverse order |
| **Progress tracking** | Tracks progress across all steps based on weights |
| **Upload context** | `UploadContext` carries state between steps |

> **Good to know**: Unlike other action types, `BaseUploadAction` requires you to define workflow steps. Direct `execute()` override is not supported.

## BaseUploadAction

```python filename="synapse_sdk/plugins/actions/upload/action.py"
# P = TypeVar('P', bound=BaseModel) - Parameter model type
class BaseUploadAction(BaseAction[P]):
    """Base class for upload actions with workflow step support."""

    category = PluginCategory.UPLOAD

    @property
    def client(self) -> BackendClient:
        """Backend client from runtime context."""
        ...

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        """Register workflow steps. Override this method."""
        pass

    def create_context(self) -> UploadContext:
        """Create upload context for the workflow."""
        ...

    def execute(self) -> dict[str, Any]:
        """Execute the upload workflow. Do not override."""
        ...
```

### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `category` | `PluginCategory` | Defaults to `PluginCategory.UPLOAD` |

### Instance Properties

| Property | Type | Description |
|----------|------|-------------|
| `client` | `BackendClient` | Backend client from runtime context |

### Methods to Override

| Method | Required | Description |
|--------|----------|-------------|
| `setup_steps(registry)` | **Yes** | Register workflow steps to the registry |
| `create_context()` | No | Customize upload context creation |

> **Warning**: Do not override `execute()` directly. The orchestrator calls it internally to run the step workflow.

## UploadContext

`UploadContext` extends `BaseStepContext` with upload-specific state fields. Steps read and write to the context as the workflow progresses.

```python filename="synapse_sdk/plugins/actions/upload/context.py"
@dataclass
class UploadContext(BaseStepContext):
    """Shared context passed between upload workflow steps."""

    # Upload parameters (from action params)
    params: dict[str, Any] = field(default_factory=dict)

    # Processing state (populated by steps)
    storage: Any | None = None
    pathlib_cwd: Any | None = None
    organized_files: list[dict[str, Any]] = field(default_factory=list)
    uploaded_files: list[dict[str, Any]] = field(default_factory=list)
    data_units: list[dict[str, Any]] = field(default_factory=list)
```

### Fields

| Field | Type | Populated By | Description |
|-------|------|--------------|-------------|
| `params` | `dict[str, Any]` | Action | Upload parameters from action params |
| `storage` | `Any \| None` | Init step | Storage configuration |
| `pathlib_cwd` | `Any \| None` | Init step | Working directory path |
| `organized_files` | `list[dict]` | Organize step | Files prepared for upload |
| `uploaded_files` | `list[dict]` | Upload step | Successfully uploaded files |
| `data_units` | `list[dict]` | Generate step | Created data units |

### Inherited from BaseStepContext

| Field | Type | Description |
|-------|------|-------------|
| `runtime_ctx` | `RuntimeContext` | Parent runtime context |
| `step_results` | `list[StepResult]` | Results from each executed step |
| `errors` | `list[str]` | Accumulated error messages |
| `current_step` | `str \| None` | Name of currently executing step |

### Context Methods (Inherited from BaseStepContext)

| Method | Description |
|--------|-------------|
| `log(event, data, file)` | Log an event via runtime context |
| `set_progress(current, total, category)` | Set progress (auto-uses `current_step` if no category) |
| `set_metrics(value: dict, category)` | Set metrics (auto-uses `current_step` if no category) |

### UploadContext Properties

| Property | Type | Description |
|----------|------|-------------|
| `client` | `BackendClient` | Backend client from runtime context (raises `RuntimeError` if not available) |

## Step-Based Workflow

Upload actions must define their workflow through steps. Override `setup_steps()` to register steps in execution order.

### Creating a Step

```python filename="plugin/steps/validate.py"
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.plugins.actions.upload import UploadContext

class ValidateFilesStep(BaseStep[UploadContext]):
    """Validate files before upload."""

    @property
    def name(self) -> str:
        return 'validate'

    @property
    def progress_weight(self) -> float:
        return 0.1  # 10% of total progress

    def execute(self, context: UploadContext) -> StepResult:
        files = context.organized_files
        if not files:
            return StepResult(success=False, error='No files to upload')

        # Validate each file
        for file in files:
            if not self._is_valid(file):
                return StepResult(success=False, error=f"Invalid file: {file['path']}")

        return StepResult(success=True, data={'validated_count': len(files)})

    def _is_valid(self, file: dict) -> bool:
        # Validation logic
        return True
```

### Registering Steps

```python filename="plugin/upload.py"
from pydantic import BaseModel
from synapse_sdk.plugins.actions.upload import BaseUploadAction, UploadContext
from synapse_sdk.plugins.steps import StepRegistry

from .steps import InitStep, ValidateFilesStep, UploadFilesStep, CleanupStep

class UploadParams(BaseModel):
    storage_id: int
    path: str

class MyUploadAction(BaseUploadAction[UploadParams]):
    action_name = 'upload'

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitStep())
        registry.register(ValidateFilesStep())
        registry.register(UploadFilesStep())
        registry.register(CleanupStep())
```

### Step Execution Order

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│    Init    │───▶│  Validate  │───▶│   Upload   │───▶│  Cleanup   │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
     10%               10%               60%               20%
```

The orchestrator executes steps in registration order:
1. **Init**: Initialize storage connection and paths
2. **Validate**: Check files before upload
3. **Upload**: Transfer files to storage
4. **Cleanup**: Post-upload cleanup tasks

## Automatic Rollback

When a step fails, the orchestrator automatically rolls back all previously executed steps in reverse order.

### Implementing Rollback

```python filename="plugin/steps/upload.py"
from synapse_sdk.plugins.steps import BaseStep, StepResult
from synapse_sdk.plugins.actions.upload import UploadContext

class UploadFilesStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'upload'

    @property
    def progress_weight(self) -> float:
        return 0.6

    def execute(self, context: UploadContext) -> StepResult:
        uploaded = []
        for file in context.organized_files:
            result = self._upload_file(file, context)
            uploaded.append(result)
            context.uploaded_files.append(result)

        return StepResult(
            success=True,
            data={'uploaded_count': len(uploaded)},
            rollback_data={'uploaded_files': uploaded},  # Store for rollback
        )

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        """Delete uploaded files on failure."""
        uploaded = result.rollback_data.get('uploaded_files', [])
        for file in uploaded:
            self._delete_file(file, context)

    def _upload_file(self, file: dict, context: UploadContext) -> dict:
        # Upload logic
        return {'path': file['path'], 'storage_id': context.storage}

    def _delete_file(self, file: dict, context: UploadContext) -> None:
        # Delete logic for rollback
        pass
```

### Rollback Flow

```
┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐
│    Init    │───▶│  Validate  │───▶│   Upload   │──X─│  Cleanup   │
│  (success) │    │  (success) │    │  (success) │    │  (failed)  │
└────────────┘    └────────────┘    └────────────┘    └────────────┘
       ▲                 ▲                 ▲
       │                 │                 │
       └─────────────────┴─────────────────┘
                    Rollback
              (reverse order: Upload → Validate → Init)
```

> **Good to know**: Rollback is best-effort. If a rollback fails, the error is logged but other rollbacks continue. Always design rollback logic to be idempotent.

## Complete Example

A full file upload plugin implementation:

```python filename="plugin/upload.py"
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, Field
from synapse_sdk.plugins.actions.upload import BaseUploadAction, UploadContext
from synapse_sdk.plugins.steps import BaseStep, StepRegistry, StepResult

# Parameters
class FileUploadParams(BaseModel):
    storage_id: int = Field(description='Target storage ID')
    source_path: str = Field(description='Local directory path')
    extensions: list[str] = Field(default=['.jpg', '.png'], description='File extensions to upload')

# Steps
class InitializeStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'initialize'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: UploadContext) -> StepResult:
        storage_id = context.params['storage_id']
        storage = context.client.get_storage(storage_id)
        context.storage = storage
        context.pathlib_cwd = Path(context.params['source_path'])
        return StepResult(success=True)

class OrganizeFilesStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'organize'

    @property
    def progress_weight(self) -> float:
        return 0.1

    def execute(self, context: UploadContext) -> StepResult:
        extensions = context.params.get('extensions', ['.jpg', '.png'])
        source_dir = context.pathlib_cwd

        files = []
        for ext in extensions:
            files.extend(source_dir.glob(f'**/*{ext}'))

        context.organized_files = [{'path': str(f), 'name': f.name} for f in files]

        context.log('files_organized', {'count': len(files)})
        return StepResult(success=True, data={'file_count': len(files)})

class UploadFilesStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'upload'

    @property
    def progress_weight(self) -> float:
        return 0.6

    def execute(self, context: UploadContext) -> StepResult:
        files = context.organized_files
        total = len(files)

        for i, file in enumerate(files):
            # Upload file (implementation depends on storage type)
            result = self._upload_to_storage(file, context.storage)
            context.uploaded_files.append(result)

            # Update progress (category auto-inferred from step name)
            context.set_progress(i + 1, total)

        return StepResult(
            success=True,
            data={'uploaded_count': total},
            rollback_data={'files': context.uploaded_files},
        )

    def rollback(self, context: UploadContext, result: StepResult) -> None:
        for file in result.rollback_data.get('files', []):
            self._delete_from_storage(file, context.storage)

    def _upload_to_storage(self, file: dict, storage) -> dict:
        # Upload implementation
        return {'path': file['path'], 'uploaded': True}

    def _delete_from_storage(self, file: dict, storage) -> None:
        # Rollback implementation
        pass

class FinalizeStep(BaseStep[UploadContext]):
    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.2

    def execute(self, context: UploadContext) -> StepResult:
        # Create data units or finalize upload
        for file in context.uploaded_files:
            data_unit = {'file': file['path'], 'status': 'complete'}
            context.data_units.append(data_unit)

        context.log('upload_complete', {
            'uploaded': len(context.uploaded_files),
            'data_units': len(context.data_units),
        })

        return StepResult(success=True)

# Action
class FileUploadAction(BaseUploadAction[FileUploadParams]):
    """Upload files to storage with automatic rollback support."""

    action_name = 'upload'

    def setup_steps(self, registry: StepRegistry[UploadContext]) -> None:
        registry.register(InitializeStep())
        registry.register(OrganizeFilesStep())
        registry.register(UploadFilesStep())
        registry.register(FinalizeStep())
```

## Best Practices

### Step Design

- **Keep steps focused**: Each step should have a single responsibility
- **Set appropriate weights**: `progress_weight` should reflect actual execution time
- **Implement rollback**: Always implement `rollback()` for steps that modify state

### Large File Handling

```python filename="plugin/steps/upload.py"
def execute(self, context: UploadContext) -> StepResult:
    files = context.organized_files

    for i, file in enumerate(files):
        # Use chunked upload for large files
        if file['size'] > 100_000_000:  # 100MB
            self._chunked_upload(file, context)
        else:
            self._simple_upload(file, context)

        context.set_progress(i + 1, len(files))

    return StepResult(success=True)
```

### Retry Logic

```python filename="plugin/steps/upload.py"
from tenacity import retry, stop_after_attempt, wait_exponential

class UploadFilesStep(BaseStep[UploadContext]):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
    )
    def _upload_file(self, file: dict, storage) -> dict:
        # Upload with automatic retry on failure
        return storage.upload(file['path'])
```

### Conditional Steps

```python filename="plugin/steps/validate.py"
class ValidateStep(BaseStep[UploadContext]):
    def can_skip(self, context: UploadContext) -> bool:
        """Skip validation if skip_validation is set."""
        return context.params.get('skip_validation', False)

    def execute(self, context: UploadContext) -> StepResult:
        # Validation logic
        return StepResult(success=True)
```

## Related

- [Steps & Workflow](/plugins/steps-workflow) - Step infrastructure details
- [Defining Actions](/plugins/defining-actions) - Action definition patterns
- [RuntimeContext](/plugins/runtime-context) - Context API reference
