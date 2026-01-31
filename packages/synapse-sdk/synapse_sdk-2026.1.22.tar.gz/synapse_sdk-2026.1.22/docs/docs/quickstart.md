---
id: quickstart
title: Quickstart Guide
sidebar_position: 3
---

# Quickstart Guide

Get up and running with Synapse SDK in minutes.

:::info[Prerequisites]

Before running CLI commands, ensure your environment is set up. See [Installation & Setup](./installation.md#verify-installation) for details.

```bash
# Option 1: Use uv run
uv run synapse --help

# Option 2: Activate virtual environment first
source .venv/bin/activate
synapse --help
```

:::

## CLI Overview

View all available commands:

```bash
synapse --help
```

Command groups:

- **plugin**: Create, test, and publish plugins
- **agent**: Configure agent connections
- **mcp**: MCP server for AI assistant integration

Standalone commands:

- **login**: Authenticate with Synapse backend

## Quick Commands

```bash
# Login to Synapse backend
synapse login

# Select an agent for remote execution
synapse agent select

# Create a new plugin
synapse plugin create
```

## Your First Plugin

This section walks you through creating a simple calculator plugin that adds two numbers.

### Step 1: Create a Plugin

Run the create command:

```bash
synapse plugin create
```

You'll see an interactive prompt. Follow these steps:

**1. Select plugin category** - Choose `Custom` (the simplest option for learning):

```
? Select plugin category: (Use arrow keys)
   Neural Net           Train and deploy ML models
   Export               Data format conversion
   Upload               External data import
   Smart Tool           Interactive annotation helpers
   Post Annotation      Process annotations after labeling
   Pre Annotation       Auto-generate initial annotations
   Data Validation      Pre-annotation data checks
 » Custom               Custom plugin type
```

**2. Enter plugin information**:

```
? Plugin name: Add Calculator
? Plugin code: (add-calculator)    # Press Enter to accept default
? Version: (0.1.0)                 # Press Enter to accept default
? Description: (Add Calculator plugin)
```

**3. Review and confirm** - A preview will be shown. Enter `Y` to create:

```
╭─────────── Plugin Info ───────────╮
│ Name        Add Calculator        │
│ Code        add-calculator        │
│ Version     0.1.0                 │
│ Category    Custom                │
╰───────────────────────────────────╯

? Create plugin? (Y/n)
```

After confirmation, a new directory `synapse-add-calculator-plugin/` will be created.

### Step 2: Implement the Logic

Navigate to the plugin directory and edit the main action file:

```bash
cd synapse-add-calculator-plugin
```

Open `plugin/main.py` and modify the `MainParams` class and `execute` method:

```python
"""Main action for Add Calculator."""

from __future__ import annotations

from pydantic import BaseModel

from synapse_sdk.plugins.action import BaseAction


class MainParams(BaseModel):
    """Parameters for main action."""

    a: int = 0
    b: int = 0


class MainAction(BaseAction[MainParams]):
    """Main action implementation."""

    def execute(self) -> dict:
        """Execute the main action.

        Returns:
            Action result.
        """
        result = self.params.a + self.params.b
        return {
            "sum": result,
            "expression": f"{self.params.a} + {self.params.b} = {result}",
        }
```

### Step 3: Test Locally

Test your plugin with sample parameters:

```bash
synapse plugin run main --mode local --params '{"a": 5, "b": 3}'
```

:::info[What is `main`?]
`main` is the **action name** defined in `config.yaml`. Each plugin can have multiple actions:

```yaml
# config.yaml
actions:
  main:                              # ← action name
    entrypoint: plugin.main:MainAction
    method: task
```

For example, a `neural_net` plugin might have `train` and `inference` actions, which you would run with `synapse plugin run train` or `synapse plugin run inference`.
:::

Expected output:

```json
{"sum": 8, "expression": "5 + 3 = 8"}
```

### Step 4: Publish (Optional)

Once satisfied, publish to the Synapse backend:

```bash
synapse plugin publish
```

:::tip[Next Steps]
Now that you've created your first plugin, try:
- Adding input validation
- Supporting more operations (subtract, multiply, divide)
- Exploring other plugin categories like `Neural Net` or `Export`
:::

## Next Steps

- Learn about [Plugin System](./plugins/index.md)
- Explore the [API Reference](./api/index.md)
- Check [Frequently Asked Questions](./operations/faq.md)
