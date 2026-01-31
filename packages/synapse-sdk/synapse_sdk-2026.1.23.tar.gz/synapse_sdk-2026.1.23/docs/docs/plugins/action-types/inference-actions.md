---
id: inference-actions
title: Inference Actions
sidebar_position: 2
---

# Inference Actions

Use inference actions to build model inference workflows. Use `BaseInferenceAction` for batch inference and `BaseDeploymentAction` for REST API serving via Ray Serve.

## Overview

Synapse SDK provides two base classes for inference workflows:

| Base Class | Purpose | Use Case |
|------------|---------|----------|
| `BaseInferenceAction` | Batch inference | Processing datasets, offline predictions |
| `BaseDeploymentAction` | REST API serving | Real-time inference endpoints via Ray Serve |

Both classes support two execution modes:
- **Simple Mode**: Override `execute()` directly for straightforward workflows
- **Step-Based Mode**: Use `setup_steps()` to register workflow steps for complex pipelines

## BaseInferenceAction

The base class for inference actions. Provides helper methods for model loading and inference workflows.

```python filename="synapse_sdk/plugins/actions/inference/action.py"
class BaseInferenceAction(BaseAction[P]):
    category = PluginCategory.NEURAL_NET
    progress = InferenceProgressCategories()
```

### Progress Categories

Track inference progress with these standard categories:

| Category | Value | Description |
|----------|-------|-------------|
| `MODEL_LOAD` | `'model_load'` | Model loading and initialization |
| `INFERENCE` | `'inference'` | Running inference on inputs |
| `POSTPROCESS` | `'postprocess'` | Post-processing results |

```python filename="examples/progress_tracking.py"
self.set_progress(1, 3, self.progress.MODEL_LOAD)
self.set_progress(2, 3, self.progress.INFERENCE)
self.set_progress(3, 3, self.progress.POSTPROCESS)
```

### Helper Methods

#### get_model

Retrieve model metadata by ID.

```python
def get_model(self, model_id: int) -> dict[str, Any]
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | `int` | Yes | Model identifier |

**Returns**: Model metadata dictionary including file URL.

```python filename="examples/get_model.py"
model = self.get_model(123)
print(model['name'], model['file'])
```

#### download_model

Download and extract model artifacts.

```python
def download_model(
    self,
    model_id: int,
    output_dir: str | Path | None = None,
) -> Path
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model_id` | `int` | Yes | - | Model identifier |
| `output_dir` | `str \| Path \| None` | No | `None` | Directory to extract model to. Uses tempdir if None |

**Returns**: Path to extracted model directory.

```python filename="examples/download_model.py"
model_path = self.download_model(123)
# model_path contains extracted model artifacts
```

#### load_model

Load model for inference. Downloads artifacts and returns model info with local path.

```python
def load_model(self, model_id: int) -> dict[str, Any]
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | `int` | Yes | Model identifier |

**Returns**: Model metadata dict with `'path'` key for local artifacts.

```python filename="examples/load_model.py"
model_info = self.load_model(123)
model_path = model_info['path']
# Load your model framework here:
# model = torch.load(model_path / 'model.pt')
```

#### infer

Run inference on inputs. Override this method to implement your inference logic.

```python
def infer(
    self,
    model: Any,
    inputs: list[dict[str, Any]],
) -> list[dict[str, Any]]
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | `Any` | Yes | Loaded model (framework-specific) |
| `inputs` | `list[dict[str, Any]]` | Yes | List of input dictionaries |

**Returns**: List of result dictionaries.

```python filename="examples/infer.py"
def infer(self, model, inputs):
    results = []
    for inp in inputs:
        prediction = model.predict(inp['image'])
        results.append({'prediction': prediction})
    return results
```

### Execution Modes

#### Simple Mode

Override `execute()` directly for simple workflows:

```python filename="plugin/inference.py"
from synapse_sdk.plugins.actions.inference import BaseInferenceAction
from pydantic import BaseModel

class InferenceParams(BaseModel):
    model_id: int
    inputs: list[dict]

class MyInferenceAction(BaseInferenceAction[InferenceParams]):
    action_name = 'inference'

    def execute(self) -> dict[str, Any]:
        # Load model
        model_info = self.load_model(self.params.model_id)
        self.set_progress(1, 3, self.progress.MODEL_LOAD)

        # Run inference
        results = self.infer(model_info, self.params.inputs)
        self.set_progress(2, 3, self.progress.INFERENCE)

        # Post-process
        processed = self._postprocess(results)
        self.set_progress(3, 3, self.progress.POSTPROCESS)

        return {'results': processed}

    def infer(self, model, inputs):
        import torch

        model_obj = torch.load(model['path'] + '/model.pt')
        results = []
        for inp in inputs:
            pred = model_obj(inp['tensor'])
            results.append({'prediction': pred.tolist()})
        return results
