"""Test step-based logging functionality.

These tests verify that BaseLogger supports step-based logging:
- set_step() and get_step() methods
- log() records step in LogEntry
- set_progress() and set_metrics() use current step when not specified
"""

from synapse_sdk.loggers import NoOpLogger
from synapse_sdk.plugins.models.logger import LogLevel


class TestStepTracking:
    """Test set_step() and get_step() methods."""

    def test_get_step_returns_none_initially(self) -> None:
        """get_step() should return None when no step is set."""
        logger = NoOpLogger()
        assert logger.get_step() is None

    def test_set_step_updates_current_step(self) -> None:
        """set_step() should update the current step."""
        logger = NoOpLogger()
        logger.set_step('training')
        assert logger.get_step() == 'training'

    def test_set_step_can_clear_step(self) -> None:
        """set_step(None) should clear the current step."""
        logger = NoOpLogger()
        logger.set_step('training')
        logger.set_step(None)
        assert logger.get_step() is None


class TestLogWithStep:
    """Test log() method with step parameter."""

    def test_log_includes_explicit_step(self) -> None:
        """log() with explicit step should include it in LogEntry."""

        class TestLogger(NoOpLogger):
            last_step: str | None = None

            def _log_impl(
                self,
                event: str,
                data: dict,
                file: str | None,
                step: str | None,
                level: LogLevel | None = None,
            ) -> None:
                self.last_step = step

        logger = TestLogger()
        logger.log(LogLevel.INFO, 'test_event', {'key': 'value'}, step='explicit_step')
        assert logger.last_step == 'explicit_step'

    def test_log_uses_current_step_when_not_specified(self) -> None:
        """log() should use current step when step is not specified."""
        logger = NoOpLogger()
        logger.set_step('training')
        # After implementation, log() without step should use 'training'
        logger.log(LogLevel.INFO, 'test_event', {'key': 'value'})

    def test_log_without_step_when_none_set(self) -> None:
        """log() should work without step when none is set (backward compatibility)."""
        logger = NoOpLogger()
        # Should not raise error
        logger.log(LogLevel.INFO, 'test_event', {'key': 'value'})


class TestProgressWithStep:
    """Test set_progress() with step parameter."""

    def test_set_progress_with_explicit_step(self) -> None:
        """set_progress() with explicit step should use that step as key."""
        logger = NoOpLogger()
        logger.set_progress(50, 100, step='training')
        # Progress should be stored with 'training' as key
        progress = logger.get_progress('training')
        assert progress is not None
        assert progress.percent == 50.0

    def test_set_progress_uses_current_step(self) -> None:
        """set_progress() should use current step when not specified."""
        logger = NoOpLogger()
        logger.set_step('validation')
        logger.set_progress(75, 100)
        # Progress should be stored with 'validation' as key
        progress = logger.get_progress('validation')
        assert progress is not None
        assert progress.percent == 75.0

    def test_set_progress_without_step_uses_default(self) -> None:
        """set_progress() without step or current step uses default key."""
        logger = NoOpLogger()
        logger.set_progress(25, 100)
        # Should still work (backward compatibility)
        progress = logger.get_progress()  # Default category
        assert progress is not None


class TestMetricsWithStep:
    """Test set_metrics() with step parameter."""

    def test_set_metrics_with_explicit_step(self) -> None:
        """set_metrics() with explicit step should use that step as key."""
        logger = NoOpLogger()
        logger.set_metrics({'accuracy': 0.95}, step='evaluation')
        metrics = logger.get_metrics('evaluation')
        assert metrics.get('accuracy') == 0.95

    def test_set_metrics_uses_current_step(self) -> None:
        """set_metrics() should use current step when not specified."""
        logger = NoOpLogger()
        logger.set_step('training')
        logger.set_metrics({'loss': 0.1})
        metrics = logger.get_metrics('training')
        assert metrics.get('loss') == 0.1

    def test_set_metrics_without_step_requires_category(self) -> None:
        """set_metrics() without step or current step should use category (backward compat)."""
        logger = NoOpLogger()
        # Current implementation requires category
        logger.set_metrics({'metric': 1}, category='default')
        metrics = logger.get_metrics('default')
        assert metrics.get('metric') == 1
