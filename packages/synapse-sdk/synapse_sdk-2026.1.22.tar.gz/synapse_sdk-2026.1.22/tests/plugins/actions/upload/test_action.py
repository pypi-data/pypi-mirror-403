"""Tests for upload action classes."""

from synapse_sdk.plugins.actions.upload import (
    BaseUploadAction,
    DefaultUploadAction,
    UploadParams,
)
from synapse_sdk.plugins.steps import StepRegistry


class TestDefaultUploadAction:
    """Test DefaultUploadAction workflow setup."""

    def test_setup_steps_registers_8_steps(self):
        """Test that setup_steps registers all 8 workflow steps."""

        # Create a concrete subclass for testing
        class TestAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestAction)
        action.setup_steps(registry)

        assert len(registry) == 8

    def test_setup_steps_correct_order(self):
        """Test that steps are registered in the correct order."""

        class TestAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestAction)
        action.setup_steps(registry)

        expected_order = [
            'initialize',
            'process_metadata',
            'analyze_collection',
            'organize_files',
            'validate_files',
            'upload_files',
            'generate_data_units',
            'cleanup',
        ]

        actual_order = [step.name for step in registry._steps]
        assert actual_order == expected_order

    def test_setup_steps_total_weight_is_100_percent(self):
        """Test that total progress weight sums to 100%."""

        class TestAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestAction)
        action.setup_steps(registry)

        total_weight = sum(step.progress_weight for step in registry._steps)
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_setup_steps_weights_match_spec(self):
        """Test that step weights match the specification."""

        class TestAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestAction)
        action.setup_steps(registry)

        expected_weights = {
            'initialize': 0.05,
            'process_metadata': 0.10,
            'analyze_collection': 0.05,
            'organize_files': 0.15,
            'validate_files': 0.10,
            'upload_files': 0.30,
            'generate_data_units': 0.20,
            'cleanup': 0.05,
        }

        for step in registry._steps:
            expected = expected_weights[step.name]
            assert abs(step.progress_weight - expected) < 0.01, (
                f'{step.name} weight {step.progress_weight} != expected {expected}'
            )


class TestBaseUploadAction:
    """Test BaseUploadAction base class."""

    def test_base_upload_action_has_setup_steps_method(self):
        """Test that BaseUploadAction has setup_steps method."""
        assert hasattr(BaseUploadAction, 'setup_steps')

    def test_base_upload_action_has_create_context_method(self):
        """Test that BaseUploadAction has create_context method."""
        assert hasattr(BaseUploadAction, 'create_context')

    def test_base_upload_action_has_execute_method(self):
        """Test that BaseUploadAction has execute method."""
        assert hasattr(BaseUploadAction, 'execute')
