---
sidebar_label: serve
title: synapse_sdk.plugins.actions.inference.serve
---

# synapse_sdk.plugins.actions.inference.serve

Ray Serve deployment base class and model multiplexing utilities.

## BaseServeDeployment

```python
class BaseServeDeployment(BaseAction):
```

Base class for Ray Serve inference deployments. Inherits from `BaseAction` to enable action discovery. Provides model loading with JWT-based multiplexing support.

### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `action_name` | `str` | Action name for discovery (e.g., `'inference'`) |
| `app` | `FastAPI` | FastAPI app instance. Decorators applied by `deploy()` |

### Constructor

```python
def __init__(self, backend_url: str) -> None
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `backend_url` | `str` | URL of the Synapse backend for fetching models |

### Methods

#### execute

```python
def execute(self) -> None
```

No-op. Serve deployments handle inference via `infer()`, not `execute()`.

#### infer_remote (classmethod)

```python
@classmethod
def infer_remote(cls, params: dict[str, Any], ctx: Any) -> Any
```

Call the deployed serve endpoint for inference. Resolves route prefix, creates model multiplexing token, and forwards the request.

**Params keys:**

| Key | Type | Required | Default | Description |
|-----|------|----------|---------|-------------|
| `model` | `int \| str` | No | `None` | Model ID for multiplexing header |
| `method` | `str` | No | `'post'` | HTTP method |
| `json` | `dict` | Yes | `{}` | Request body forwarded to serve endpoint |

**Route prefix resolution order:**
1. `SYNAPSE_PLUGIN_RELEASE_CHECKSUM` env var → `/{checksum}`
2. `SYNAPSE_PLUGIN_RELEASE_CODE` env var → `/{md5(code)}`
3. `config.yaml` in working directory → `/{md5(code@version)}`

#### get_model

```python
async def get_model(self) -> Any
```

Get the current model using Ray Serve's multiplexed model ID from request headers.

#### _get_model (abstract)

```python
@abstractmethod
async def _get_model(self, model_info: dict[str, Any]) -> Any
```

Load model from extracted artifacts. Override to implement model-specific loading.

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_info` | `dict` | Model metadata with `'path'` key pointing to extracted directory |

#### infer (abstract)

```python
@abstractmethod
async def infer(self, *args: Any, **kwargs: Any) -> Any
```

Run inference. Override and decorate with `@app.post('/')` to define the endpoint.

## create_serve_multiplexed_model_id

```python
def create_serve_multiplexed_model_id(
    model_id: int | str,
    token: str,
    backend_url: str,
    tenant: str | None = None,
) -> str
```

Create a JWT-encoded model ID for serve multiplexing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_id` | `int \| str` | Yes | Model ID to encode |
| `token` | `str` | Yes | User access token |
| `backend_url` | `str` | Yes | Backend URL (used as JWT secret) |
| `tenant` | `str \| None` | No | Tenant identifier |

**Returns**: JWT-encoded model token string for the `serve_multiplexed_model_id` header.
