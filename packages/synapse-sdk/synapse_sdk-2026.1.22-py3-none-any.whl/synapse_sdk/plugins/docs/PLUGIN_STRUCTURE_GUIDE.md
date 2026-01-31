# Plugin Structure Guide: Step-Based Workflows

Complete guide for structuring plugins with step orchestration, following best practices from the SDK's built-in actions.

## Overview

This guide demonstrates how to structure a plugin with step-based workflow orchestration, using the `BaseUploadAction` as a reference implementation. This pattern is recommended for complex, multi-phase operations that benefit from:

- **Modular Steps**: Each step is a separate, testable unit
- **Automatic Rollback**: Failed steps trigger automatic cleanup
- **Progress Tracking**: Weighted progress across all steps
- **Reusability**: Steps can be shared across actions
- **Maintainability**: Clear separation of concerns

---

## Recommended Directory Structure

```
my_plugin/
├── config.yaml                 # Plugin configuration
├── requirements.txt            # Python dependencies
├── setup.py                    # Package setup (optional)
│
├── my_plugin/
│   ├── __init__.py            # Plugin exports
│   │
│   ├── actions/               # Action implementations
│   │   ├── __init__.py        # Action exports
│   │   │
│   │   ├── process/           # Process action (example with steps)
│   │   │   ├── __init__.py    # Export ProcessAction, ProcessParams, etc.
│   │   │   ├── action.py      # BaseProcessAction class
│   │   │   ├── context.py     # ProcessContext (step context)
│   │   │   ├── models.py      # Pydantic models (params, results)
│   │   │   ├── enums.py       # Enums (progress categories, modes)
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   │
│   │   │   ├── steps/         # **Step implementations (separate module)**
│   │   │   │   ├── __init__.py        # Export all steps
│   │   │   │   ├── validate.py        # ValidateStep
│   │   │   │   ├── load.py            # LoadDataStep
│   │   │   │   ├── transform.py       # TransformStep
│   │   │   │   ├── process.py         # ProcessStep
│   │   │   │   └── finalize.py        # FinalizeStep
│   │   │   │
│   │   │   └── utils/         # Helper utilities (optional)
│   │   │       ├── __init__.py
│   │   │       ├── validators.py
│   │   │       └── transformers.py
│   │   │
│   │   └── simple/            # Simple action (no steps)
│   │       ├── __init__.py
│   │       └── action.py      # SimpleAction class
│   │
│   ├── common/                # Shared utilities
│   │   ├── __init__.py
│   │   ├── utils.py
│   │   └── constants.py
│   │
│   └── tests/                 # Test suite
│       ├── __init__.py
│       ├── conftest.py        # Pytest fixtures
│       ├── test_actions.py
│       └── test_steps.py
│
└── docs/
    └── README.md              # Plugin documentation
```

---

## File-by-File Breakdown

### 1. `config.yaml` - Plugin Configuration

```yaml
name: My Plugin
code: my_plugin
version: 1.0.0
category: custom

env:
  DEFAULT_BATCH_SIZE: 100
  MAX_WORKERS: 4

actions:
  process:
    name: Process Data
    description: Multi-step data processing workflow
    entrypoint: my_plugin.actions.process:ProcessAction
    method: task

  simple:
    name: Simple Action
    description: Single-step operation
    entrypoint: my_plugin.actions.simple:SimpleAction
    method: local
```

### 2. `actions/process/__init__.py` - Action Module Exports

```python
"""Process action with step-based workflow."""

from my_plugin.actions.process.action import (
    BaseProcessAction,
    DefaultProcessAction,
)
from my_plugin.actions.process.context import ProcessContext
from my_plugin.actions.process.enums import ProcessProgressCategories, ProcessMode
from my_plugin.actions.process.models import ProcessParams, ProcessResult

# Import steps for convenience
from my_plugin.actions.process.steps import (
    ValidateStep,
    LoadDataStep,
    TransformStep,
    ProcessStep,
    FinalizeStep,
)

__all__ = [
    # Action classes
    'BaseProcessAction',
    'DefaultProcessAction',
    # Context
    'ProcessContext',
    # Models
    'ProcessParams',
    'ProcessResult',
    # Enums
    'ProcessProgressCategories',
    'ProcessMode',
    # Steps
    'ValidateStep',
    'LoadDataStep',
    'TransformStep',
    'ProcessStep',
    'FinalizeStep',
]
```

