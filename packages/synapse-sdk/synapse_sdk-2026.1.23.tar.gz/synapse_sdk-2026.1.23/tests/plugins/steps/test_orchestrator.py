"""Tests for Orchestrator with current_step tracking (T035)."""

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest

from synapse_sdk.plugins.steps import (
    BaseStep,
    BaseStepContext,
    Orchestrator,
    StepRegistry,
    StepResult,
)


@dataclass
class MockRuntimeContext:
    """Mock RuntimeContext for testing."""

    logger: MagicMock = field(default_factory=MagicMock)

    def log(self, event: str, data: dict, file: str | None = None) -> None:
        self.logger.log(event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        self.logger.set_progress(current, total, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        self.logger.set_metrics(value, category)


@dataclass
class TestContext(BaseStepContext):
    """Test context for testing."""

    data: list[str] = field(default_factory=list)
    step_history: list[str | None] = field(default_factory=list)


class RecordingStep(BaseStep[TestContext]):
    """Step that records current_step during execution."""

    def __init__(self, step_name: str, weight: float = 0.5):
        self._name = step_name
        self._weight = weight

    @property
    def name(self) -> str:
        return self._name

    @property
    def progress_weight(self) -> float:
        return self._weight

    def execute(self, context: TestContext) -> StepResult:
        # Record what current_step is during execution
        context.step_history.append(context.current_step)
        context.data.append(self._name)
        return StepResult(success=True)


class TestOrchestratorCurrentStep:
    """T035: Test that Orchestrator updates current_step during execution."""

    def test_current_step_is_set_during_execution(self):
        """Orchestrator should set current_step before each step executes."""
        runtime_ctx = MockRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(RecordingStep('step1'))
        registry.register(RecordingStep('step2'))
        registry.register(RecordingStep('step3'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # Each step should have seen its own name as current_step
        assert context.step_history == ['step1', 'step2', 'step3']

    def test_current_step_is_none_after_execution(self):
        """Orchestrator should clear current_step after all steps complete."""
        runtime_ctx = MockRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(RecordingStep('step1'))

        orchestrator = Orchestrator(registry, context)
        orchestrator.execute()

        # After execution, current_step should be cleared
        assert context.current_step is None

    def test_current_step_is_none_after_failure(self):
        """Orchestrator should clear current_step after step failure and rollback."""

        class FailingStep(BaseStep[TestContext]):
            @property
            def name(self) -> str:
                return 'failing'

            @property
            def progress_weight(self) -> float:
                return 0.5

            def execute(self, context: TestContext) -> StepResult:
                return StepResult(success=False, error='Test failure')

        runtime_ctx = MockRuntimeContext()
        context = TestContext(runtime_ctx=runtime_ctx)

        registry = StepRegistry[TestContext]()
        registry.register(RecordingStep('step1'))
        registry.register(FailingStep())

        orchestrator = Orchestrator(registry, context)

        with pytest.raises(RuntimeError, match='failing'):
            orchestrator.execute()

        # After failure and rollback, current_step should be cleared
        assert context.current_step is None
