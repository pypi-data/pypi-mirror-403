# Plugin System Overview

The Synapse SDK Plugin System is a comprehensive framework for building, discovering, and executing plugin actions. It provides a flexible architecture for creating reusable components that can run locally or distributed across Ray clusters.

## Target Audience

This documentation is for **plugin system developers** who need to:
- Create custom plugin actions for ML training, export, upload, inference, etc.
- Understand the plugin architecture for extension and customization
- Build step-based workflows with progress tracking and rollback support

## Prerequisites

- Python 3.12+
- Familiarity with Pydantic v2 for data validation
- Basic understanding of async/await patterns (for Ray execution)

---

## Key Concepts

### Actions

Actions are the fundamental units of work in the plugin system. Each action:
- Receives typed parameters (Pydantic models)
- Has access to a runtime context (logger, environment, clients)
- Produces a result (optionally typed)

```python
from synapse_sdk.plugins import BaseAction
from pydantic import BaseModel

class TrainParams(BaseModel):
    epochs: int = 10
    learning_rate: float = 0.001

class TrainAction(BaseAction[TrainParams]):
    def execute(self) -> dict:
        for epoch in range(self.params.epochs):
            self.set_progress(epoch + 1, self.params.epochs)
            # Training logic here
        return {'status': 'completed'}
```

### Contexts

Contexts provide runtime services and shared state:

- **RuntimeContext**: Injected into all actions, provides logger, environment, job tracking
- **BaseStepContext**: Extended by step-based workflows to share state between steps
- **Specialized Contexts**: TrainContext, UploadContext, etc. for domain-specific state

### Steps

Steps are composable workflow building blocks for multi-phase operations:

```python
from synapse_sdk.plugins.steps import BaseStep, StepResult

class LoadDataStep(BaseStep[MyContext]):
    @property
    def name(self) -> str:
        return 'load_data'

    @property
    def progress_weight(self) -> float:
        return 0.3  # 30% of total progress

    def execute(self, context: MyContext) -> StepResult:
        context.data = load_data()
        return StepResult(success=True)
```

### Executors

Executors determine where and how actions run:

| Executor | Use Case | Startup Time |
|----------|----------|--------------|
| `LocalExecutor` | Development, testing | Instant |
| `RayActorExecutor` | Light parallel tasks | <1 second |
| `RayJobExecutor` | Heavy workloads, isolation | ~30 seconds |
| `RayPipelineExecutor` | Multi-action workflows | Variable |

### Discovery

Plugin discovery loads actions from:
- **Config files**: `config.yaml` with action metadata
- **Python modules**: Scans for `@action` decorators and `BaseAction` subclasses
- **AST scanning**: Static analysis without import failures

---

## Tutorial: Creating Your First Plugin

This tutorial walks through creating a complete plugin from scratch.

### Step 1: Define Parameters Model

Create a Pydantic model for your action's input parameters:

```python
# my_plugin/params.py
from pydantic import BaseModel, Field

class ProcessParams(BaseModel):
    """Parameters for the process action."""

    input_path: str = Field(..., description='Path to input file')
    output_path: str = Field(..., description='Path to output file')
    batch_size: int = Field(default=32, ge=1, le=1024)
    verbose: bool = False
```

### Step 2: Create Action Class

Implement your action by subclassing `BaseAction`:

```python
# my_plugin/actions.py
from synapse_sdk.plugins import BaseAction
from synapse_sdk.plugins.enums import PluginCategory
from my_plugin.params import ProcessParams

class ProcessAction(BaseAction[ProcessParams]):
    """Process files with progress tracking."""

    action_name = 'process'
    category = PluginCategory.CUSTOM

    def execute(self) -> dict:
        # Access validated parameters
        input_path = self.params.input_path
        output_path = self.params.output_path

        # Log events
        self.log('process_start', {'input': input_path})

        # Simulate processing with progress
        total_items = 100
        for i in range(total_items):
            # Update progress (current, total)
            self.set_progress(i + 1, total_items)

            if self.params.verbose:
                self.log('item_processed', {'index': i})

        # Log metrics
        self.set_metrics({'items_processed': total_items}, category='process')

        # Return result
        return {
            'status': 'completed',
            'output_path': output_path,
            'items_processed': total_items,
        }
```

### Step 3: Write config.yaml

Create a configuration file for your plugin:

```yaml
# my_plugin/config.yaml
name: My Plugin
code: my_plugin
version: 0.1.0
category: custom

actions:
  process:
    name: Process Files
    description: Process input files with batch processing
    entrypoint: my_plugin.actions:ProcessAction
    method: task
```