### 3. `actions/process/models.py` - Pydantic Models

```python
"""Pydantic models for process action."""

from pydantic import BaseModel, Field


class ProcessParams(BaseModel):
    """Parameters for process action."""

    input_path: str = Field(..., description='Path to input data')
    output_path: str = Field(..., description='Path to output data')
    batch_size: int = Field(default=100, ge=1, le=10000)
    mode: str = Field(default='standard', pattern='^(standard|fast|thorough)$')
    validate: bool = Field(default=True, description='Run validation')


class ProcessResult(BaseModel):
    """Result schema for process action."""

    output_path: str
    processed_count: int
    errors: list[str] = []
    duration_seconds: float
```

### 4. `actions/process/enums.py` - Enumerations

```python
"""Enums for process action."""

from dataclasses import dataclass


@dataclass
class ProcessProgressCategories:
    """Standard progress category names."""

    VALIDATE: str = 'validate'
    LOAD: str = 'load'
    TRANSFORM: str = 'transform'
    PROCESS: str = 'process'
    FINALIZE: str = 'finalize'
```

### 5. `actions/process/context.py` - Step Context

```python
"""Context for process workflow steps."""

from dataclasses import dataclass, field
from pathlib import Path

from synapse_sdk.plugins.steps import BaseStepContext

from my_plugin.actions.process.models import ProcessParams


@dataclass
class ProcessContext(BaseStepContext):
    """Shared context for process workflow steps.

    Attributes:
        params: Process parameters
        input_data: Loaded input data
        transformed_data: Transformed data
        processed_count: Number of items processed
        output_path: Final output path
    """

    params: ProcessParams = field(default_factory=lambda: ProcessParams(input_path='', output_path=''))
    input_data: list[dict] = field(default_factory=list)
    transformed_data: list[dict] = field(default_factory=list)
    processed_count: int = 0
    output_path: Path | None = None
```

### 6. `actions/process/exceptions.py` - Custom Exceptions

```python
"""Custom exceptions for process action."""

from synapse_sdk.plugins.errors import PluginError


class ProcessError(PluginError):
    """Base exception for process action."""


class ValidationError(ProcessError):
    """Validation failed."""


class TransformError(ProcessError):
    """Transformation failed."""
```

### 7. `actions/process/steps/__init__.py` - **Step Module Exports**

```python
"""Process workflow steps.

Provides a 5-step workflow:
    1. ValidateStep: Validate input parameters and files
    2. LoadDataStep: Load input data from source
    3. TransformStep: Transform data to required format
    4. ProcessStep: Main processing logic
    5. FinalizeStep: Write output and cleanup

Example:
    >>> from my_plugin.actions.process.steps import (
    ...     ValidateStep,
    ...     LoadDataStep,
    ...     TransformStep,
    ...     ProcessStep,
    ...     FinalizeStep,
    ... )
    >>>
    >>> # Register steps in order
    >>> registry.register(ValidateStep())
    >>> registry.register(LoadDataStep())
    >>> # ... etc
"""

from my_plugin.actions.process.steps.finalize import FinalizeStep
from my_plugin.actions.process.steps.load import LoadDataStep
from my_plugin.actions.process.steps.process import ProcessStep
from my_plugin.actions.process.steps.transform import TransformStep
from my_plugin.actions.process.steps.validate import ValidateStep

__all__ = [
    'ValidateStep',
    'LoadDataStep',
    'TransformStep',
    'ProcessStep',
    'FinalizeStep',
]
```

### 8. `actions/process/steps/validate.py` - Example Step Implementation

