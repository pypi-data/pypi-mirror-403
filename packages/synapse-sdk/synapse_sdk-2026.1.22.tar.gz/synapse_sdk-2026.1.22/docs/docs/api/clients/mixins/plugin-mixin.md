---
id: plugin-mixin
title: PluginClientMixin
sidebar_position: 8
---

# PluginClientMixin

Mixin providing plugin release management endpoints for fetching, caching, and executing plugins.

## Overview

The `PluginClientMixin` provides methods for managing plugin releases on agents. It supports listing, fetching, caching, and executing plugin releases.

## Methods

### list_plugin_releases

List all cached plugin releases.

```python filename="examples/list_releases.py"
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(base_url="https://agent.example.com")

releases, total = client.list_plugin_releases(list_all=True)
for release in releases:
    print(f"{release['plugin']}@{release['version']}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `params` | `dict` | Filter parameters |
| `list_all` | `bool` | Fetch all pages automatically |

**Returns:** `dict` or `tuple[list, int]` - Release list (with total count if `list_all=True`).

---

### get_plugin_release

Get a plugin release by ID or `code@version` identifier.

```python filename="examples/get_release.py"
# By code@version
release = client.get_plugin_release("my_plugin@1.0.0")

# By ID
release = client.get_plugin_release("123")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `lookup` | `str` | Release ID or `plugin_code@version` |

**Returns:** `dict` - Plugin release details.

---

### create_plugin_release

Fetch and cache a plugin release from the backend.

```python filename="examples/create_release.py"
release = client.create_plugin_release(
    plugin="my_plugin",
    version="1.0.0"
)

print(f"Cached: {release['id']}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `plugin` | `str` | Plugin code identifier |
| `version` | `str` | Version string |

**Returns:** `dict` - Created/cached release details.

---

### delete_plugin_release

Delete a cached plugin release.

```python filename="examples/delete_release.py"
client.delete_plugin_release("my_plugin@1.0.0")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `lookup` | `str` | Release ID or `plugin_code@version` |

---

### run_plugin_release

Execute a plugin release action.

```python filename="examples/run_release.py"
result = client.run_plugin_release(
    lookup="ocr_plugin@2.0.0",
    action="process_document",
    params={"file_path": "/data/document.pdf"},
    requirements=["pillow>=9.0.0"],
    job_id="job_abc123"
)

print(f"Result: {result}")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lookup` | `str` | Yes | Plugin identifier (ID or `plugin@version`) |
| `action` | `str` | No* | Action name to execute |
| `params` | `dict` | No | Parameters to pass to the action |
| `data` | `dict` | No | Full request payload (legacy compatibility). If provided, sent as-is and other fields are ignored |
| `requirements` | `list[str]` | No | Additional pip requirements |
| `job_id` | `str` | No | Job ID for tracking |

\* `action` is required unless `data` is provided.

**Returns:** `Any` - Action execution result.

**Legacy compatibility:**

The `data` parameter supports the v1 calling convention where the full payload is passed as a dict:

```python
# Legacy style (still supported)
result = client.run_plugin_release("my_plugin@1.0.0", data={
    "action": "train",
    "params": {"epochs": 10},
    "job_id": "job-uuid",
})

# Recommended style
result = client.run_plugin_release(
    "my_plugin@1.0.0", "train",
    params={"epochs": 10},
    job_id="job-uuid",
)
```

---

### run_debug_plugin_release

Run a plugin in debug mode directly from source path.

```python filename="examples/debug_release.py"
result = client.run_debug_plugin_release(
    action="process",
    params={"input": "test"},
    plugin_path="/path/to/plugin/source",
    config={"debug": True},
    modules={
        "my_plugin.processor": "class Processor: ...",
    },
    requirements=["numpy"],
    job_id="debug_job_123"
)
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | `str` | Yes | Action name to execute |
| `params` | `dict` | No | Parameters to pass to the action |
| `plugin_path` | `str` | No | Path to plugin source directory |
| `config` | `dict` | No | Plugin configuration override |
| `modules` | `dict` | No | Module source code mapping |
| `requirements` | `list[str]` | No | Additional pip requirements |
| `job_id` | `str` | No | Job ID for tracking |

**Returns:** `Any` - Action execution result.

> **Good to know**: Debug mode is useful for development and testing. The plugin is loaded directly from source without creating a release.

---

## Usage with AgentClient

The `PluginClientMixin` is used by `AgentClient`:

```python filename="examples/agent_plugin.py"
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(
    base_url="https://agent.example.com",
    access_token="your-token"
)

# Cache a plugin release
client.create_plugin_release("ml_model", "1.2.0")

# Execute the plugin
result = client.run_plugin_release(
    lookup="ml_model@1.2.0",
    action="predict",
    params={"data": [1, 2, 3, 4, 5]}
)

print(f"Prediction: {result}")
```

---

## Typical Workflow

1. **Fetch and cache** the plugin release:
   ```python
   client.create_plugin_release("my_plugin", "1.0.0")
   ```

2. **Execute** the plugin action:
   ```python
   result = client.run_plugin_release("my_plugin@1.0.0", "process", params={...})
   ```

3. **Clean up** when done:
   ```python
   client.delete_plugin_release("my_plugin@1.0.0")
   ```

---

## See Also

- [ContainerClientMixin](./container-mixin.md) - Container management
- [AgentClient](../agent.md) - Agent client overview
