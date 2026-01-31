"""Integration tests for upload workflow."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from synapse_sdk.plugins.actions.upload import (
    BaseUploadAction,
    DefaultUploadAction,
    UploadContext,
    UploadParams,
)
from synapse_sdk.plugins.actions.upload.steps import (
    AnalyzeCollectionStep,
    CleanupStep,
    GenerateDataUnitsStep,
    InitializeStep,
    OrganizeFilesStep,
    ProcessMetadataStep,
    UploadFilesStep,
    ValidateFilesStep,
)
from synapse_sdk.plugins.context import RuntimeContext
from synapse_sdk.plugins.steps import Orchestrator, StepRegistry, StepResult


class TestOrchestratorIntegration:
    """Test orchestrator with upload steps."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.logger = MagicMock()
        ctx.job_id = 'test-job-123'
        return ctx

    @pytest.fixture
    def upload_context(self, mock_runtime_ctx):
        """Create UploadContext."""
        return UploadContext(
            params={
                'name': 'Test Upload',
                'path': '/data/images',
                'storage': 1,
                'data_collection': 1,
                'use_single_path': True,
            },
            runtime_ctx=mock_runtime_ctx,
        )

    def test_registry_accepts_all_steps(self):
        """Test StepRegistry accepts all upload steps."""
        registry = StepRegistry()

        registry.register(InitializeStep())
        registry.register(ProcessMetadataStep(None))
        registry.register(AnalyzeCollectionStep())
        registry.register(OrganizeFilesStep(None))
        registry.register(ValidateFilesStep(None))
        registry.register(UploadFilesStep(None))
        registry.register(GenerateDataUnitsStep(None))
        registry.register(CleanupStep())

        assert len(registry) == 8

    def test_orchestrator_creation(self, upload_context):
        """Test Orchestrator can be created with upload context."""
        registry = StepRegistry()
        registry.register(InitializeStep())

        orchestrator = Orchestrator(
            registry=registry,
            context=upload_context,
        )

        assert orchestrator is not None

    def test_orchestrator_with_progress_callback(self, upload_context):
        """Test Orchestrator accepts progress callback."""
        registry = StepRegistry()
        registry.register(InitializeStep())

        progress_values = []

        def progress_callback(current, total):
            progress_values.append((current, total))

        orchestrator = Orchestrator(
            registry=registry,
            context=upload_context,
            progress_callback=progress_callback,
        )

        assert orchestrator is not None


class TestStepExecution:
    """Test individual step execution."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.client.get_storage.return_value = {
            'id': 1,
            'name': 'Test Storage',
            'provider': 'local',
            'default_path': '/data',
        }
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def context_single_path(self, mock_runtime_ctx):
        """Create single-path mode context."""
        return UploadContext(
            params={
                'name': 'Test Upload',
                'path': '/data/images',
                'storage': 1,
                'data_collection': 1,
                'use_single_path': True,
            },
            runtime_ctx=mock_runtime_ctx,
        )

    def test_initialize_step_validates_storage(self, context_single_path):
        """Test InitializeStep validates and retrieves storage."""
        step = InitializeStep()

        # Mock get_pathlib to avoid filesystem access
        with patch('synapse_sdk.plugins.actions.upload.steps.initialize.get_pathlib') as mock_pathlib:
            from pathlib import Path

            mock_pathlib.return_value = Path('/data/images')
            result = step.execute(context_single_path)

        assert result.success is True
        assert context_single_path.storage is not None

    def test_initialize_step_fails_without_storage_param(self, mock_runtime_ctx):
        """Test InitializeStep fails when storage param is missing."""
        context = UploadContext(
            params={
                'name': 'Test',
                'path': '/data',
                # storage is missing
            },
            runtime_ctx=mock_runtime_ctx,
        )

        step = InitializeStep()
        result = step.execute(context)

        assert result.success is False
        assert 'Storage' in result.error

    def test_initialize_step_fails_without_path_in_single_mode(self, mock_runtime_ctx):
        """Test InitializeStep fails without path in single-path mode."""
        mock_runtime_ctx.client.get_storage.return_value = {'id': 1}

        context = UploadContext(
            params={
                'name': 'Test',
                'storage': 1,
                'use_single_path': True,
                # path is missing
            },
            runtime_ctx=mock_runtime_ctx,
        )

        step = InitializeStep()
        result = step.execute(context)

        assert result.success is False
        assert 'path' in result.error.lower() or 'Path' in result.error

    def test_cleanup_step_always_succeeds(self, context_single_path):
        """Test CleanupStep succeeds even with no temp files."""
        step = CleanupStep()
        result = step.execute(context_single_path)

        assert result.success is True


class TestStepRollback:
    """Test step rollback functionality."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.logger = MagicMock()
        return ctx

    @pytest.fixture
    def context(self, mock_runtime_ctx):
        """Create context."""
        return UploadContext(
            params={'name': 'Test'},
            runtime_ctx=mock_runtime_ctx,
        )

    def test_initialize_step_rollback_clears_state(self, context):
        """Test InitializeStep rollback clears context state."""
        # Set some state
        context.storage = {'id': 1}
        context.pathlib_cwd = '/data'

        step = InitializeStep()
        result = StepResult(
            success=True,
            rollback_data={'storage_id': 1, 'path': '/data'},
        )

        step.rollback(context, result)

        assert context.storage is None
        assert context.pathlib_cwd is None

    def test_cleanup_step_rollback_is_noop(self, context):
        """Test CleanupStep rollback does nothing (as expected)."""
        step = CleanupStep()
        result = StepResult(success=True)

        # Should not raise
        step.rollback(context, result)


