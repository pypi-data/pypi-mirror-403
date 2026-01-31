"""Integration tests for automatic category with step execution (T036)."""

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
class MockRuntimeContext:
    """Mock RuntimeContext that records all calls."""

    progress_calls: list[tuple[int, int, str | None]] = field(default_factory=list)
    metrics_calls: list[tuple[dict, str]] = field(default_factory=list)
    log_calls: list[tuple[str, dict]] = field(default_factory=list)

    def log(self, event: str, data: dict, file: str | None = None) -> None:
        self.log_calls.append((event, data))

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        self.progress_calls.append((current, total, category))

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        self.metrics_calls.append((value, category))


@dataclass
class TestContext(BaseStepContext):
    """Test context for integration testing."""

    data: list[str] = field(default_factory=list)


class ProgressReportingStep(BaseStep[TestContext]):
    """Step that reports progress without explicit category."""

    def __init__(self, step_name: str, items: int = 10):
        self._name = step_name
        self._items = items

    @property
    def name(self) -> str:
        return self._name

    @property
    def progress_weight(self) -> float:
        return 0.5

    def execute(self, context: TestContext) -> StepResult:
        # Report progress without specifying category
        for i in range(self._items):
            context.set_progress(i + 1, self._items)

        # Also set metrics without category
        context.set_metrics({'processed': self._items})

        context.data.append(self._name)
        return StepResult(success=True)


class TestAutoCategoryIntegration:
    """T036: Integration test for automatic category during step execution."""

    def test_progress_and_metrics_use_step_name_as_category(self):
        """When step calls set_progress/set_metrics, step name should be auto-category."""
        runtime_ctx = MockRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(ProgressReportingStep('validate', items=3))
        registry.register(ProgressReportingStep('upload', items=2))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Check that progress calls used step names as categories
        validate_progress = [p for p in runtime_ctx.progress_calls if p[2] == 'validate']
        upload_progress = [p for p in runtime_ctx.progress_calls if p[2] == 'upload']

        assert len(validate_progress) == 3  # 3 items in validate step
        assert len(upload_progress) == 2  # 2 items in upload step

        # Check metrics
        validate_metrics = [m for m in runtime_ctx.metrics_calls if m[1] == 'validate']
        upload_metrics = [m for m in runtime_ctx.metrics_calls if m[1] == 'upload']

        assert len(validate_metrics) == 1
        assert len(upload_metrics) == 1
        assert validate_metrics[0][0] == {'processed': 3}
        assert upload_metrics[0][0] == {'processed': 2}

    def test_explicit_category_overrides_auto_category(self):
        """Explicit category should override auto-category even during step execution."""

        class MixedCategoryStep(BaseStep[TestContext]):
            @property
            def name(self) -> str:
                return 'my_step'

            @property
            def progress_weight(self) -> float:
                return 0.5

            def execute(self, context: TestContext) -> StepResult:
                # Auto category
                context.set_progress(1, 2)
                # Explicit category
                context.set_progress(2, 2, category='custom')
                return StepResult(success=True)

        runtime_ctx = MockRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(MixedCategoryStep())

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # First call should use step name, second should use custom
        assert runtime_ctx.progress_calls[0] == (1, 2, 'my_step')
        assert runtime_ctx.progress_calls[1] == (2, 2, 'custom')
