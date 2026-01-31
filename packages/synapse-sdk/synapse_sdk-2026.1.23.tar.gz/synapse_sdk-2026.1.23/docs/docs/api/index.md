---
id: index
title: SDK API
sidebar_position: 1
---

# SDK API

SDK 사용을 위한 가이드 문서입니다. 상세 API 레퍼런스는 [Developer Guides](../developer-guides/index.md)를 참조하세요.

## Overview

The SDK API is organized into the following main sections:

### [Clients](./clients/index.md)

Client classes for interacting with backend services and agents.

- **Guide** - Usage examples and best practices for BackendClient, AgentClient, RayClient
- **Mixins** - Specialized functionality (Annotation, DataCollection, HITL, ML, Integration)

### [Plugins](./plugins/models.md)

Plugin system API for building custom actions and integrations.

- **API** - Plugin models, categories, datasets, and utilities

## Quick Reference

### Creating a Client

```python
from synapse_sdk.clients.backend import BackendClient

client = BackendClient(
    base_url="https://api.synapse.sh",
    api_token="your-api-token"
)
```

### Using Plugin Actions

```python
from synapse_sdk.plugins.actions.train import TrainAction

class MyTrainAction(TrainAction):
    def run(self):
        # Your training logic here
        pass
```

### File Operations

```python
from synapse_sdk.utils.file import archive, checksum

# Create archive
archive.create_zip("/path/to/source", "/path/to/output.zip")

# Verify checksum
checksum.verify_md5("/path/to/file", expected_hash)
```

## Documentation Structure

| Section | Description | Use When |
|---------|-------------|----------|
| **Guide** | High-level usage patterns and examples | Learning how to use a feature |
| **Mixins** | Specialized client functionality | Understanding specific capabilities |
| **API** | Plugin system interfaces | Building custom plugins |