```

#### Step-Based Mode

Use `setup_steps()` to register workflow steps for complex pipelines:

```python filename="plugin/inference.py"
from synapse_sdk.plugins.actions.inference import (
    BaseInferenceAction,
    InferenceContext,
)
from synapse_sdk.plugins.steps import BaseStep, StepResult, StepRegistry

class LoadModelStep(BaseStep[InferenceContext]):
    @property
    def name(self) -> str:
        return 'load_model'

    @property
    def progress_weight(self) -> float:
        return 0.3

    def execute(self, context: InferenceContext) -> StepResult:
        # Load model using context
        import torch

        model_path = context.model_path
        context.model = torch.load(f'{model_path}/model.pt')
        return StepResult(success=True)

class InferenceStep(BaseStep[InferenceContext]):
    @property
    def name(self) -> str:
        return 'inference'

    @property
    def progress_weight(self) -> float:
        return 0.7

    def execute(self, context: InferenceContext) -> StepResult:
        for request in context.requests:
            prediction = context.model(request['input'])
            context.results.append({'prediction': prediction})
            context.processed_count += 1
        return StepResult(success=True)

class MyInferenceAction(BaseInferenceAction[InferenceParams]):
    action_name = 'inference'

    def setup_steps(self, registry: StepRegistry[InferenceContext]) -> None:
        registry.register(LoadModelStep())
        registry.register(InferenceStep())
```

## InferenceContext

Context for inference action step-based workflows. Extends `BaseStepContext` with inference-specific state.

```python filename="synapse_sdk/plugins/actions/inference/context.py"
@dataclass
class InferenceContext(BaseStepContext):
    params: dict[str, Any] = field(default_factory=dict)
    model_id: int | None = None
    model: dict[str, Any] | None = None
    model_path: str | None = None
    requests: list[dict[str, Any]] = field(default_factory=list)
    results: list[dict[str, Any]] = field(default_factory=list)
    batch_size: int = 1
    processed_count: int = 0
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `params` | `dict[str, Any]` | Action parameters |
| `model_id` | `int \| None` | ID of the model being used |
| `model` | `dict[str, Any] \| None` | Loaded model information from backend |
| `model_path` | `str \| None` | Local path to downloaded model |
| `requests` | `list[dict[str, Any]]` | Input requests to process |
| `results` | `list[dict[str, Any]]` | Inference results |
| `batch_size` | `int` | Batch size for processing |
| `processed_count` | `int` | Number of processed items |

## Example: Batch Inference

Complete example of a batch inference action with PyTorch:

```python filename="plugin/batch_inference.py"
from pathlib import Path
from typing import Any

import torch
from pydantic import BaseModel

from synapse_sdk.plugins.actions.inference import BaseInferenceAction


class BatchInferenceParams(BaseModel):
    model_id: int
    inputs: list[dict[str, Any]]
    batch_size: int = 32


class BatchInferenceAction(BaseInferenceAction[BatchInferenceParams]):
    """Batch inference action for PyTorch models."""

    action_name = 'batch_inference'

    def execute(self) -> dict[str, Any]:
        # Step 1: Load model
        model_info = self.load_model(self.params.model_id)
        model_path = Path(model_info['path'])
        model = torch.load(model_path / 'model.pt')
        model.eval()
        self.set_progress(1, 3, self.progress.MODEL_LOAD)

        # Step 2: Run inference in batches
        results = []
        inputs = self.params.inputs
        batch_size = self.params.batch_size

        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            batch_tensors = torch.stack([
                torch.tensor(inp['data']) for inp in batch
            ])

            with torch.no_grad():
                predictions = model(batch_tensors)

            for pred in predictions:
                results.append({'prediction': pred.tolist()})

        self.set_progress(2, 3, self.progress.INFERENCE)

        # Step 3: Post-process
        self.set_progress(3, 3, self.progress.POSTPROCESS)

        return {
            'results': results,
            'processed_count': len(results),
        }

    def infer(self, model, inputs):
        # Optional: Override for custom inference logic
        pass
```

---

## Deployment Actions

Use deployment actions to serve REST APIs via Ray Serve. Use `BaseDeploymentAction` to deploy inference endpoints.

### BaseDeploymentAction