```python
"""Validation step for process workflow."""

from pathlib import Path

from synapse_sdk.plugins.steps import BaseStep, StepResult

from my_plugin.actions.process.context import ProcessContext
from my_plugin.actions.process.exceptions import ValidationError


class ValidateStep(BaseStep[ProcessContext]):
    """Validate input parameters and files.

    Checks:
    - Input file exists and is readable
    - Output directory exists or can be created
    - Parameters are valid
    """

    @property
    def name(self) -> str:
        return 'validate'

    @property
    def progress_weight(self) -> float:
        return 0.10  # 10% of workflow

    def execute(self, context: ProcessContext) -> StepResult:
        """Execute validation.

        Args:
            context: Process workflow context

        Returns:
            StepResult with validation results

        Raises:
            ValidationError: If validation fails
        """
        # Validate input file
        input_path = Path(context.params.input_path)
        if not input_path.exists():
            return StepResult(
                success=False,
                error=f'Input file not found: {input_path}',
            )

        # Validate output directory
        output_path = Path(context.params.output_path)
        output_dir = output_path.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except OSError as e:
                return StepResult(
                    success=False,
                    error=f'Cannot create output directory: {e}',
                )

        # Validate parameters
        if context.params.batch_size <= 0:
            return StepResult(
                success=False,
                error=f'Invalid batch_size: {context.params.batch_size}',
            )

        return StepResult(
            success=True,
            data={'validated': True, 'input_path': str(input_path)},
        )

    def can_skip(self, context: ProcessContext) -> bool:
        """Skip validation if not required."""
        return not context.params.validate
```

### 9. `actions/process/steps/load.py` - Load Data Step

```python
"""Load data step for process workflow."""

import json
from pathlib import Path

from synapse_sdk.plugins.steps import BaseStep, StepResult

from my_plugin.actions.process.context import ProcessContext


class LoadDataStep(BaseStep[ProcessContext]):
    """Load input data from source."""

    @property
    def name(self) -> str:
        return 'load'

    @property
    def progress_weight(self) -> float:
        return 0.20  # 20% of workflow

    def execute(self, context: ProcessContext) -> StepResult:
        """Load data from input file.

        Updates context.input_data with loaded data.

        Args:
            context: Process workflow context

        Returns:
            StepResult with load statistics
        """
        input_path = Path(context.params.input_path)

        try:
            # Load data (example: JSON file)
            with open(input_path) as f:
                data = json.load(f)

            # Store in context
            context.input_data = data if isinstance(data, list) else [data]

            return StepResult(
                success=True,
                data={'loaded_count': len(context.input_data)},
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to load data: {e}',
            )
```

### 10. `actions/process/steps/transform.py` - Transform Step

```python
"""Transform step for process workflow."""

from synapse_sdk.plugins.steps import BaseStep, StepResult

from my_plugin.actions.process.context import ProcessContext


class TransformStep(BaseStep[ProcessContext]):
    """Transform data to required format."""

    @property
    def name(self) -> str:
        return 'transform'

    @property
    def progress_weight(self) -> float:
        return 0.20  # 20% of workflow

    def execute(self, context: ProcessContext) -> StepResult:
        """Transform loaded data.

        Args:
            context: Process workflow context

        Returns:
            StepResult with transformation statistics
        """
        transformed = []

        for i, item in enumerate(context.input_data):
            # Report progress
            context.set_progress(i + 1, len(context.input_data))

            # Transform item (example: add metadata)
            transformed_item = {
                'id': i,
                'original': item,
                'processed': False,
                'batch_size': context.params.batch_size,
            }
            transformed.append(transformed_item)

        # Store in context
        context.transformed_data = transformed

        return StepResult(
            success=True,
            data={'transformed_count': len(transformed)},
        )
```

### 11. `actions/process/steps/process.py` - Main Processing Step

