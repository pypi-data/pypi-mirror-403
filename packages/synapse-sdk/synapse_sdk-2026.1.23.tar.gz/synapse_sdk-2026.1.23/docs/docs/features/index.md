---
id: index
title: Features
sidebar_position: 1
---

# Features

This section covers the key features and functionality provided by the Synapse SDK.

## [Plugin System](../plugins/index.md)

Comprehensive plugin framework for building and managing ML workflows.

- **[Plugin Categories](../plugins/index.md#plugin-categories)** - Neural networks, export, upload, smart tools, and validation plugins
- **[Execution Methods](../plugins/index.md#execution-methods)** - Job, Task, and REST API execution modes
- **[Development Guide](../plugins/plugin-development.md)** - Create, test, and deploy custom plugins

## [Pipeline Patterns](./pipelines/index.md)

Powerful workflow orchestration patterns for complex multi-step operations.

- **[Step Orchestration](./pipelines/step-orchestration.md)** - Sequential step-based workflows with progress tracking and rollback
- **Utility Steps** - Built-in logging, timing, and validation step wrappers
- **Action Integration** - Seamless integration with Train, Export, and Upload actions

## [Data Converters](./converters/index.md)

Comprehensive data format conversion utilities for computer vision datasets.

- **[Format Converters](./converters/index.md)** - Convert between DM, COCO, Pascal VOC, and YOLO formats
- **[Version Migration](./converters/index.md#dm-version-converter)** - Migrate DM datasets between versions

## [Utilities](../utils/storage.md)

Storage, file handling, and data transfer utilities.

- **[Storage Providers](../utils/storage.md)** - Abstraction layer for S3, GCS, Azure, local, and SFTP storage
- **[File Utilities](../utils/file.md)** - Checksum, archive, and file I/O operations
- **[Network Utilities](../utils/network.md)** - Streaming and network transfer utilities