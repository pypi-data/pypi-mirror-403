"""Tests for step module import paths (T011-T014)."""


class TestNewImportPaths:
    """Test that new import paths work correctly."""

    def test_base_step_import(self):
        """T011: Test BaseStep and StepResult import from new location."""
        from synapse_sdk.plugins.steps import BaseStep, StepResult

        assert BaseStep is not None
        assert StepResult is not None
        # Verify they come from the new location
        assert 'synapse_sdk.plugins.steps.base' in str(BaseStep.__module__)
        assert 'synapse_sdk.plugins.steps.base' in str(StepResult.__module__)

    def test_context_import(self):
        """T012: Test BaseStepContext import from new location."""
        from synapse_sdk.plugins.steps import BaseStepContext

        assert BaseStepContext is not None
        assert 'synapse_sdk.plugins.steps.context' in str(BaseStepContext.__module__)

    def test_registry_import(self):
        """T013: Test StepRegistry import from new location."""
        from synapse_sdk.plugins.steps import StepRegistry

        assert StepRegistry is not None
        assert 'synapse_sdk.plugins.steps.registry' in str(StepRegistry.__module__)

    def test_orchestrator_import(self):
        """T014: Test Orchestrator import from new location."""
        from synapse_sdk.plugins.steps import Orchestrator

        assert Orchestrator is not None
        assert 'synapse_sdk.plugins.steps.orchestrator' in str(Orchestrator.__module__)

    def test_all_core_exports(self):
        """Test that all core classes are exported from __init__."""
        from synapse_sdk.plugins.steps import (
            BaseStep,
            BaseStepContext,
            Orchestrator,
            StepRegistry,
            StepResult,
        )

        # All should be accessible
        assert all([
            BaseStep,
            BaseStepContext,
            Orchestrator,
            StepRegistry,
            StepResult,
        ])
