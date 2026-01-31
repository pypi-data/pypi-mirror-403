"""Tests for BaseStepContext (T031-T034 auto-category, T043-T045 delegation)."""

from dataclasses import dataclass, field
from typing import Any
from unittest.mock import MagicMock

import pytest

from synapse_sdk.plugins.steps import BaseStepContext


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


class TestCurrentStepField:
    """T031: Test current_step field on BaseStepContext."""

    def test_current_step_default_is_none(self):
        """current_step should default to None."""
        ctx = BaseStepContext(runtime_ctx=MockRuntimeContext())
        assert ctx.current_step is None

    def test_current_step_can_be_set_via_internal_method(self):
        """_set_current_step() should update current_step."""
        ctx = BaseStepContext(runtime_ctx=MockRuntimeContext())
        ctx._set_current_step('validate')
        assert ctx.current_step == 'validate'

    def test_current_step_can_be_cleared(self):
        """_set_current_step(None) should clear current_step."""
        ctx = BaseStepContext(runtime_ctx=MockRuntimeContext())
        ctx._set_current_step('validate')
        ctx._set_current_step(None)
        assert ctx.current_step is None


class TestSetProgressAutoCategory:
    """T032: Test set_progress with automatic category from current_step."""

    def test_uses_current_step_when_category_not_provided(self):
        """set_progress should use current_step as category when not provided."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)
        ctx._set_current_step('validate')

        ctx.set_progress(50, 100)

        runtime_ctx.logger.set_progress.assert_called_once_with(50, 100, 'validate')

    def test_uses_none_when_no_current_step_and_no_category(self):
        """set_progress should pass None when both current_step and category are None."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.set_progress(50, 100)

        runtime_ctx.logger.set_progress.assert_called_once_with(50, 100, None)


class TestSetMetricsAutoCategory:
    """T033: Test set_metrics with automatic category from current_step."""

    def test_uses_current_step_when_category_not_provided(self):
        """set_metrics should use current_step as category when not provided."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)
        ctx._set_current_step('validate')

        ctx.set_metrics({'accuracy': 0.95})

        runtime_ctx.logger.set_metrics.assert_called_once_with({'accuracy': 0.95}, 'validate')

    def test_raises_error_when_no_category_and_no_current_step(self):
        """set_metrics should raise ValueError when no category and no current_step."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        with pytest.raises(ValueError, match='category must be provided'):
            ctx.set_metrics({'accuracy': 0.95})


class TestExplicitCategoryPriority:
    """T034: Test that explicit category takes priority over current_step."""

    def test_explicit_category_for_set_progress(self):
        """Explicit category should override current_step for set_progress."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)
        ctx._set_current_step('validate')

        ctx.set_progress(50, 100, category='custom_category')

        runtime_ctx.logger.set_progress.assert_called_once_with(50, 100, 'custom_category')

    def test_explicit_category_for_set_metrics(self):
        """Explicit category should override current_step for set_metrics."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)
        ctx._set_current_step('validate')

        ctx.set_metrics({'accuracy': 0.95}, category='custom_category')

        runtime_ctx.logger.set_metrics.assert_called_once_with({'accuracy': 0.95}, 'custom_category')


class TestLogDelegation:
    """T043: Test log() delegation to RuntimeContext."""

    def test_log_delegates_to_runtime_context(self):
        """log() should delegate to runtime_ctx.log() with all arguments."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.log('upload_start', {'count': 10})

        runtime_ctx.logger.log.assert_called_once_with('upload_start', {'count': 10}, None)

    def test_log_passes_file_parameter(self):
        """log() should pass file parameter to runtime_ctx.log()."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.log('file_processed', {'size': 1024}, file='/path/to/file.txt')

        runtime_ctx.logger.log.assert_called_once_with('file_processed', {'size': 1024}, '/path/to/file.txt')


class TestSetProgressDelegation:
    """T044: Test set_progress() delegation to RuntimeContext."""

    def test_set_progress_delegates_to_runtime_context(self):
        """set_progress() should delegate to runtime_ctx.set_progress()."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.set_progress(25, 100, category='validate')

        runtime_ctx.logger.set_progress.assert_called_once_with(25, 100, 'validate')

    def test_set_progress_with_all_parameters(self):
        """set_progress() should pass all parameters correctly."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.set_progress(75, 200, category='upload')

        runtime_ctx.logger.set_progress.assert_called_once_with(75, 200, 'upload')


class TestSetMetricsDelegation:
    """T045: Test set_metrics() delegation to RuntimeContext."""

    def test_set_metrics_delegates_to_runtime_context(self):
        """set_metrics() should delegate to runtime_ctx.set_metrics()."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        ctx.set_metrics({'accuracy': 0.95, 'loss': 0.05}, category='training')

        runtime_ctx.logger.set_metrics.assert_called_once_with({'accuracy': 0.95, 'loss': 0.05}, 'training')

    def test_set_metrics_with_complex_values(self):
        """set_metrics() should handle complex nested values."""
        runtime_ctx = MockRuntimeContext()
        ctx = BaseStepContext(runtime_ctx=runtime_ctx)

        complex_metrics = {
            'counts': {'total': 100, 'success': 95},
            'rates': [0.1, 0.2, 0.3],
        }
        ctx.set_metrics(complex_metrics, category='analysis')

        runtime_ctx.logger.set_metrics.assert_called_once_with(complex_metrics, 'analysis')