### Step 4: Run Locally

Execute your action using `run_plugin`:

```python
# run.py
from synapse_sdk.plugins import run_plugin

result = run_plugin(
    plugin_code='my_plugin',  # Module path
    action='process',
    params={
        'input_path': '/data/input.csv',
        'output_path': '/data/output.csv',
        'batch_size': 64,
        'verbose': True,
    },
    mode='local',  # Run in current process
)

print(f"Result: {result}")
# Output: Result: {'status': 'completed', 'output_path': '/data/output.csv', 'items_processed': 100}
```

### Step 5: Add Result Schema (Optional)

For typed results, create a result model:

```python
# my_plugin/results.py
from pydantic import BaseModel

class ProcessResult(BaseModel):
    """Typed result for process action."""
    status: str
    output_path: str
    items_processed: int
```

Then update your action:

```python
# my_plugin/actions.py
from my_plugin.results import ProcessResult

class ProcessAction(BaseAction[ProcessParams]):
    result_model = ProcessResult  # Enable result validation

    def execute(self) -> ProcessResult:
        # ... processing logic ...
        return ProcessResult(
            status='completed',
            output_path=self.params.output_path,
            items_processed=total_items,
        )
```

---

## Two Ways to Define Actions

### Class-Based Actions (Recommended for Complex Actions)

Use `BaseAction` subclass for:
- Complex actions with multiple methods
- Actions that need class attributes (input_type, output_type)
- Step-based workflows
- Actions requiring autolog integration

```python
from synapse_sdk.plugins import BaseAction
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.types import YOLODataset, ModelWeights

class TrainAction(BaseAction[TrainParams]):
    """Train a YOLO model with comprehensive features."""

    # Optional class attributes
    action_name = 'train'
    category = PluginCategory.NEURAL_NET
    input_type = YOLODataset      # Semantic input type
    output_type = ModelWeights    # Semantic output type
    result_model = TrainResult    # Typed result schema

    def execute(self) -> TrainResult:
        # Enable automatic logging for Ultralytics
        self.autolog('ultralytics')

        # Access environment variables
        api_key = self.ctx.env.get('API_KEY', '')

        # Use the logger
        self.logger.info('Starting training')

        # Training implementation
        model = train_model(self.params)

        return TrainResult(
            weights_path=model.path,
            final_loss=model.loss,
        )
```

### Function-Based Actions (Simple Actions)

> **⚠️ DEPRECATED**: The `@action` decorator is deprecated and will be removed in a future version. Use class-based actions (extending `BaseAction`) instead for all new development.

Use `@action` decorator for:
- Simple, stateless operations
- Quick prototyping
- Actions without complex dependencies

**Note**: For new development, prefer class-based actions even for simple use cases.

```python
from synapse_sdk.plugins import action
from synapse_sdk.plugins.context import RuntimeContext
from pydantic import BaseModel

class ConvertParams(BaseModel):
    input_format: str
    output_format: str
    file_path: str

class ConvertResult(BaseModel):
    output_path: str
    converted: bool

@action(
    name='convert',
    description='Convert file between formats',
    params=ConvertParams,
    result=ConvertResult,
)
def convert(params: ConvertParams, context: RuntimeContext) -> ConvertResult:
    """Convert a file from one format to another."""

    # Log progress
    context.set_progress(0, 100)

    # Conversion logic
    output_path = convert_file(
        params.file_path,
        params.input_format,
        params.output_format,
    )

    context.set_progress(100, 100)

    return ConvertResult(
        output_path=output_path,
        converted=True,
    )
```

### Comparison: When to Use Each

| Aspect | Class-Based (`BaseAction`) | Function-Based (`@action`) |
|--------|---------------------------|---------------------------|
| **Status** | ✅ Recommended | ⚠️ **Deprecated** |
| Complexity | Complex, multi-method | Simple, single function |
| State | Can have instance state | Stateless |
| Type declarations | `input_type`, `output_type` | Not supported |
| Autolog | `self.autolog()` | Not available |
| Step workflows | Supported via mixins | Not supported |
| Testing | Easier mocking | Direct function calls |
| Config discovery | Full introspection | Limited metadata |

**Recommendation:** Always use class-based actions (`BaseAction`) for all new development, regardless of complexity.

---

## Specialized Action Base Classes

The SDK provides several specialized base classes that extend `BaseAction` with domain-specific features and built-in workflows:

### DatasetAction

Unified action for dataset download and conversion operations.

