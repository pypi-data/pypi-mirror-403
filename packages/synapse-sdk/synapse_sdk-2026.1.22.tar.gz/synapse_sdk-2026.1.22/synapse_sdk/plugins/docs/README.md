# Plugin System Developer Guide

Quick reference and extension guide for the Synapse SDK Plugin System.

## Documentation Index

| Document | Description | When to Read |
|----------|-------------|--------------|
| **[OVERVIEW.md](OVERVIEW.md)** | Introduction, key concepts, tutorials | Start here for new developers |
| **[PLUGIN_STRUCTURE_GUIDE.md](PLUGIN_STRUCTURE_GUIDE.md)** | Complete plugin structure with step orchestration | Setting up a new plugin project |
| **[ACTION_DEV_GUIDE.md](ACTION_DEV_GUIDE.md)** | Action development, async patterns | Building custom actions |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Technical architecture, component details | Deep dive into internals |
| **[STEP.md](STEP.md)** | Step implementations, orchestration | Building step-based workflows |
| **[LOGGING_SYSTEM.md](LOGGING_SYSTEM.md)** | Logging, progress tracking, metrics | Implementing observability |
| **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)** | Multi-action pipeline execution | Building complex workflows |

### Recommended Reading Order

1. **OVERVIEW.md** - Understand concepts, create your first plugin
2. **PLUGIN_STRUCTURE_GUIDE.md** - See complete plugin structure with examples
3. **ACTION_DEV_GUIDE.md** - For developing custom actions
4. **ARCHITECTURE.md** - Learn component details as needed
5. **STEP.md** - For step-based workflows within actions
6. **LOGGING_SYSTEM.md** - For progress tracking and logging
7. **PIPELINE_GUIDE.md** - For multi-action workflows

---

## Quick Reference

### Module Reference

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `synapse_sdk.plugins` | Main API | `BaseAction`, `run_plugin`, `action` |
| `synapse_sdk.plugins.actions` | Action registry | `ActionRegistry`, `ActionSpec`, `ActionType` |
| `synapse_sdk.plugins.actions.dataset` | Dataset operations | `DatasetAction`, `DatasetOperation` |
| `synapse_sdk.plugins.actions.train` | Training workflows | `BaseTrainAction`, `TrainContext` |
| `synapse_sdk.plugins.actions.export` | Export workflows | `BaseExportAction`, `DefaultExportAction`, `ExportContext` (6 built-in steps) |
| `synapse_sdk.plugins.actions.upload` | Upload workflows | `BaseUploadAction`, `UploadContext` (7 built-in steps) |
| `synapse_sdk.plugins.actions.add_task_data` | Pre-annotation | `AddTaskDataAction`, `AddTaskDataMethod` |
| `synapse_sdk.plugins.actions.inference` | Inference/deployment | `BaseInferenceAction`, `BaseDeploymentAction`, `BaseServeDeployment` |
| `synapse_sdk.plugins.context` | Runtime services | `RuntimeContext`, `PluginEnvironment` |
| `synapse_sdk.plugins.steps` | Workflow steps | `BaseStep`, `StepRegistry`, `Orchestrator` |
| `synapse_sdk.loggers` | Logging system | `BaseLogger`, `ConsoleLogger`, `BackendLogger` |
| `synapse_sdk.plugins.models.logger` | Logger models | `LogLevel`, `ActionProgress`, `PipelineProgress` |
| `synapse_sdk.plugins.executors` | Execution backends | `LocalExecutor` |
| `synapse_sdk.plugins.executors.ray` | Ray execution | `RayActorExecutor`, `RayJobExecutor`, `RayJobsApiExecutor` |
| `synapse_sdk.plugins.pipelines` | Multi-action | `ActionPipeline`, `PipelineProgress` |
| `synapse_sdk.plugins.enums` | Enumerations | `PluginCategory`, `RunMethod` |
| `synapse_sdk.plugins.types` | Semantic types | `DataType`, `YOLODataset`, `ModelWeights` |
| `synapse_sdk.plugins.schemas` | Result schemas | `TrainResult`, `InferenceResult`, `UploadResult` |
| `synapse_sdk.utils.converters` | Format converters | `FromDMConverter`, `ToDMConverter`, `get_converter` |
| `synapse_sdk.plugins.config` | Configuration | `PluginConfig`, `ActionConfig` |
| `synapse_sdk.plugins.discovery` | Plugin loading | `PluginDiscovery` |
| `synapse_sdk.plugins.errors` | Exceptions | `PluginError`, `ValidationError` |

