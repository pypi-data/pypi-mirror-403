---
id: index
title: Architecture Overview
sidebar_label: Overview
sidebar_position: 1
---

# Architecture Overview

This section provides an overview of the Synapse SDK internal architecture for maintainers and contributors.

## Design Principles

### 1. Plugin-First Architecture

The SDK is designed around a plugin system that allows extensibility without modifying core code.

- **Actions** are the atomic units of work
- **Pipelines** compose actions into workflows
- **Executors** handle local or distributed execution

### 2. Type Safety

Strong typing throughout the codebase:

- Pydantic models for configuration and data validation
- Generic types for action parameters and results
- Runtime type checking for plugin discovery

### 3. Separation of Concerns

Clear boundaries between modules:

- `clients/` - HTTP communication with backend services
- `plugins/` - Plugin system and action definitions
- `utils/` - Shared utilities (file, network, storage)
- `cli/` - Command-line interface

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│                    (typer, commands)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Plugin System                           │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Actions │  │ Pipelines│  │ Executors│  │  Discovery  │  │
│  └─────────┘  └──────────┘  └──────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Backend  │  │   Agent   │  │   Ray    │  │ Pipeline │   │
│  └──────────┘  └───────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Utilities Layer                          │
│  ┌────────┐  ┌─────────┐  ┌──────────┐  ┌────────────────┐ │
│  │  File  │  │ Network │  │ Storage  │  │ Authentication │ │
│  └────────┘  └─────────┘  └──────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Key Modules

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `plugins.action` | Base action classes | `BaseAction`, `@action` |
| `plugins.executors` | Execution engines | `LocalExecutor`, `RayExecutor` |
| `plugins.pipelines` | Workflow composition | `Pipeline`, `Step` |
| `clients.backend` | Backend API client | `BackendClient` |
| `clients.agent` | Agent communication | `AgentClient`, `RayClient` |

## Next Steps

- [Project Structure](./project-structure) - Detailed codebase organization
