---
id: installation
title: Installation & Setup
sidebar_position: 2
---

# Installation & Setup

Get started with Synapse SDK in minutes.

:::note[Version]

This documentation is for **v2-alpha**. PyPI installation (`pip install synapse-sdk`) is planned for a future release.

:::

## Prerequisites

Before installing Synapse SDK, ensure you have:

- **Python 3.12 or higher** installed
- **uv** (recommended) or **pip** for package management

### Installing uv (Recommended)

This project uses [uv](https://docs.astral.sh/uv/) as the recommended package manager.

```bash
# macOS (Homebrew)
brew install uv

# Linux/macOS (curl)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Installation Methods

### Install with uv (Recommended)

```bash
git clone https://github.com/datamaker-kr/synapse-sdk-v2.git
cd synapse-sdk-v2

# Sync all dependencies
uv sync

# Or install in editable mode
uv pip install -e .
```

:::tip[Running CLI commands]

After `uv sync`, use `uv run` to execute commands (e.g., `uv run synapse --version`), or activate the virtual environment first. See [Verify Installation](#verify-installation) for details.

:::

#### Install with Optional Dependencies (uv)

```bash
# Install with all dependencies (Ray, cloud storage providers, MCP)
uv pip install -e ".[all]"

# Install with multiple extras
uv pip install -e ".[dev,test,all]"
```

### Install with pip (Alternative)

If you prefer using pip directly:

```bash
git clone https://github.com/datamaker-kr/synapse-sdk-v2.git
cd synapse-sdk-v2

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -e .
```

:::tip[pip not found?]

If `pip` is not in your PATH, use Python module syntax:

```bash
python -m pip install -e .
```

:::

#### Install with Optional Dependencies (pip)

```bash
# Install with all dependencies (Ray, cloud storage providers, MCP)
pip install -e ".[all]"
```

| Extra | Description | Dependencies |
|-------|-------------|--------------|
| `all` | Ray + all cloud storage providers + MCP | ray[all], universal-pathlib, s3fs, gcsfs, sshfs, mcp |
| `test` | Testing utilities | pytest, pytest-asyncio, pytest-cov, etc. |
| `dev` | Development tools | pre-commit, ruff |
| `docs` | Documentation generation | pydoc-markdown |

## Verify Installation

After installation, verify everything is working:

```bash
# Using uv (recommended)
uv run synapse --version
uv run synapse

# Or activate virtual environment first
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

synapse --version
synapse
```

## Troubleshooting

### Common Issues

1. **ImportError: No module named 'synapse_sdk'**
   - Ensure you've activated your virtual environment
   - Check Python path: `python -c "import sys; print(sys.path)"`

2. **Connection timeout to backend**
   - Verify your API token is correct
   - Check network connectivity
   - Ensure backend URL is accessible

### Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./operations/troubleshooting.md)
2. Search [GitHub Issues](https://github.com/datamaker-kr/synapse-sdk-v2/issues)

## Next Steps

- Follow the [Quickstart Guide](./quickstart.md)
- Learn about [Plugin System](./plugins/index.md)