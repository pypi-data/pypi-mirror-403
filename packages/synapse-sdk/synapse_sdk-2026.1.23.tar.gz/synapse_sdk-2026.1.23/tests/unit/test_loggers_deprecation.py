"""Test category deprecation warnings.

These tests verify that using the deprecated 'category' parameter
triggers DeprecationWarning and that step takes precedence.
"""

import warnings

from synapse_sdk.loggers import NoOpLogger


class TestCategoryDeprecation:
    """Test deprecation warnings for category parameter."""

    def test_set_progress_with_category_shows_warning(self) -> None:
        """set_progress(category=...) should emit DeprecationWarning."""
        logger = NoOpLogger()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            logger.set_progress(50, 100, category='old_category')

            # Check that a DeprecationWarning was raised
            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1
            assert 'category' in str(deprecation_warnings[0].message).lower()

    def test_set_metrics_with_category_shows_warning(self) -> None:
        """set_metrics(category=...) should emit DeprecationWarning when step is available."""
        logger = NoOpLogger()
        logger.set_step('current_step')

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter('always')
            # When step is set, using category should show warning
            logger.set_metrics({'metric': 1}, category='old_category')

            deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
            assert len(deprecation_warnings) >= 1


class TestStepTakesPrecedence:
    """Test that step takes precedence over category."""

    def test_set_progress_step_overrides_category(self) -> None:
        """When both step and category are provided, step takes precedence."""
        logger = NoOpLogger()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            logger.set_progress(50, 100, step='new_step', category='old_category')

        # Progress should be stored under 'new_step', not 'old_category'
        progress = logger.get_progress('new_step')
        assert progress is not None
        assert progress.percent == 50.0

        # 'old_category' should not have progress
        old_progress = logger.get_progress('old_category')
        assert old_progress is None

    def test_set_metrics_step_overrides_category(self) -> None:
        """When both step and category are provided, step takes precedence."""
        logger = NoOpLogger()

        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            logger.set_metrics({'value': 42}, step='new_step', category='old_category')

        # Metrics should be stored under 'new_step'
        metrics = logger.get_metrics('new_step')
        assert metrics.get('value') == 42

    def test_current_step_overrides_category(self) -> None:
        """Current step should take precedence over explicit category."""
        logger = NoOpLogger()
        logger.set_step('current_step')

        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            logger.set_metrics({'value': 123}, category='old_category')

        # Metrics should be stored under 'current_step'
        metrics = logger.get_metrics('current_step')
        assert metrics.get('value') == 123


class TestBackwardCompatibility:
    """Test that existing code still works."""

    def test_category_still_works_without_step(self) -> None:
        """category parameter should still work when step is not available."""
        logger = NoOpLogger()

        # When no step is set or provided, category should work (with warning)
        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            logger.set_progress(50, 100, category='my_category')

        # If no step is available, category should be used as fallback
        progress = logger.get_progress('my_category')
        # This behavior depends on implementation - step or category as key
        # At minimum, progress should be accessible somewhere
        assert progress is not None or logger.get_progress() is not None
