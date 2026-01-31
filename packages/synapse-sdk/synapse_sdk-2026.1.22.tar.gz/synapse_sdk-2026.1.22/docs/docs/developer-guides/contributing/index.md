---
id: index
title: Contributing to Synapse SDK
sidebar_label: Overview
sidebar_position: 1
---

# Contributing to Synapse SDK

Thank you for your interest in contributing to Synapse SDK.

## Quick Start

```bash title="Clone and setup"
# Clone and setup development environment
# Note: This repository may be private. Contact maintainers for access.
git clone <repository-url>
cd synapse-sdk-v2
make uv-setup

# Run tests
make test
```

:::note
This package is not yet published to PyPI. Install from source using `pip install -e ".[dev,test]"`.
:::

## Prerequisites

Before contributing, ensure you have:

- **Python 3.12 or higher** (required)
- **Git** for version control
- **uv** package manager (recommended) or pip

:::tip
This project requires Python 3.12+. Earlier versions are not supported.
:::

## Next Steps

- [Development Setup](./development-setup) - Detailed environment setup instructions
- [Code Quality](./code-quality) - Formatting, linting, and style guidelines
- [Testing](./testing) - How to write and run tests
- [Pull Requests](./pull-request) - Contribution workflow
- [CI/CD](./ci-cd) - Continuous integration and releases

## Plugin Development

For information on developing plugins (as a user of the SDK), see the [Plugin System](../../plugins/index.md) documentation.

The plugin development examples in this section are for contributors who are extending the SDK itself.

## Getting Help

- **GitHub Issues**: Report bugs or request features
- **Discussions**: Ask questions or discuss ideas
- **Documentation**: Check existing docs first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