Base class for Ray Serve deployment actions. Handles Ray initialization, deployment creation, and backend registration.

```python filename="synapse_sdk/plugins/actions/inference/deployment.py"
class BaseDeploymentAction(BaseAction[P]):
    progress = DeploymentProgressCategories()
    entrypoint: type | None = None  # Set to your serve deployment class
```

### DeploymentProgressCategories

| Category | Value | Description |
|----------|-------|-------------|
| `INITIALIZE` | `'initialize'` | Ray cluster initialization |
| `DEPLOY` | `'deploy'` | Deploying to Ray Serve |
| `REGISTER` | `'register'` | Registering with backend |

### Deployment Methods

#### ray_init

Initialize Ray cluster connection.

```python
def ray_init(self, **kwargs: Any) -> None
```

#### deploy

Deploy the inference endpoint to Ray Serve.

```python
def deploy(self) -> None
```

#### register_serve_application

Register the serve application with the backend.

```python
def register_serve_application(self) -> int | None
```

**Returns**: Serve application ID if created, `None` otherwise.

### Configuration Methods

Override these methods to customize deployment:

| Method | Default | Description |
|--------|---------|-------------|
| `get_serve_app_name()` | `SYNAPSE_PLUGIN_RELEASE_CODE` env var | Serve application name |
| `get_route_prefix()` | `SYNAPSE_PLUGIN_RELEASE_CHECKSUM` env var | URL route prefix |
| `get_ray_actor_options()` | Extract from params | Ray actor options (num_cpus, num_gpus, memory) |
| `get_runtime_env()` | `{}` | Ray runtime environment |

### BaseServeDeployment

Base class for Ray Serve inference deployments. Inherits from `BaseAction` and provides model loading with multiplexing support.

```python filename="synapse_sdk/plugins/actions/inference/serve.py"
class BaseServeDeployment(BaseAction):
    def __init__(self, backend_url: str) -> None:
        self.backend_url = backend_url
        self._model_cache: dict[str, Any] = {}
```

**Abstract methods to implement:**

| Method | Description |
|--------|-------------|
| `async _get_model(model_info: dict) -> Any` | Load model from extracted artifacts |
| `async infer(*args, **kwargs) -> Any` | Run inference on inputs |

**Class attributes:**

| Attribute | Description |
|-----------|-------------|
| `action_name` | Name for action discovery (e.g., `'inference'`) |
| `app` | FastAPI app instance (decorators applied automatically by `deploy()`) |

#### infer_remote

Call the deployed serve endpoint for inference. Used by the entrypoint when an inference action is executed.

```python
@classmethod
def infer_remote(cls, params: dict[str, Any], ctx: Any) -> Any
```

**Params format:**

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `model` | `int \| str` | No | Model ID for multiplexing |
| `method` | `str` | No | HTTP method (default: `'post'`) |
| `json` | `dict` | Yes | Request body sent to the serve endpoint |

```python filename="examples/infer_remote_params.py"
# Inference params payload
params = {
    "model": 34,
    "method": "post",
    "json": {
        "image_path": "https://example.com/image.jpg",
        "threshold": 0.5,
    }
}
```

### DeploymentContext

Context for deployment action step-based workflows.

```python filename="synapse_sdk/plugins/actions/inference/context.py"
@dataclass
class DeploymentContext(BaseStepContext):
    params: dict[str, Any] = field(default_factory=dict)
    model_id: int | None = None
    model: dict[str, Any] | None = None
    model_path: str | None = None
    serve_app_name: str | None = None
    serve_app_id: int | None = None
    route_prefix: str | None = None
    ray_actor_options: dict[str, Any] = field(default_factory=dict)
    deployed: bool = False
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `serve_app_name` | `str \| None` | Ray Serve application name |
| `serve_app_id` | `int \| None` | ID of created serve application |
| `route_prefix` | `str \| None` | URL route prefix for deployment |
| `ray_actor_options` | `dict[str, Any]` | Ray actor configuration |
| `deployed` | `bool` | Whether deployment succeeded |

### create_serve_multiplexed_model_id

Create a JWT-encoded model ID for serve multiplexing.

```python
def create_serve_multiplexed_model_id(
    model_id: int | str,
    token: str,
    backend_url: str,
    tenant: str | None = None,
) -> str
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | `int \| str` | Yes | Model ID to encode |
| `token` | `str` | Yes | User access token |
| `backend_url` | `str` | Yes | Backend URL (used as JWT secret) |
| `tenant` | `str \| None` | No | Tenant identifier |

**Returns**: JWT-encoded model token string.

