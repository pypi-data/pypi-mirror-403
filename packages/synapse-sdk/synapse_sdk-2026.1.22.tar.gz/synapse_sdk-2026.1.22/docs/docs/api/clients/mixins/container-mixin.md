---
id: container-mixin
title: ContainerClientMixin
sidebar_position: 7
---

# ContainerClientMixin

Mixin providing container management endpoints for Docker container lifecycle operations.

## Overview

The `ContainerClientMixin` provides methods for managing Docker containers on agents. It supports creating, listing, and removing containers that run plugin releases.

## Methods

### list_docker_containers

List all Docker containers on the host.

```python filename="examples/list_containers.py"
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(base_url="https://agent.example.com")

containers = client.list_docker_containers()
for container in containers:
    print(f"Container: {container['id']} - {container['status']}")
```

**Returns:** `list[dict]` - List of container information dictionaries.

---

### get_docker_container

Get a specific Docker container by ID.

```python filename="examples/get_container.py"
container = client.get_docker_container("abc123def456")
print(f"Status: {container['status']}")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container_id` | `str` | Docker container ID |

**Returns:** `dict` - Container details.

---

### create_docker_container

Build and run a Docker container for a plugin release.

```python filename="examples/create_container.py"
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(base_url="https://agent.example.com")

container = client.create_docker_container(
    plugin_release="my_plugin@1.0.0",
    params={"input": "data"},
    envs={"DEBUG": "true"},
    metadata={"created_by": "automation"},
    labels=["production", "ml-model"]
)

print(f"Container ID: {container['id']}")
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `plugin_release` | `str` | Yes | Plugin identifier (e.g., `plugin_code@version`) |
| `params` | `dict` | No | Parameters forwarded to the plugin |
| `envs` | `dict` | No | Environment variables for the container |
| `metadata` | `dict` | No | Additional metadata stored with the record |
| `labels` | `list[str]` | No | Container labels for display/filtering |

**Returns:** `dict` - Created container information.

---

### delete_docker_container

Stop and remove a Docker container.

```python filename="examples/delete_container.py"
client.delete_docker_container("abc123def456")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container_id` | `str` | Docker container ID |

---

## Database Container Records

In addition to Docker operations, this mixin provides methods for managing container records in the database.

### list_containers

List tracked containers from the database.

```python filename="examples/list_db_containers.py"
containers, total = client.list_containers(
    params={"status": "running"},
    list_all=True
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `params` | `dict` | Filter parameters |
| `list_all` | `bool` | Fetch all pages automatically |

**Returns:** `dict` or `tuple[list, int]` - Container list (with total count if `list_all=True`).

---

### get_container

Get a tracked container by database ID.

```python filename="examples/get_db_container.py"
container = client.get_container(42)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container_id` | `int` | Database container ID |

**Returns:** `dict` - Container details.

---

### update_container

Update a tracked container's status.

```python filename="examples/update_container.py"
updated = client.update_container(42, status="stopped")
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container_id` | `int` | Database container ID |
| `status` | `str` | New status value |

**Returns:** `dict` - Updated container details.

---

### delete_container

Delete a tracked container (also stops the Docker container).

```python filename="examples/delete_db_container.py"
client.delete_container(42)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `container_id` | `int` | Database container ID |

---

## Usage with AgentClient

The `ContainerClientMixin` is used by `AgentClient`:

```python filename="examples/agent_client.py"
from synapse_sdk.clients.agent import AgentClient

client = AgentClient(
    base_url="https://agent.example.com",
    access_token="your-token"
)

# Create a container for a plugin
container = client.create_docker_container(
    plugin_release="ocr_processor@2.0.0",
    params={"format": "pdf"},
    envs={"WORKERS": "4"}
)

# Monitor the container
status = client.get_docker_container(container["docker_id"])
print(f"Running: {status['running']}")

# Clean up
client.delete_docker_container(container["docker_id"])
```

---

## See Also

- [PluginClientMixin](./plugin-mixin.md) - Plugin release management
- [AgentClient](../agent.md) - Agent client overview
