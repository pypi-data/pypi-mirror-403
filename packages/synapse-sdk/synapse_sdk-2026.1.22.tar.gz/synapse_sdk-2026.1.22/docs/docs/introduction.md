---
id: introduction
title: Introduction
sidebar_position: 1
---

:::warning[Alpha Version]

This is **v2-alpha** of the Synapse SDK. The API is under active development and may change without notice. Not recommended for production use.

:::

# Synapse SDK

Build ML and data processing plugins for the Synapse platform.

## Overview

Synapse SDK is a Python framework for creating modular, reusable plugins. Run your plugins as distributed jobs, background tasks, or REST API endpoints.

### Key Features

- **Plugin Development**: Create modular components organized by categories
- **Distributed Execution**: Scale across multiple nodes with [Ray](https://www.ray.io/)
- **Multiple Run Modes**: Execute as Jobs (batch processing), Tasks (async operations), or Serve (REST APIs)
- **Isolated Environments**: Each plugin runs with its own dependencies
- **Progress Tracking**: Monitor execution and report metrics

### Plugin Categories

| Category | Code | Description |
|----------|------|-------------|
| Neural Network | `NEURAL_NET` | ML model training, inference, and deployment |
| Export | `EXPORT` | Data export and transformation |
| Upload | `UPLOAD` | File and data upload |
| Smart Tools | `SMART_TOOL` | Intelligent automation tools |
| Post-Annotation | `POST_ANNOTATION` | Post-processing after annotation |
| Pre-Annotation | `PRE_ANNOTATION` | Pre-processing before annotation |
| Data Validation | `DATA_VALIDATION` | Data quality checks |
| Custom | `CUSTOM` | User-defined plugins |

## Getting Started

1. [Install the SDK](./installation.md)
2. [Follow the Quickstart](./quickstart.md)
3. [Explore the API Reference](./api/index.md)
4. [Learn about Plugin System](./plugins/index.md)

## Related

- [Plugin System](./plugins/index.md) - Understand the plugin architecture
- [Configuration](./configuration.md) - Set up backend connection