### Common Imports

```python
# Basic action development
from synapse_sdk.plugins import BaseAction, run_plugin
# Note: 'action' decorator is deprecated, use BaseAction instead
from synapse_sdk.plugins.context import RuntimeContext
from synapse_sdk.plugins.enums import PluginCategory

# Step-based workflows
from synapse_sdk.plugins.steps import (
    BaseStep,
    StepResult,
    BaseStepContext,
    StepRegistry,
    Orchestrator,
)

# Specialized actions
from synapse_sdk.plugins.actions.dataset import DatasetAction, DatasetOperation
from synapse_sdk.plugins.actions.train import BaseTrainAction, TrainContext
from synapse_sdk.plugins.actions.export import BaseExportAction, DefaultExportAction, ExportContext
from synapse_sdk.plugins.actions.upload import BaseUploadAction, UploadContext
from synapse_sdk.plugins.actions.add_task_data import AddTaskDataAction, AddTaskDataMethod
from synapse_sdk.plugins.actions.inference import (
    BaseInferenceAction,
    BaseDeploymentAction,
    BaseServeDeployment,
)

# Executors
from synapse_sdk.plugins.executors import LocalExecutor
from synapse_sdk.plugins.executors.ray import (
    RayActorExecutor,
    RayJobExecutor,
    RayJobsApiExecutor,
)

# Action Registry
from synapse_sdk.plugins.actions import ActionRegistry, ActionSpec, ActionType

# Types and Schemas
from synapse_sdk.plugins.types import DataType, YOLODataset, ModelWeights
from synapse_sdk.plugins.schemas import TrainResult, InferenceResult, UploadResult

# Dataset Converters
from synapse_sdk.utils.converters import get_converter, FromDMConverter, ToDMConverter

# Logging
from synapse_sdk.loggers import BaseLogger, ConsoleLogger, BackendLogger
from synapse_sdk.plugins.models.logger import LogLevel, ActionProgress, PipelineProgress

# Pipelines
from synapse_sdk.plugins.pipelines import ActionPipeline, PipelineProgress

# Discovery
from synapse_sdk.plugins.discovery import PluginDiscovery
```

### Common Patterns

| Pattern | When to Use | Example |
|---------|-------------|---------|
| Class-based action | Complex actions, type declarations | `class MyAction(BaseAction[Params])` |
| Function action | Simple, stateless operations | `@action(params=Params)` |
| Step workflow | Multi-phase with rollback | `BaseStep` + `Orchestrator` |
| Local execution | Development, testing | `mode='local'` |
| Ray task | Light parallel tasks | `mode='task'` |
| Ray job | Production workloads | `mode='job'` |

---

## Extension Points Guide

### Creating Custom Actions

**Checklist:**
- [ ] Define Pydantic params model
- [ ] Create action class or decorated function
- [ ] Implement `execute()` method
- [ ] Add to `config.yaml`
- [ ] Test with `LocalExecutor`

**Template:**

```python
from synapse_sdk.plugins import BaseAction
from synapse_sdk.plugins.enums import PluginCategory
from pydantic import BaseModel, Field

class MyParams(BaseModel):
    """Action parameters."""
    input_path: str = Field(..., description='Input file path')
    output_path: str = Field(..., description='Output file path')
    option: int = Field(default=10, ge=1, le=100)

class MyResult(BaseModel):
    """Action result."""
    status: str
    processed_count: int

class MyAction(BaseAction[MyParams]):
    """My custom action."""

    action_name = 'my_action'
    category = PluginCategory.CUSTOM
    result_model = MyResult

    def execute(self) -> MyResult:
        # Log start
        self.log('start', {'input': self.params.input_path})

        # Process with progress
        total = 100
        for i in range(total):
            self.set_progress(i + 1, total)
            # ... processing ...

        # Return result
        return MyResult(
            status='completed',
            processed_count=total,
        )
```

**Testing:**

