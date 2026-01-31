---
id: cli-usage
title: CLI Usage Guide
sidebar_position: 1
---

# CLI Usage Guide

The Synapse SDK provides a powerful interactive CLI for managing your development workflow, from configuration to plugin development and code editing.

:::info[Prerequisites]

Before using CLI commands, complete the [Installation Guide](../installation.md#verify-installation) and ensure your environment is set up (`uv run synapse` or activate virtual environment).

:::

## Getting Started

Show available commands and options:

```bash
synapse --help
```

Check the installed version:

```bash
synapse --version
```

## Available Commands

The CLI provides these main command groups:

- `synapse login` - Authenticate with Synapse backend
- `synapse plugin` - Plugin development and management
- `synapse agent` - Agent configuration
- `synapse mcp` - MCP server for AI assistant integration
- `synapse doctor` - Run configuration diagnostics

## Authentication

Authenticate with the Synapse backend using the `login` command:

```bash
# Interactive login
synapse login

# With token directly
synapse login --token YOUR_ACCESS_TOKEN

# With custom host
synapse login --host https://api.synapse.example.com --token YOUR_TOKEN
```

### Configuration Files

Synapse stores configuration in:
- **Credentials**: `~/.synapse/config.json` - Backend host and access token

## Plugin Management

Comprehensive plugin development and management tools:

### Create New Plugin

```bash
# Interactive wizard
synapse plugin create

# With options
synapse plugin create --name "My Plugin" --category neural_net
```

The wizard creates:
- Plugin directory structure
- Configuration files (`config.yaml`)
- Example plugin code
- Requirements and dependencies

### Run Plugin

Test plugins in different execution modes:

```bash
# Local execution (best for debugging)
synapse plugin run test --mode local

# Ray Actor execution
synapse plugin run test --mode task --gpus 1

# Ray Jobs API with log streaming
synapse plugin run train --mode job --params '{"epochs": 10}'

# Remote execution via Synapse backend
synapse plugin run deploy --mode remote
```

#### Execution Modes

| Mode | Description |
|------|-------------|
| `local` | In-process execution, best for debugging |
| `task` | Ray Actor execution (no log streaming) |
| `job` | Ray Jobs API with log streaming (recommended for remote) |
| `remote` | Run via Synapse backend API (requires auth) |

### Publish Plugin

Deploy plugins to your Synapse backend:

```bash
# Preview without uploading
synapse plugin publish --dry-run

# Publish with debug mode
synapse plugin publish --debug

# Skip confirmation prompt
synapse plugin publish --yes
```

## Command Reference

### Main Commands

```bash
synapse --help          # Show help
synapse --version       # Show version
synapse login           # Authenticate with Synapse
synapse plugin          # Plugin management commands
synapse agent           # Agent configuration commands
synapse mcp             # MCP server commands
synapse doctor          # Run configuration diagnostics
```

### Login Command

```bash
synapse login [OPTIONS]

Options:
  --host TEXT     Synapse API host
  --token, -t TEXT  Access token (will prompt if not provided)
  --help          Show this message and exit
```

### Plugin Commands

```bash
# Create a new plugin from template
synapse plugin create [OPTIONS]
  --path, -p PATH       Output directory (default: current)
  --name, -n TEXT       Plugin name
  --code TEXT           Plugin code (slug)
  --category, -c TEXT   Plugin category
  --yes, -y             Skip confirmation

# Run a plugin action
synapse plugin run ACTION [OPTIONS]
  --plugin, -p TEXT     Plugin code (auto-detects from config.yaml)
  --path PATH           Plugin directory (default: current)
  --params TEXT         JSON parameters
  --mode, -m TEXT       Executor mode: local, task, job, or remote
  --ray-address TEXT    Ray cluster address (for task/job modes)
  --gpus INTEGER        Number of GPUs to request
  --cpus INTEGER        Number of CPUs to request
  --input, -i TEXT      JSON input for inference (for infer action)
  --infer-path TEXT     Inference endpoint path (for infer action)
  --host TEXT           Synapse API host (for remote mode)
  --token, -t TEXT      Access token (for remote mode)
  --debug/--no-debug    Debug mode (default: enabled)
  --debug-sdk           Bundle local SDK with upload (for SDK development)

# Publish a plugin release
synapse plugin publish [OPTIONS]
  --path, -p PATH       Plugin directory (default: current)
  --config, -c PATH     Config file path
  --host TEXT           Synapse API host
  --token, -t TEXT      Access token
  --dry-run             Preview without uploading
  --debug               Debug mode (bypasses backend validation)
  --yes, -y             Skip confirmation

# Auto-discover actions and sync config
synapse plugin update-config [OPTIONS]
  --path, -p PATH       Plugin directory (default: current)
  --config, -c PATH     Config file path

# Job management
synapse plugin job get JOB_ID [OPTIONS]
  --host TEXT           Synapse API host
  --token, -t TEXT      Access token

synapse plugin job logs JOB_ID [OPTIONS]
  --follow, -f          Follow log output (stream)
  --host TEXT           Synapse API host
  --token, -t TEXT      Access token
```

### Agent Commands

```bash
# Interactively select an agent
synapse agent select [OPTIONS]
  --host TEXT           Synapse API host
  --token, -t TEXT      Access token

# Show current agent configuration
synapse agent show

# Clear agent configuration
synapse agent clear [OPTIONS]
  --yes, -y             Skip confirmation
```

### MCP Commands

```bash
# Start MCP server for AI assistant integration
synapse mcp serve [OPTIONS]
  --config, -c PATH     Path to config file (default: ~/.synapse/config.json)

# Initialize MCP configuration file
synapse mcp init [OPTIONS]
  --config, -c PATH     Path to config file (default: ~/.synapse/config.json)
  --force, -f           Overwrite existing config file
```

### Doctor Command

```bash
# Run diagnostics on Synapse configuration
synapse doctor
```

## Doctor Command

The `synapse doctor` command runs comprehensive diagnostics on your Synapse SDK configuration.

### Usage

```bash
synapse doctor
```

### What It Checks

The doctor command verifies:

1. **Configuration File Existence**: Ensures `~/.synapse/config.json` exists
2. **Valid JSON Format**: Validates config file is properly formatted JSON
3. **CLI Authentication**: Verifies authentication credentials are present
4. **MCP Configuration**: Checks MCP server settings
5. **Agent Configuration**: Validates agent configuration
6. **Token Validity**: Tests if authentication tokens are valid
7. **File Permissions**: Ensures config file has proper permissions (600)

### Example Output

```
✓ Configuration file exists
✓ Valid JSON format
✓ CLI authentication configured
⚠ MCP configuration has warnings
✓ Agent configuration valid
✓ Token is valid
✓ File permissions are secure
```

### Exit Codes

- `0`: All checks passed
- `1`: Errors found (must fix)

## Tips & Best Practices

### Configuration Management

1. **Token Security**: Store API tokens securely and rotate them regularly
2. **Agent Selection**: Use descriptive agent names to identify their purpose
3. **Backend URLs**: Ensure backend URLs are accessible from your development environment

### Plugin Development

1. **Local Testing**: Always test plugins locally with `--mode local` before deploying
2. **Debug Mode**: Use debug mode for initial deployments to catch issues early
3. **Version Control**: Use git to track plugin changes and manage versions
4. **Config Sync**: Run `synapse plugin update-config` after adding new actions

## Troubleshooting

### Authentication Issues

**Problem**: "Not authenticated"
- **Solution**: Run `synapse login` to set up backend connection

**Problem**: "Invalid token (401)"
- **Solution**: Generate a new API token and run `synapse login` again

**Problem**: "Connection timeout"
- **Solution**: Check network connectivity and backend URL accessibility

### Plugin Issues

**Problem**: Plugin not detected in workspace
- **Solution**: Ensure your directory has a valid `config.yaml` file

**Problem**: Plugin execution fails
- **Solution**: Check plugin dependencies and syntax, test locally first with `--mode local`

**Problem**: "No agent configured" when using remote mode
- **Solution**: Run `synapse agent select` to configure an agent

For more troubleshooting help, see the [Troubleshooting Guide](./troubleshooting.md).