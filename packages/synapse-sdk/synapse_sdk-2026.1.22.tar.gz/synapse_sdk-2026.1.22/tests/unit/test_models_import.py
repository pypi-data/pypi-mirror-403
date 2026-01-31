"""Test model imports from synapse_sdk.plugins.models.

These tests verify that models can be imported from canonical locations.
"""


class TestNewImportPaths:
    """Test imports from the new synapse_sdk.plugins.models location."""

    def test_import_from_models_root(self) -> None:
        """All models should be importable from synapse_sdk.plugins.models."""
        from synapse_sdk.plugins.models import (
            ActionStatus,
            LogLevel,
            RunStatus,
        )

        # Verify enums have expected values
        assert RunStatus.RUNNING.value == 'running'
        assert ActionStatus.COMPLETED.value == 'completed'
        assert LogLevel.INFO.value == 'info'

    def test_import_from_pipeline_module(self) -> None:
        """RunStatus and ActionStatus should be importable from pipeline module."""
        from synapse_sdk.plugins.models.pipeline import ActionStatus, RunStatus

        assert RunStatus.PENDING.value == 'pending'
        assert ActionStatus.SKIPPED.value == 'skipped'

    def test_import_from_logger_module(self) -> None:
        """Logger models should be importable from logger module."""
        from synapse_sdk.plugins.models.logger import (
            LogLevel,
        )

        assert LogLevel.DEBUG.value == 'debug'
        assert LogLevel.ERROR.value == 'error'


class TestLoggerImports:
    """Test imports from synapse_sdk.loggers (canonical location)."""

    def test_import_from_loggers(self) -> None:
        """Core logger types should be importable from synapse_sdk.loggers."""
        from synapse_sdk.loggers import LogEntry, ProgressData

        # ProgressData should be a dataclass
        progress = ProgressData(percent=50.0)
        assert progress.percent == 50.0
        assert progress.status == 'running'

        # LogEntry should be a dataclass with new fields
        entry = LogEntry(event='test', data={'key': 'value'})
        assert entry.event == 'test'
        assert entry.step is None  # New field, defaults to None
        assert entry.level is None  # New field, defaults to None


class TestModelFunctionality:
    """Test that models work correctly after import."""

    def test_log_entry_to_dict(self) -> None:
        """LogEntry.to_dict() should work correctly."""
        from synapse_sdk.plugins.models import LogEntry, LogLevel

        entry = LogEntry(
            event='train_epoch',
            data={'epoch': 1, 'loss': 0.5},
            step='training',
            level=LogLevel.INFO,
        )

        result = entry.to_dict()
        assert result['event'] == 'train_epoch'
        assert result['step'] == 'training'
        assert result['level'] == 'info'

    def test_action_progress_default_status(self) -> None:
        """ActionProgress should default to PENDING status."""
        from synapse_sdk.plugins.models import ActionProgress, ActionStatus

        progress = ActionProgress(name='test_action')
        assert progress.status == ActionStatus.PENDING

    def test_pipeline_progress_default_status(self) -> None:
        """PipelineProgress should default to PENDING status."""
        from synapse_sdk.plugins.models import PipelineProgress, RunStatus

        progress = PipelineProgress(run_id='test-run')
        assert progress.status == RunStatus.PENDING
