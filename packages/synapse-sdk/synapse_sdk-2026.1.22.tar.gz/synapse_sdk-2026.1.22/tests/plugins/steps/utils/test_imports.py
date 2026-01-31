"""Tests for utility step import paths (T015-T017)."""


class TestUtilityImports:
    """Test that utility step imports work correctly."""

    def test_logging_step_import(self):
        """T015: Test LoggingStep import from new location."""
        from synapse_sdk.plugins.steps import LoggingStep
        from synapse_sdk.plugins.steps.utils import LoggingStep as LoggingStepDirect

        assert LoggingStep is not None
        assert LoggingStepDirect is not None
        assert LoggingStep is LoggingStepDirect
        assert 'synapse_sdk.plugins.steps.utils.logging' in str(LoggingStep.__module__)

    def test_timing_step_import(self):
        """T016: Test TimingStep import from new location."""
        from synapse_sdk.plugins.steps import TimingStep
        from synapse_sdk.plugins.steps.utils import TimingStep as TimingStepDirect

        assert TimingStep is not None
        assert TimingStepDirect is not None
        assert TimingStep is TimingStepDirect
        assert 'synapse_sdk.plugins.steps.utils.timing' in str(TimingStep.__module__)

    def test_validation_step_import(self):
        """T017: Test ValidationStep import from new location."""
        from synapse_sdk.plugins.steps import ValidationStep
        from synapse_sdk.plugins.steps.utils import ValidationStep as ValidationStepDirect

        assert ValidationStep is not None
        assert ValidationStepDirect is not None
        assert ValidationStep is ValidationStepDirect
        assert 'synapse_sdk.plugins.steps.utils.validation' in str(ValidationStep.__module__)

    def test_all_utility_exports(self):
        """Test that all utility classes are exported."""
        from synapse_sdk.plugins.steps.utils import (
            LoggingStep,
            TimingStep,
            ValidationStep,
        )

        # All should be accessible
        assert all([LoggingStep, TimingStep, ValidationStep])

    def test_utilities_also_exported_from_main_module(self):
        """Test that utilities are also available from main steps module."""
        from synapse_sdk.plugins.steps import (
            LoggingStep,
            TimingStep,
            ValidationStep,
        )

        # All should be accessible from main module too
        assert all([LoggingStep, TimingStep, ValidationStep])
