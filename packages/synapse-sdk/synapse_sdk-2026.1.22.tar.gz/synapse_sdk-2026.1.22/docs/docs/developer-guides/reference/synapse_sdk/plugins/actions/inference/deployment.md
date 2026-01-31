---
sidebar_label: deployment
title: synapse_sdk.plugins.actions.inference.deployment
---

# synapse_sdk.plugins.actions.inference.deployment

Ray Serve deployment action base class.

## DeploymentProgressCategories

```python
class DeploymentProgressCategories:
    INITIALIZE = 'initialize'
    DEPLOY = 'deploy'
    REGISTER = 'register'
```

## BaseDeploymentAction

```python
class BaseDeploymentAction(BaseAction[P]):
```

Base class for deploying `BaseServeDeployment` subclasses to Ray Serve. Handles Ray initialization, serve deployment with decorators, and backend registration.

### Class Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `progress` | `DeploymentProgressCategories` | Progress category constants |
| `entrypoint` | `type \| None` | `BaseServeDeployment` subclass to deploy |

### Properties

#### client

```python
@property
def client(self) -> BackendClient
```

Backend client from runtime context.

#### agent_client

```python
@property
def agent_client(self) -> AgentClient
```

Agent client for serve application registration.

### Methods

#### ray_init

```python
def ray_init(self, **kwargs: Any) -> None
```

Initialize Ray cluster connection. Connects to the cluster specified by environment.

#### deploy

```python
def deploy(self) -> None
```

Deploy the `entrypoint` class to Ray Serve. Automatically applies `@serve.deployment` and `@serve.ingress(app)` decorators, using `get_ray_actor_options()` for resource configuration and `get_route_prefix()` for URL routing.

#### register_serve_application

```python
def register_serve_application(self) -> int | None
```

Register the deployed serve application with the Synapse backend.

**Returns**: Serve application ID if created, `None` otherwise.

### Configuration Methods

Override these to customize deployment behavior:

#### get_serve_app_name

```python
def get_serve_app_name(self) -> str
```

**Default**: `SYNAPSE_PLUGIN_RELEASE_CODE` env var.

#### get_route_prefix

```python
def get_route_prefix(self) -> str
```

**Default**: `/{SYNAPSE_PLUGIN_RELEASE_CHECKSUM}` or `/{md5(app_name)}`.

#### get_ray_actor_options

```python
def get_ray_actor_options(self) -> dict[str, Any]
```

**Default**: Extracts `num_cpus`, `num_gpus`, `memory` from action params.

#### get_runtime_env

```python
def get_runtime_env(self) -> dict[str, Any]
```

**Default**: Empty dict `{}`.

### Usage

See [Inference Actions](../../../../plugins/action-types/inference-actions#example-model-deployment) for a complete example.