```python
"""Main processing step for process workflow."""

from synapse_sdk.plugins.steps import BaseStep, StepResult

from my_plugin.actions.process.context import ProcessContext


class ProcessStep(BaseStep[ProcessContext]):
    """Main processing logic."""

    @property
    def name(self) -> str:
        return 'process'

    @property
    def progress_weight(self) -> float:
        return 0.40  # 40% of workflow (main work)

    def execute(self, context: ProcessContext) -> StepResult:
        """Process transformed data.

        Args:
            context: Process workflow context

        Returns:
            StepResult with processing statistics
        """
        batch_size = context.params.batch_size
        processed = 0

        for i in range(0, len(context.transformed_data), batch_size):
            batch = context.transformed_data[i : i + batch_size]

            # Report progress
            context.set_progress(min(i + batch_size, len(context.transformed_data)), len(context.transformed_data))

            # Process batch (example: mark as processed)
            for item in batch:
                item['processed'] = True
                processed += 1

        context.processed_count = processed

        return StepResult(
            success=True,
            data={'processed_count': processed},
        )
```

### 12. `actions/process/steps/finalize.py` - Finalize Step

```python
"""Finalize step for process workflow."""

import json
from pathlib import Path

from synapse_sdk.plugins.steps import BaseStep, StepResult

from my_plugin.actions.process.context import ProcessContext


class FinalizeStep(BaseStep[ProcessContext]):
    """Write output and cleanup."""

    @property
    def name(self) -> str:
        return 'finalize'

    @property
    def progress_weight(self) -> float:
        return 0.10  # 10% of workflow

    def execute(self, context: ProcessContext) -> StepResult:
        """Write processed data to output file.

        Args:
            context: Process workflow context

        Returns:
            StepResult with output information
        """
        output_path = Path(context.params.output_path)

        try:
            # Write output
            with open(output_path, 'w') as f:
                json.dump(context.transformed_data, f, indent=2)

            context.output_path = output_path

            return StepResult(
                success=True,
                data={
                    'output_path': str(output_path),
                    'written_count': len(context.transformed_data),
                },
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f'Failed to write output: {e}',
            )

    def rollback(self, context: ProcessContext, result: StepResult) -> None:
        """Clean up output file on failure.

        Args:
            context: Process workflow context
            result: Step result from execute
        """
        if context.output_path and context.output_path.exists():
            try:
                context.output_path.unlink()
                context.errors.append(f'Cleaned up output file: {context.output_path}')
            except Exception as e:
                context.errors.append(f'Failed to clean up output file: {e}')
```

### 13. `actions/process/action.py` - Action Class with Step Registration

```python
"""Process action with step-based workflow."""

from synapse_sdk.plugins import BaseAction
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry

from my_plugin.actions.process.context import ProcessContext
from my_plugin.actions.process.enums import ProcessProgressCategories
from my_plugin.actions.process.models import ProcessParams, ProcessResult
from my_plugin.actions.process.steps import (
    FinalizeStep,
    LoadDataStep,
    ProcessStep,
    TransformStep,
    ValidateStep,
)


class BaseProcessAction(BaseAction[ProcessParams]):
    """Base class for process actions with workflow step support.

    Provides a step-based workflow system:
    - Override setup_steps() to register custom steps
    - Steps execute in order with automatic rollback on failure
    - Progress tracked across all steps based on weights
    """

    category = PluginCategory.CUSTOM
    result_model = ProcessResult
    progress = ProcessProgressCategories()

    def setup_steps(self, registry: StepRegistry[ProcessContext]) -> None:
        """Register workflow steps.

        Override this method to register custom steps for your workflow.
        Steps are executed in registration order.

        Args:
            registry: StepRegistry to register steps with.
        """
        pass  # Subclasses override to add steps

    def create_context(self) -> ProcessContext:
        """Create process context for the workflow.

        Returns:
            ProcessContext instance with params and runtime context.
        """
        return ProcessContext(
            runtime_ctx=self.ctx,
            params=self.params,
        )

    def execute(self) -> ProcessResult:
        """Execute the workflow via orchestrator.

        Returns:
            ProcessResult with workflow results
        """
        import time

        start_time = time.time()

        # Create step registry
        registry = StepRegistry[ProcessContext]()

        # Let subclass register steps
        self.setup_steps(registry)

        # If no steps registered, raise error
        if not registry.get_steps():
            raise RuntimeError('No steps registered. Override setup_steps() to register workflow steps.')

        # Create context
        context = self.create_context()

        # Execute via orchestrator
        orchestrator = Orchestrator(
            registry=registry,
            context=context,
            progress_callback=None,  # Progress handled by steps
        )

        try:
            orchestrator.execute()

            # Build result from context
            duration = time.time() - start_time

            return ProcessResult(
                output_path=str(context.output_path) if context.output_path else '',
                processed_count=context.processed_count,
                errors=context.errors,
                duration_seconds=duration,
            )

        except RuntimeError as e:
            # Orchestrator already performed rollback
            raise RuntimeError(f'Process workflow failed: {e}') from e


class DefaultProcessAction(BaseProcessAction):
    """Default process action with standard 5-step workflow.

    Provides a complete workflow with all standard steps:
    1. ValidateStep (10%) - Input validation
    2. LoadDataStep (20%) - Load input data
    3. TransformStep (20%) - Transform data
    4. ProcessStep (40%) - Main processing
    5. FinalizeStep (10%) - Write output

    Use this class when you need the standard workflow without
    customization. For custom workflows, extend BaseProcessAction instead.
    """

    def setup_steps(self, registry: StepRegistry[ProcessContext]) -> None:
        """Register the standard 5-step workflow.

        Args:
            registry: StepRegistry to register steps with.
        """
        # 1. Validate - Input validation (10%)
        registry.register(ValidateStep())

        # 2. Load - Load input data (20%)
        registry.register(LoadDataStep())

        # 3. Transform - Transform data (20%)
        registry.register(TransformStep())

        # 4. Process - Main processing (40%)
        registry.register(ProcessStep())

        # 5. Finalize - Write output (10%)
        registry.register(FinalizeStep())
```

