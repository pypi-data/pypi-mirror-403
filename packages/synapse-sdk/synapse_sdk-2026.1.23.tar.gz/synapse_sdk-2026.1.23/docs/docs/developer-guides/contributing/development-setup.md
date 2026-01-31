---
id: development-setup
title: Development Setup
sidebar_label: Development Setup
sidebar_position: 2
---

# Development Setup

This guide covers setting up your local development environment for Synapse SDK.

## Prerequisites

Before contributing, ensure you have:

- **Python 3.12 or higher** (required)
- **Git** for version control
- **uv** package manager (recommended) or pip

### Installing uv

**macOS/Linux:**

```bash title="Install uv (macOS/Linux)"
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**

```bash title="Install uv (Windows)"
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

## Using uv (Recommended)

```bash title="Setup with uv"
# Create virtual environment with Python 3.12
make uv-venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies including dev extras
make uv-install
```

Or run both steps at once:

```bash title="Quick setup"
make uv-setup
```

## Using pip (Alternative)

```bash title="Setup with pip"
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with all extras
pip install -e ".[dev,test]"
```

## Available Makefile Commands

| Command | Description |
|---------|-------------|
| `make uv-venv` | Create virtual environment with Python 3.12 |
| `make uv-install` | Install all dependencies |
| `make uv-setup` | Create venv and install dependencies |
| `make uv-clean-venv` | Remove virtual environment |
| `make test` | Run all tests |
| `make test-coverage` | Run tests with coverage report |
| `make docs` | Start documentation dev server |
| `make docs-build` | Build documentation |
| `make docs-gen` | Generate API docs from docstrings |

## Verifying Installation

After setup, verify everything works:

```bash title="Verify installation"
# Check Python version
python --version  # Should be 3.12+

# Run tests
make test

# Start docs server
make run-docs
```