class TestDefaultUploadActionIntegration:
    """Test DefaultUploadAction integration."""

    def test_action_setup_steps_returns_all_8_steps(self):
        """Test that setup_steps registers all 8 workflow steps."""

        class TestUploadAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestUploadAction)
        action.setup_steps(registry)

        step_names = [step.name for step in registry._steps]

        expected_steps = [
            'initialize',
            'process_metadata',
            'analyze_collection',
            'organize_files',
            'validate_files',
            'upload_files',
            'generate_data_units',
            'cleanup',
        ]

        assert step_names == expected_steps

    def test_action_step_weights_sum_to_100(self):
        """Test that step weights sum to 100%."""

        class TestUploadAction(DefaultUploadAction[UploadParams]):
            action_name = 'test_upload'
            params_model = UploadParams

        registry = StepRegistry()
        action = object.__new__(TestUploadAction)
        action.setup_steps(registry)

        total_weight = sum(step.progress_weight for step in registry._steps)

        assert abs(total_weight - 1.0) < 0.001


class TestCustomUploadAction:
    """Test custom upload action with subset of steps."""

    def test_custom_action_with_subset_of_steps(self):
        """Test creating action with custom subset of steps."""

        class MinimalUploadAction(BaseUploadAction[UploadParams]):
            action_name = 'minimal_upload'
            params_model = UploadParams

            def setup_steps(self, registry):
                registry.register(InitializeStep())
                registry.register(CleanupStep())

        registry = StepRegistry()
        action = object.__new__(MinimalUploadAction)
        action.setup_steps(registry)

        assert len(registry) == 2
        assert registry._steps[0].name == 'initialize'
        assert registry._steps[1].name == 'cleanup'

    def test_empty_action_has_no_steps(self):
        """Test that base action with no steps is empty."""

        class EmptyUploadAction(BaseUploadAction[UploadParams]):
            action_name = 'empty_upload'
            params_model = UploadParams

            # Don't override setup_steps - uses base which does nothing

        registry = StepRegistry()
        action = object.__new__(EmptyUploadAction)
        action.setup_steps(registry)

        assert len(registry) == 0


class TestWorkflowErrorHandling:
    """Test workflow error handling and recovery."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.client.get_storage.side_effect = Exception('Storage service unavailable')
        ctx.logger = MagicMock()
        return ctx

    def test_step_returns_error_on_client_failure(self, mock_runtime_ctx):
        """Test step returns error when client fails."""
        context = UploadContext(
            params={
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'use_single_path': True,
            },
            runtime_ctx=mock_runtime_ctx,
        )

        step = InitializeStep()
        result = step.execute(context)

        assert result.success is False
        assert 'Storage service unavailable' in result.error


class TestContextSharing:
    """Test context sharing between steps."""

    @pytest.fixture
    def mock_runtime_ctx(self):
        """Create mock RuntimeContext."""
        ctx = MagicMock(spec=RuntimeContext)
        ctx.client = MagicMock()
        ctx.client.get_storage.return_value = {'id': 1, 'name': 'Test'}
        ctx.logger = MagicMock()
        return ctx

    def test_step_modifies_context_for_next_step(self, mock_runtime_ctx):
        """Test that step modifications persist in context."""
        context = UploadContext(
            params={
                'name': 'Test',
                'path': '/data',
                'storage': 1,
                'use_single_path': True,
            },
            runtime_ctx=mock_runtime_ctx,
        )

        # Verify initial state
        assert context.storage is None

        # Execute step
        step = InitializeStep()
        with patch('synapse_sdk.plugins.actions.upload.steps.initialize.get_pathlib'):
            step.execute(context)

        # Verify state is modified
        assert context.storage is not None
        assert context.storage['id'] == 1
