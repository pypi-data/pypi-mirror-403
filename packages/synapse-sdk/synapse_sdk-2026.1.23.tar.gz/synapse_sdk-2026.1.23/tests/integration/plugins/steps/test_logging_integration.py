"""Integration tests for logging delegation through RuntimeContext (T046)."""

from dataclasses import dataclass, field
from typing import Any

from synapse_sdk.plugins.steps import (
    BaseStep,
    BaseStepContext,
    Orchestrator,
    StepRegistry,
    StepResult,
)


@dataclass
class RecordingRuntimeContext:
    """RuntimeContext that records all logging calls for verification."""

    log_calls: list[tuple[str, dict, str | None]] = field(default_factory=list)
    progress_calls: list[tuple[int, int, str | None]] = field(default_factory=list)
    metrics_calls: list[tuple[dict, str]] = field(default_factory=list)

    def log(self, event: str, data: dict, file: str | None = None) -> None:
        self.log_calls.append((event, data, file))

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        self.progress_calls.append((current, total, category))

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        self.metrics_calls.append((value, category))


@dataclass
class TestContext(BaseStepContext):
    """Test context for integration testing."""

    data: list[str] = field(default_factory=list)


class LoggingTestStep(BaseStep[TestContext]):
    """Step that uses all logging methods during execution."""

    def __init__(self, step_name: str):
        self._name = step_name

    @property
    def name(self) -> str:
        return self._name

    @property
    def progress_weight(self) -> float:
        return 1.0

    def execute(self, context: TestContext) -> StepResult:
        # Use log() method
        context.log('step_start', {'step': self._name})

        # Use set_progress() without category (should use step name)
        context.set_progress(50, 100)

        # Use set_metrics() without category (should use step name)
        context.set_metrics({'items_processed': 10})

        # Use log() with file parameter
        context.log('file_processed', {'size': 1024}, file='/path/to/file.txt')

        context.data.append(self._name)
        return StepResult(success=True)


class TestRuntimeContextLoggingIntegration:
    """T046: Integration test for logging through RuntimeContext."""

    def test_log_calls_recorded_in_runtime_context(self):
        """log() calls from step should be recorded in RuntimeContext."""
        runtime_ctx = RecordingRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(LoggingTestStep('process'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Verify log calls
        assert len(runtime_ctx.log_calls) == 2
        assert runtime_ctx.log_calls[0] == ('step_start', {'step': 'process'}, None)
        assert runtime_ctx.log_calls[1] == (
            'file_processed',
            {'size': 1024},
            '/path/to/file.txt',
        )

    def test_progress_calls_recorded_in_runtime_context(self):
        """set_progress() calls from step should be recorded in RuntimeContext."""
        runtime_ctx = RecordingRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(LoggingTestStep('validate'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Verify progress calls (auto-category should be step name)
        progress_from_step = [p for p in runtime_ctx.progress_calls if p[2] == 'validate']
        assert len(progress_from_step) == 1
        assert progress_from_step[0] == (50, 100, 'validate')

    def test_metrics_calls_recorded_in_runtime_context(self):
        """set_metrics() calls from step should be recorded in RuntimeContext."""
        runtime_ctx = RecordingRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(LoggingTestStep('upload'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Verify metrics calls (auto-category should be step name)
        assert len(runtime_ctx.metrics_calls) == 1
        assert runtime_ctx.metrics_calls[0] == ({'items_processed': 10}, 'upload')

    def test_multiple_steps_logging_isolation(self):
        """Each step's logging should use its own name as category."""
        runtime_ctx = RecordingRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(LoggingTestStep('step1'))
        registry.register(LoggingTestStep('step2'))
        registry.register(LoggingTestStep('step3'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Verify each step used its own name as category
        step1_metrics = [m for m in runtime_ctx.metrics_calls if m[1] == 'step1']
        step2_metrics = [m for m in runtime_ctx.metrics_calls if m[1] == 'step2']
        step3_metrics = [m for m in runtime_ctx.metrics_calls if m[1] == 'step3']

        assert len(step1_metrics) == 1
        assert len(step2_metrics) == 1
        assert len(step3_metrics) == 1

    def test_unified_logging_interface_across_context_and_steps(self):
        """BaseStepContext logging methods should match RuntimeContext interface."""
        runtime_ctx = RecordingRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        # Direct logging via context (not inside step)
        context.log('direct_log', {'source': 'context'})
        context.set_progress(10, 50, category='direct')

        # Set current step to allow metrics without error
        context._set_current_step('manual')
        context.set_metrics({'direct_metric': True})

        # Verify all calls reached RuntimeContext
        assert ('direct_log', {'source': 'context'}, None) in runtime_ctx.log_calls
        assert (10, 50, 'direct') in runtime_ctx.progress_calls
        assert ({'direct_metric': True}, 'manual') in runtime_ctx.metrics_calls