```python
from synapse_sdk.plugins.actions import DatasetAction, DatasetOperation, DatasetParams

class MyDatasetParams(DatasetParams):
    dataset: int
    operation: DatasetOperation = DatasetOperation.DOWNLOAD
    target_format: str | None = None

# Usage for download
result = run_plugin(
    'dataset_plugin',
    'dataset',
    {'dataset': 123, 'operation': 'download'},
)

# Usage for conversion
result = run_plugin(
    'dataset_plugin',
    'dataset',
    {'dataset': 123, 'operation': 'convert', 'target_format': 'yolo'},
)
```

### BaseTrainAction

For ML training workflows with dataset fetching and model upload helpers.

```python
from synapse_sdk.plugins.actions.train import BaseTrainAction

class MyTrainAction(BaseTrainAction[TrainParams]):
    def execute(self) -> dict:
        # Built-in helper methods
        dataset = self.get_dataset()  # Fetches params.dataset
        checkpoint = self.get_checkpoint()  # Optional resume

        # Training logic...

        # Upload model
        model = self.create_model('./model', name='trained-model')
        return {'model_id': model['id']}
```

**Progress Categories**: `DATASET`, `TRAIN`, `MODEL_UPLOAD`

### BaseUploadAction

Full step-based upload workflow with 7 built-in steps and automatic rollback.

```python
from synapse_sdk.plugins.actions.upload import BaseUploadAction

class S3UploadAction(BaseUploadAction[UploadParams]):
    # Uses built-in steps or override setup_steps()
    pass
```

**Built-in Steps**: `InitializeStep`, `ValidateFilesStep`, `AnalyzeCollectionStep`, `OrganizeFilesStep`, `GenerateDataUnitsStep`, `UploadFilesStep`, `ProcessMetadataStep`, `CleanupStep`

### BaseExportAction

Full step-based export workflow with 6 built-in steps and automatic rollback.

```python
from synapse_sdk.plugins.actions.export import DefaultExportAction

class MyExportAction(DefaultExportAction):
    action_name = 'export'
    # Uses built-in 6-step workflow
    # No setup_steps() override needed
```

**Built-in Steps** (6 total):
1. `InitializeStep`: Storage/path setup, output directory creation
2. `FetchResultsStep`: Target handler data retrieval
3. `PrepareExportStep`: Export params build, project config retrieval
4. `ConvertDataStep`: Data conversion pipeline
5. `SaveFilesStep`: File saving (original_file + data_file)
6. `FinalizeStep`: Additional file saving, error list, cleanup

**Progress Categories**: `FETCH`, `DATASET_CONVERSION`, `ORIGINAL_FILE`, `DATA_FILE`

### AddTaskDataAction

Pre-annotation workflows for task data preparation with FILE and INFERENCE methods.

```python
from synapse_sdk.plugins.actions import AddTaskDataAction, AddTaskDataMethod

class MyAddTaskDataAction(AddTaskDataAction):
    # Supports FILE and INFERENCE methods
    # Built-in step orchestration included
    pass
```

**Progress Category**: `ANNOTATE_TASK_DATA`

### BaseInferenceAction & BaseDeploymentAction

For model inference and Ray Serve deployment workflows.

```python
from synapse_sdk.plugins.actions.inference import BaseInferenceAction

class MyInferenceAction(BaseInferenceAction[InferParams]):
    def execute(self) -> dict:
        model = self.load_model(self.params.model_id)
        results = self.infer(model, self.params.inputs)
        return {'results': results}
```

### BaseServeDeployment

Ray Serve deployment class with model multiplexing support.

```python
from synapse_sdk.plugins.actions.inference import BaseServeDeployment
from ray import serve

@serve.deployment
@serve.ingress(app)
class MyServe(BaseServeDeployment):
    async def _get_model(self, model_info: dict):
        # Load model from artifacts
        return load_model(model_info['path'])

    async def infer(self, inputs: list[dict]) -> list[dict]:
        model = await self.get_model()  # Multiplexed loading
        return [model.predict(inp) for inp in inputs]
```

**Features**: Model caching, JWT-based model multiplexing, async inference

---

## Plugin Categories

Plugins are organized into categories for management and UI presentation:

| Category | Value | Description | Example Use Cases |
|----------|-------|-------------|-------------------|
| Neural Net | `neural_net` | ML model training | YOLO training, classification |
| Export | `export` | Model conversion/export | ONNX export, TensorRT |
| Upload | `upload` | Data/model uploads | S3 upload, model registry |
| Smart Tool | `smart_tool` | Interactive annotation | Auto-labeling, SAM |
| Pre-Annotation | `pre_annotation` | Before annotation | Data preprocessing |
| Post-Annotation | `post_annotation` | After annotation | QA checks, format conversion |
| Data Validation | `data_validation` | Data quality checks | Schema validation |
| Custom | `custom` | Custom functionality | Anything else |