```python
from synapse_sdk.plugins.executors import LocalExecutor

executor = LocalExecutor()
result = executor.execute(
    action_cls=MyAction,
    params={'input_path': '/in', 'output_path': '/out'},
)
assert result['status'] == 'completed'
```

### Creating Custom Steps

**Checklist:**
- [ ] Define context class extending `BaseStepContext`
- [ ] Implement step class with `name`, `progress_weight`, `execute()`
- [ ] Optionally implement `can_skip()` and `rollback()`
- [ ] Register steps in `StepRegistry`
- [ ] Execute with `Orchestrator`

**Template:**

```python
from dataclasses import dataclass, field
from synapse_sdk.plugins.steps import (
    BaseStep,
    StepResult,
    BaseStepContext,
    StepRegistry,
    Orchestrator,
)

@dataclass
class MyContext(BaseStepContext):
    """Shared state for my workflow."""
    items: list[str] = field(default_factory=list)
    processed: list[str] = field(default_factory=list)

class LoadStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'load'

    @property
    def progress_weight(self) -> float:
        return 0.2

    def execute(self, context: MyContext) -> StepResult:
        context.items = ['item1', 'item2', 'item3']
        return StepResult(success=True, data={'count': len(context.items)})

class ProcessStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'process'

    @property
    def progress_weight(self) -> float:
        return 0.8

    def execute(self, context: MyContext) -> StepResult:
        for item in context.items:
            context.set_progress(len(context.processed), len(context.items))
            context.processed.append(f"processed_{item}")
        return StepResult(success=True)

    def rollback(self, context: MyContext, result: StepResult) -> None:
        context.processed.clear()

# Usage
registry = StepRegistry[MyContext]()
registry.register(LoadStep())
registry.register(ProcessStep())

context = MyContext(runtime_ctx=runtime_ctx)
orchestrator = Orchestrator(registry, context)
result = orchestrator.execute()
```

### Creating Custom DataTypes

**When needed:**
- Pipeline validation between actions
- Semantic type declarations
- Custom format compatibility

**Template:**

```python
from synapse_sdk.plugins.types import DataType

class MyDataset(DataType):
    """My custom dataset format."""
    name = 'my_dataset'
    format = 'my_format'
    description = 'Custom dataset format for my use case'

class MyModel(DataType):
    """My custom model format."""
    name = 'my_model'
    format = 'my_format'
```

**Usage:**

```python
class MyTrainAction(BaseAction[TrainParams]):
    input_type = MyDataset
    output_type = MyModel
```

### Creating Custom Contexts

**Template:**

```python
from dataclasses import dataclass, field
from synapse_sdk.plugins.steps import BaseStepContext

@dataclass
class MyContext(BaseStepContext):
    """Context for my workflow."""

    # Required fields (no default)
    config_path: str

    # Optional fields (with default)
    items: list[str] = field(default_factory=list)
    processed_count: int = 0
    error_messages: list[str] = field(default_factory=list)

    def add_item(self, item: str) -> None:
        """Helper method for steps."""
        self.items.append(item)
        self.processed_count += 1
```

---

## Best Practices

### Progress Tracking

**Weight Distribution:**
- Assign weights proportional to expected duration
- Total weights should represent relative time spent
- Consider user perception (fast steps feel slower)

```python
# Example: 80% time in training, 10% each for setup/cleanup
class SetupStep(BaseStep):
    progress_weight = 0.1

class TrainStep(BaseStep):
    progress_weight = 0.8

class CleanupStep(BaseStep):
    progress_weight = 0.1
```

**Category Naming:**
- Use descriptive, consistent category names
- Categories appear in UI progress displays

```python
# Good categories
self.set_progress(1, 10, category='dataset_download')
self.set_progress(5, 100, category='model_training')
self.set_progress(1, 1, category='checkpoint_save')

# Avoid generic names
self.set_progress(1, 10, category='step1')  # Not descriptive
```

### Error Handling

**Exception Hierarchy:**

```python
from synapse_sdk.plugins.errors import (
    PluginError,       # Base exception
    ValidationError,   # Parameter validation failed
    ActionNotFoundError,  # Action not in plugin
    ExecutionError,    # Runtime execution failed
)
```

**Best Practices:**