---

## Usage Examples

### 1. Using the Default Workflow

```python
from my_plugin.actions.process import DefaultProcessAction, ProcessParams

# Create action with default 5-step workflow
action = DefaultProcessAction(
    params=ProcessParams(
        input_path='data/input.json',
        output_path='data/output.json',
        batch_size=50,
    ),
    ctx=runtime_context,
)

# Execute workflow
result = action.execute()

print(f'Processed {result.processed_count} items in {result.duration_seconds:.2f}s')
print(f'Output: {result.output_path}')
```

### 2. Custom Workflow with Additional Steps

```python
from my_plugin.actions.process import BaseProcessAction, ProcessParams
from my_plugin.actions.process.steps import ValidateStep, LoadDataStep, FinalizeStep
from my_plugin.custom_steps import CustomTransformStep, CustomProcessStep

class CustomProcessAction(BaseProcessAction):
    """Custom process action with modified workflow."""

    def setup_steps(self, registry):
        """Register custom steps."""
        # Use standard validate and load
        registry.register(ValidateStep())
        registry.register(LoadDataStep())

        # Use custom transform and process
        registry.register(CustomTransformStep())
        registry.register(CustomProcessStep())

        # Use standard finalize
        registry.register(FinalizeStep())
```

### 3. Inserting Steps Dynamically

```python
class ExtendedProcessAction(DefaultProcessAction):
    """Extended workflow with additional validation."""

    def setup_steps(self, registry):
        """Register extended workflow."""
        # First register default steps
        super().setup_steps(registry)

        # Insert custom step before processing
        registry.insert_before('process', DataQualityStep())

        # Add cleanup step at the end
        registry.register(CleanupStep())
```

---

## Best Practices

### 1. **Separate Steps into Their Own Module**

✅ **Good**: Steps in separate `steps/` directory
```python
actions/process/
├── steps/
│   ├── __init__.py      # Export all steps
│   ├── validate.py
│   ├── load.py
│   └── process.py
```

❌ **Bad**: All steps in `action.py`
```python
# Don't define steps in action.py - hard to test and maintain
```

### 2. **Use Meaningful Progress Weights**

Progress weights should reflect **perceived duration** for better UX:

```python
class ValidateStep(BaseStep):
    progress_weight = 0.10   # Fast validation - 10%

class LoadDataStep(BaseStep):
    progress_weight = 0.20   # I/O operation - 20%

class ProcessStep(BaseStep):
    progress_weight = 0.50   # Main work - 50%
```

