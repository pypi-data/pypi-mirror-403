---
id: index
title: Developer Guides
sidebar_label: Developer Guides
sidebar_position: 1
---

# Developer Guides

This section is intended for **SDK maintainers and contributors** who work on the Synapse SDK codebase itself.

:::info Who is this for?

- **SDK Maintainers**: Developers who maintain and extend the SDK
- **Contributors**: Anyone who wants to contribute to the project
- **Plugin Developers (Advanced)**: Those who need to understand internal APIs

If you're looking to **use** the SDK to build plugins, see the [Plugin System](../plugins/index.md) guide instead.

:::

## What's in this section

### Contributing

Learn how to set up your development environment, follow code quality standards, write tests, and submit pull requests.

- [Development Setup](./contributing/development-setup.md) - Set up your local environment
- [Code Quality](./contributing/code-quality.md) - Ruff, pre-commit hooks, and style guidelines
- [Testing](./contributing/testing.md) - Write and run tests
- [Pull Requests](./contributing/pull-request.md) - PR process and review guidelines
- [CI/CD](./contributing/ci-cd.md) - GitHub Actions and release process

### Architecture

Understand the internal design and structure of the SDK.

- [Project Structure](./architecture/project-structure.md) - Codebase organization

### API Reference

Detailed API documentation auto-generated from source code.

- [Clients Reference](./reference/synapse_sdk/clients/index.md) - HTTP client internals
- [Plugins Reference](./reference/synapse_sdk/plugins/index.md) - Plugin system internals
- [Utilities Reference](./reference/synapse_sdk/utils/index.md) - Utility modules
- [CLI Reference](./reference/synapse_sdk/cli/index.md) - CLI implementation