```python
def execute(self) -> dict:
    # Validate early
    if not os.path.exists(self.params.input_path):
        raise ValidationError(f"Input not found: {self.params.input_path}")

    try:
        result = process_data(self.params.input_path)
    except IOError as e:
        # Wrap with context
        raise ExecutionError(f"Failed to process: {e}") from e

    return result
```

**Step Rollback:**

```python
class UploadStep(BaseStep[MyContext]):
    def execute(self, context: MyContext) -> StepResult:
        urls = []
        for file in context.files:
            url = upload(file)
            urls.append(url)

        return StepResult(
            success=True,
            rollback_data={'urls': urls},  # Save for rollback
        )

    def rollback(self, context: MyContext, result: StepResult) -> None:
        # Clean up on failure
        for url in result.rollback_data.get('urls', []):
            try:
                delete(url)
            except Exception as e:
                # Log but don't fail rollback
                context.errors.append(f"Rollback failed: {url}: {e}")
```

### Context Usage

**State Management:**

```python
# Good: Use context fields for state
@dataclass
class ProcessContext(BaseStepContext):
    items: list[str] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)

class Step1(BaseStep[ProcessContext]):
    def execute(self, context: ProcessContext) -> StepResult:
        context.items = load_items()
        return StepResult(success=True)

class Step2(BaseStep[ProcessContext]):
    def execute(self, context: ProcessContext) -> StepResult:
        # Access state from previous step
        for item in context.items:
            context.results[item] = process(item)
        return StepResult(success=True)
```

**Avoid Side Effects:**

```python
# Bad: Modifying global state
class BadStep(BaseStep[MyContext]):
    def execute(self, context: MyContext) -> StepResult:
        global_cache.update(data)  # Side effect!
        return StepResult(success=True)

# Good: Use context
class GoodStep(BaseStep[MyContext]):
    def execute(self, context: MyContext) -> StepResult:
        context.cache_data = data  # State in context
        return StepResult(success=True)
```

---

## Troubleshooting

### Common Errors

**"Action not found"**
```
ActionNotFoundError: Action 'train' not found in plugin 'my_plugin'
```
- Check `config.yaml` has the action defined
- Verify entrypoint format: `module.path:ClassName`
- Ensure module is importable

**"Parameter validation failed"**
```
ValidationError: 1 validation error for TrainParams
epochs: Input should be greater than 0
```
- Check parameter values against Pydantic constraints
- Review Field validators in params model

**"Step failed with rollback"**
```
RuntimeError: Step 'upload' failed: Connection timeout
```
- Check step's error message for root cause
- Verify rollback completed (check logs)
- Implement better error handling in step

**"Cannot import action class"**
```
ImportError: cannot import name 'MyAction' from 'my_module'
```
- Verify class is exported in module's `__all__`
- Check for circular imports
- Ensure dependencies are installed

### Debugging Tips

**Enable debug logging:**

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or for specific module
logging.getLogger('synapse_sdk.plugins').setLevel(logging.DEBUG)
```

**Test with LocalExecutor first:**

```python
from synapse_sdk.plugins.executors import LocalExecutor

executor = LocalExecutor(env={'DEBUG': 'true'})
result = executor.execute(MyAction, params)
```

**Inspect discovered actions:**

```python
from synapse_sdk.plugins.discovery import PluginDiscovery

discovery = PluginDiscovery.from_path('/path/to/plugin')
print(f"Actions: {discovery.list_actions()}")

for name in discovery.list_actions():
    cls = discovery.get_action_class(name)
    print(f"{name}: {cls.params_model}, {cls.result_model}")
```

**Check step execution order:**

```python
registry = StepRegistry[MyContext]()
# ... register steps ...

for step in registry.get_steps():
    print(f"{step.name}: weight={step.progress_weight}")

print(f"Total weight: {registry.total_weight}")
```

---

## Related Documentation

- **[../../AGENT.md](../../AGENT.md)** - Project development guide
- **[../../README.md](../../README.md)** - SDK overview
- **[PLUGIN_STRUCTURE_GUIDE.md](PLUGIN_STRUCTURE_GUIDE.md)** - Complete plugin structure
- **[ACTION_DEV_GUIDE.md](ACTION_DEV_GUIDE.md)** - Action development
- **[STEP.md](STEP.md)** - Step implementations
- **[LOGGING_SYSTEM.md](LOGGING_SYSTEM.md)** - Logging system
- **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)** - Pipeline execution