### 3. **Implement Rollback for Resource Cleanup**

```python
def rollback(self, context, result):
    """Clean up resources on failure."""
    if context.temp_file and context.temp_file.exists():
        context.temp_file.unlink()
        context.errors.append(f'Cleaned up: {context.temp_file}')
```

### 4. **Use Context for Shared State**

```python
@dataclass
class ProcessContext(BaseStepContext):
    """Shared state across all steps."""
    input_data: list = field(default_factory=list)
    output_path: Path | None = None
    processed_count: int = 0
```

### 5. **Provide Both Base and Default Action Classes**

```python
# Base class - for customization
class BaseProcessAction(BaseAction):
    def setup_steps(self, registry):
        pass  # Override in subclass

# Default class - ready to use
class DefaultProcessAction(BaseProcessAction):
    def setup_steps(self, registry):
        # Register all standard steps
        registry.register(ValidateStep())
        # ... etc
```

### 6. **Export Steps for Reusability**

```python
# steps/__init__.py
from .validate import ValidateStep
from .load import LoadDataStep

__all__ = ['ValidateStep', 'LoadDataStep']

# Now users can import and reuse
from my_plugin.actions.process.steps import ValidateStep
```

### 7. **Use Type Hints and Generics**

```python
class ProcessContext(BaseStepContext):
    """Context with proper typing."""
    params: ProcessParams  # Typed
    input_data: list[dict]  # Typed

class ValidateStep(BaseStep[ProcessContext]):  # Generic type
    """Step with typed context."""
    def execute(self, context: ProcessContext) -> StepResult:
        # IDE knows context.params is ProcessParams
        path = context.params.input_path
```

---

## Testing Steps

### Pytest Example

```python
# tests/test_steps.py
import pytest
from synapse_sdk.plugins.steps import StepResult

from my_plugin.actions.process.context import ProcessContext
from my_plugin.actions.process.models import ProcessParams
from my_plugin.actions.process.steps import ValidateStep


@pytest.fixture
def context():
    """Create test context."""
    return ProcessContext(
        params=ProcessParams(
            input_path='test_input.json',
            output_path='test_output.json',
        ),
    )


def test_validate_step_success(context, tmp_path):
    """Test validation with valid input."""
    # Create test file
    input_file = tmp_path / 'test_input.json'
    input_file.write_text('{"test": true}')
    context.params.input_path = str(input_file)
    context.params.output_path = str(tmp_path / 'output.json')

    # Execute step
    step = ValidateStep()
    result = step.execute(context)

    # Verify
    assert result.success
    assert result.data['validated']


def test_validate_step_missing_input(context):
    """Test validation with missing input file."""
    context.params.input_path = '/nonexistent/file.json'

    # Execute step
    step = ValidateStep()
    result = step.execute(context)

    # Verify
    assert not result.success
    assert 'not found' in result.error
```

---

## Related Documentation

- **[STEP.md](STEP.md)** - Detailed step implementation guide
- **[ACTION_DEV_GUIDE.md](ACTION_DEV_GUIDE.md)** - Action development guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture details
- **Upload Action Source** - `synapse_sdk/plugins/actions/upload/` for reference implementation

---

## Summary Checklist

When creating a plugin with step orchestration:

- [ ] Create separate `steps/` directory for step implementations
- [ ] Export all steps from `steps/__init__.py`
- [ ] Define `BaseStepContext` subclass for shared state
- [ ] Implement each step as `BaseStep[YourContext]` subclass
- [ ] Set meaningful `progress_weight` for each step
- [ ] Implement `rollback()` for steps that create resources
- [ ] Create both `Base` and `Default` action classes
- [ ] Use `StepRegistry` to register steps in `setup_steps()`
- [ ] Use `Orchestrator` to execute workflow in `execute()`
- [ ] Write unit tests for individual steps
- [ ] Document step workflow in action docstring

This structure ensures your plugin is maintainable, testable, and follows SDK best practices.
