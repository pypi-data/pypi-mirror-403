"""Tests for upload module imports."""


class TestUploadModuleImports:
    """Test that upload module exports are accessible."""

    def test_action_imports(self):
        """Test action classes are importable."""
        from synapse_sdk.plugins.actions.upload import (
            BaseUploadAction,
            DefaultUploadAction,
        )

        assert BaseUploadAction is not None
        assert DefaultUploadAction is not None

    def test_step_imports(self):
        """Test all 8 workflow steps are importable."""
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

        steps = [
            InitializeStep,
            ProcessMetadataStep,
            AnalyzeCollectionStep,
            OrganizeFilesStep,
            ValidateFilesStep,
            UploadFilesStep,
            GenerateDataUnitsStep,
            CleanupStep,
        ]
        assert len(steps) == 8
        assert all(s is not None for s in steps)

    def test_context_import(self):
        """Test UploadContext is importable."""
        from synapse_sdk.plugins.actions.upload import UploadContext

        assert UploadContext is not None

    def test_enum_imports(self):
        """Test enum classes are importable."""
        from synapse_sdk.plugins.actions.upload import (
            LOG_MESSAGES,
            VALIDATION_ERROR_MESSAGES,
            LogCode,
            LogLevel,
            UploadStatus,
            ValidationErrorCode,
        )

        assert LogCode is not None
        assert LogLevel is not None
        assert UploadStatus is not None
        assert ValidationErrorCode is not None
        assert LOG_MESSAGES is not None
        assert VALIDATION_ERROR_MESSAGES is not None

    def test_model_imports(self):
        """Test model classes are importable."""
        from synapse_sdk.plugins.actions.upload import (
            AssetConfig,
            ExcelSecurityConfig,
            UploadParams,
        )

        assert UploadParams is not None
        assert AssetConfig is not None
        assert ExcelSecurityConfig is not None

    def test_exception_imports(self):
        """Test exception classes are importable."""
        from synapse_sdk.plugins.actions.upload import (
            ExcelParsingError,
            ExcelSecurityError,
            FileProcessingError,
            FileUploadError,
            FileValidationError,
            UploadError,
        )

        exceptions = [
            UploadError,
            ExcelSecurityError,
            ExcelParsingError,
            FileUploadError,
            FileValidationError,
            FileProcessingError,
        ]
        assert all(e is not None for e in exceptions)

    def test_strategy_base_imports(self):
        """Test strategy base classes are importable."""
        from synapse_sdk.plugins.actions.upload import (
            DataUnitStrategy,
            FileDiscoveryStrategy,
            MetadataStrategy,
            UploadConfig,
            UploadStrategy,
            ValidationResult,
            ValidationStrategy,
        )

        assert ValidationResult is not None
        assert UploadConfig is not None
        assert ValidationStrategy is not None
        assert FileDiscoveryStrategy is not None
        assert MetadataStrategy is not None
        assert UploadStrategy is not None
        assert DataUnitStrategy is not None

    def test_strategy_implementation_imports(self):
        """Test strategy implementations are importable."""
        from synapse_sdk.plugins.actions.upload import (
            BatchDataUnitStrategy,
            DefaultValidationStrategy,
            ExcelMetadataStrategy,
            FlatFileDiscoveryStrategy,
            NoneMetadataStrategy,
            RecursiveFileDiscoveryStrategy,
            SingleDataUnitStrategy,
            SyncUploadStrategy,
        )

        strategies = [
            DefaultValidationStrategy,
            FlatFileDiscoveryStrategy,
            RecursiveFileDiscoveryStrategy,
            ExcelMetadataStrategy,
            NoneMetadataStrategy,
            SyncUploadStrategy,
            SingleDataUnitStrategy,
            BatchDataUnitStrategy,
        ]
        assert all(s is not None for s in strategies)
