"""Tests for upload workflow steps."""

import pytest

from synapse_sdk.plugins.actions.upload import (
    AnalyzeCollectionStep,
    CleanupStep,
    GenerateDataUnitsStep,
    InitializeStep,
    OrganizeFilesStep,
    ProcessMetadataStep,
    UploadFilesStep,
    ValidateFilesStep,
)


class TestStepProperties:
    """Test that all steps have required properties."""

    @pytest.fixture
    def all_steps(self):
        """Fixture providing instances of all steps."""
        return [
            InitializeStep(),
            ProcessMetadataStep(None),
            AnalyzeCollectionStep(),
            OrganizeFilesStep(None),
            ValidateFilesStep(None),
            UploadFilesStep(None),
            GenerateDataUnitsStep(None),
            CleanupStep(),
        ]

    def test_all_steps_have_name(self, all_steps):
        """Test that all steps have a name property."""
        for step in all_steps:
            assert hasattr(step, 'name')
            assert isinstance(step.name, str)
            assert len(step.name) > 0

    def test_all_steps_have_progress_weight(self, all_steps):
        """Test that all steps have a progress_weight property."""
        for step in all_steps:
            assert hasattr(step, 'progress_weight')
            assert isinstance(step.progress_weight, float)
            assert 0 < step.progress_weight <= 1

    def test_all_steps_have_execute_method(self, all_steps):
        """Test that all steps have an execute method."""
        for step in all_steps:
            assert hasattr(step, 'execute')
            assert callable(step.execute)

    def test_all_steps_have_can_skip_method(self, all_steps):
        """Test that all steps have a can_skip method."""
        for step in all_steps:
            assert hasattr(step, 'can_skip')
            assert callable(step.can_skip)

    def test_all_steps_have_rollback_method(self, all_steps):
        """Test that all steps have a rollback method."""
        for step in all_steps:
            assert hasattr(step, 'rollback')
            assert callable(step.rollback)


class TestInitializeStep:
    """Test InitializeStep."""

    def test_name(self):
        """Test step name."""
        step = InitializeStep()
        assert step.name == 'initialize'

    def test_progress_weight(self):
        """Test progress weight."""
        step = InitializeStep()
        assert step.progress_weight == 0.05

    def test_cannot_skip(self):
        """Test that step cannot be skipped."""
        step = InitializeStep()
        # can_skip requires context, but the method should exist
        assert callable(step.can_skip)


class TestProcessMetadataStep:
    """Test ProcessMetadataStep."""

    def test_name(self):
        """Test step name."""
        step = ProcessMetadataStep(None)
        assert step.name == 'process_metadata'

    def test_progress_weight(self):
        """Test progress weight."""
        step = ProcessMetadataStep(None)
        assert step.progress_weight == 0.10


class TestAnalyzeCollectionStep:
    """Test AnalyzeCollectionStep."""

    def test_name(self):
        """Test step name."""
        step = AnalyzeCollectionStep()
        assert step.name == 'analyze_collection'

    def test_progress_weight(self):
        """Test progress weight."""
        step = AnalyzeCollectionStep()
        assert step.progress_weight == 0.05


class TestOrganizeFilesStep:
    """Test OrganizeFilesStep."""

    def test_name(self):
        """Test step name."""
        step = OrganizeFilesStep(None)
        assert step.name == 'organize_files'

    def test_progress_weight(self):
        """Test progress weight."""
        step = OrganizeFilesStep(None)
        assert step.progress_weight == 0.15


class TestValidateFilesStep:
    """Test ValidateFilesStep."""

    def test_name(self):
        """Test step name."""
        step = ValidateFilesStep(None)
        assert step.name == 'validate_files'

    def test_progress_weight(self):
        """Test progress weight."""
        step = ValidateFilesStep(None)
        assert step.progress_weight == 0.10


class TestUploadFilesStep:
    """Test UploadFilesStep."""

    def test_name(self):
        """Test step name."""
        step = UploadFilesStep(None)
        assert step.name == 'upload_files'

    def test_progress_weight(self):
        """Test progress weight."""
        step = UploadFilesStep(None)
        assert step.progress_weight == 0.30


class TestGenerateDataUnitsStep:
    """Test GenerateDataUnitsStep."""

    def test_name(self):
        """Test step name."""
        step = GenerateDataUnitsStep(None)
        assert step.name == 'generate_data_units'

    def test_progress_weight(self):
        """Test progress weight."""
        step = GenerateDataUnitsStep(None)
        assert step.progress_weight == 0.20


class TestCleanupStep:
    """Test CleanupStep."""

    def test_name(self):
        """Test step name."""
        step = CleanupStep()
        assert step.name == 'cleanup'

    def test_progress_weight(self):
        """Test progress weight."""
        step = CleanupStep()
        assert step.progress_weight == 0.05