Usage in actions:

```python
from synapse_sdk.plugins.enums import PluginCategory

class MyAction(BaseAction[MyParams]):
    category = PluginCategory.NEURAL_NET
```

---

## Execution Modes

### Local Execution

Best for development and testing. Runs in the current process:

```python
from synapse_sdk.plugins import run_plugin

result = run_plugin(
    plugin_code='my_plugin',
    action='train',
    params={'epochs': 10},
    mode='local',
)
```

Or using the executor directly:

```python
from synapse_sdk.plugins.executors import LocalExecutor

executor = LocalExecutor(
    env={'DEBUG': 'true'},  # Environment variables
    job_id='test-123',       # Optional job tracking ID
)

result = executor.execute(
    action_cls=TrainAction,
    params={'epochs': 10},
)
```

### Ray Task Execution

For parallel tasks with fast startup. Uses Ray Actors:

```python
from synapse_sdk.plugins.executors.ray import RayActorExecutor

executor = RayActorExecutor(
    working_dir='/path/to/plugin',  # Plugin code directory
    num_gpus=1,                      # GPU allocation
    num_cpus=4,                      # CPU allocation
)

result = executor.execute(
    action_cls=TrainAction,
    params={'epochs': 10},
)

# Clean up when done
executor.shutdown()
```

### Ray Job Execution

For heavy workloads requiring full isolation:

```python
from synapse_sdk.plugins.executors.ray import RayJobExecutor

executor = RayJobExecutor(
    dashboard_url='http://localhost:8265',
    working_dir='/path/to/plugin',
)

# Submit job (async)
job_id = executor.submit('train', {'epochs': 100})

# Check status
status = executor.get_status(job_id)
print(f"Status: {status}")  # PENDING, RUNNING, SUCCEEDED, FAILED

# Get logs
logs = executor.get_logs(job_id)

# Wait for completion
result = executor.wait(job_id, timeout_seconds=3600)
```

### Execution Mode Comparison

| Mode | Startup | Isolation | Best For |
|------|---------|-----------|----------|
| `local` | Instant | None | Development, testing |
| `task` | <1s | Process | Light parallel tasks |
| `job` | ~30s | Full | Production, heavy workloads |

---

## RuntimeContext Reference

All actions receive a `RuntimeContext` with these capabilities:

```python
def execute(self) -> dict:
    # Access the logger
    self.ctx.logger.info('Processing started')

    # Access environment variables
    api_key = self.ctx.env.get('API_KEY')
    debug = self.ctx.env.get('DEBUG', 'false') == 'true'

    # Log structured events
    self.ctx.log('event_name', {'key': 'value'})

    # Track progress
    self.ctx.set_progress(current=50, total=100, category='training')

    # Record metrics
    self.ctx.set_metrics({'loss': 0.05, 'accuracy': 0.95}, category='train')

    # Log user-visible messages
    self.ctx.log_message('Training complete!')

    # Log developer debug events
    self.ctx.log_dev_event('checkpoint_saved', {'path': '/model.pt'})

    # Access job ID for tracking
    job_id = self.ctx.job_id

    # Access backend client (if available)
    if self.ctx.client:
        self.ctx.client.upload_file(...)
```

---

## PluginEnvironment

Load configuration from environment variables or files:

```python
from synapse_sdk.plugins.context.env import PluginEnvironment

# From environment variables with prefix
env = PluginEnvironment.from_environ(prefix='PLUGIN_')

# From TOML file
env = PluginEnvironment.from_file('config.toml')

# Type-safe getters
api_key = env.get_str('API_KEY')
batch_size = env.get_int('BATCH_SIZE', default=32)
learning_rate = env.get_float('LEARNING_RATE', default=0.001)
debug = env.get_bool('DEBUG', default=False)
tags = env.get_list('TAGS', default=[])

# Merge multiple environments
merged = env.merge(another_env)
```

---

## Next Steps

- **[PLUGIN_STRUCTURE_GUIDE.md](PLUGIN_STRUCTURE_GUIDE.md)**: Complete plugin structure with step orchestration
- **[ACTION_DEV_GUIDE.md](ACTION_DEV_GUIDE.md)**: Complete action development guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)**: Deep dive into system architecture
- **[STEP.md](STEP.md)**: Step implementations guide
- **[LOGGING_SYSTEM.md](LOGGING_SYSTEM.md)**: Logging and progress tracking
- **[README.md](README.md)**: Quick reference and extension guide
- **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)**: Multi-action pipelines