```python filename="examples/multiplexing.py"
from synapse_sdk.plugins.actions.inference import create_serve_multiplexed_model_id

model_token = create_serve_multiplexed_model_id(
    model_id=123,
    token='user_access_token',
    backend_url='https://api.example.com',
    tenant='my-tenant',
)
# Use in request headers:
headers = {'serve_multiplexed_model_id': model_token}
```

### Example: Model Deployment

Complete example of deploying a PyTorch model with Ray Serve:

```python filename="plugin/inference.py"
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

from synapse_sdk.plugins.actions.inference import (
    BaseDeploymentAction,
    BaseServeDeployment,
)

app = FastAPI()


class PyTorchInference(BaseServeDeployment):
    """PyTorch inference deployment.

    The @serve.deployment and @serve.ingress(app) decorators are applied
    automatically by BaseDeploymentAction.deploy().
    """

    action_name = 'inference'
    app = app

    async def _get_model(self, model_info: dict[str, Any]) -> Any:
        import torch

        model_path = model_info['path'] / 'model.pt'
        model = torch.load(model_path)
        model.eval()
        return model

    @app.post('/')
    async def infer(self, inputs: list[dict]) -> list[dict]:
        model = await self.get_model()

        import torch

        results = []
        for inp in inputs:
            tensor = torch.tensor(inp['data'])
            with torch.no_grad():
                prediction = model(tensor)
            results.append({'prediction': prediction.tolist()})

        return results


class DeploymentParams(BaseModel):
    model: int
    num_gpus: int = 1


class MyDeploymentAction(BaseDeploymentAction[DeploymentParams]):
    """Deploy PyTorch model to Ray Serve."""

    action_name = 'deployment'
    entrypoint = PyTorchInference

    def execute(self) -> dict[str, Any]:
        # Initialize Ray
        self.ray_init()
        self.set_progress(1, 3, self.progress.INITIALIZE)

        # Deploy to Ray Serve
        self.deploy()
        self.set_progress(2, 3, self.progress.DEPLOY)

        # Register with backend
        app_id = self.register_serve_application()
        self.set_progress(3, 3, self.progress.REGISTER)

        return {'serve_application': app_id}
```

### Running Inference

Once deployed, call the serve endpoint via the `inference` action:

```bash
synapse plugin run inference --mode job --params '{"model": 34, "method": "post", "json": {"inputs": [{"data": [1, 2, 3]}]}}'
```

The entrypoint detects `BaseServeDeployment` subclasses and calls `infer_remote()`, which resolves the deployed endpoint's route prefix and forwards the request.

---

## Best Practices

### Model Caching

Cache loaded models to avoid repeated downloads:

```python filename="examples/model_caching.py"
class CachedInferenceAction(BaseInferenceAction[InferenceParams]):
    _model_cache: dict[int, Any] = {}

    def load_model_cached(self, model_id: int) -> Any:
        if model_id not in self._model_cache:
            model_info = self.load_model(model_id)
            self._model_cache[model_id] = torch.load(model_info['path'] + '/model.pt')
        return self._model_cache[model_id]
```

### Batch Processing Optimization

Process inputs in batches for better throughput:

```python filename="examples/batch_processing.py"
def execute(self) -> dict[str, Any]:
    model = self.load_model_cached(self.params.model_id)

    # Process in batches
    batch_size = self.params.batch_size
    results = []

    for i in range(0, len(self.params.inputs), batch_size):
        batch = self.params.inputs[i:i + batch_size]
        batch_results = self._process_batch(model, batch)
        results.extend(batch_results)

        # Update progress
        progress = min((i + batch_size) / len(self.params.inputs), 1.0)
        self.set_progress(int(progress * 100), 100, self.progress.INFERENCE)

    return {'results': results}
```

### Error Handling

Handle model loading and inference errors gracefully:

```python filename="examples/error_handling.py"
def execute(self) -> dict[str, Any]:
    try:
        model_info = self.load_model(self.params.model_id)
    except ValueError as e:
        self.log('model_load_error', {'error': str(e)})
        return {'error': f'Failed to load model: {e}'}

    try:
        results = self.infer(model_info, self.params.inputs)
    except Exception as e:
        self.log('inference_error', {'error': str(e)})
        return {'error': f'Inference failed: {e}', 'partial_results': []}

    return {'results': results}
```

---

## Related

- [Defining Actions](../defining-actions) - Core action base class
- [Step-Based Workflows](../steps-workflow) - Building complex workflows with steps
- [Train Actions](./train-actions) - Model training workflows
