"""Test LogLevel enum functionality.

These tests verify that log() accepts LogLevel enum and handles
level correctly.
"""

import pytest

from synapse_sdk.loggers import NoOpLogger
from synapse_sdk.plugins.models.logger import LogLevel


class TestLogLevelEnum:
    """Test LogLevel enum values."""

    def test_log_level_values(self) -> None:
        """LogLevel enum should have correct values."""
        assert LogLevel.DEBUG.value == 'debug'
        assert LogLevel.INFO.value == 'info'
        assert LogLevel.WARNING.value == 'warning'
        assert LogLevel.ERROR.value == 'error'
        assert LogLevel.CRITICAL.value == 'critical'


class TestLogWithLevel:
    """Test log() method with LogLevel parameter."""

    def test_log_with_info_level(self) -> None:
        """log() with LogLevel.INFO should work correctly."""

        class TestLogger(NoOpLogger):
            last_level: LogLevel | None = None

            def _log_impl(
                self,
                event: str,
                data: dict,
                file: str | None,
                step: str | None,
                level: LogLevel | None = None,
            ) -> None:
                # Import here to avoid any type issues
                self.last_level = level

        logger = TestLogger()
        logger.log(LogLevel.INFO, 'test_event', {'key': 'value'})
        assert logger.last_level == LogLevel.INFO

    def test_log_with_debug_level(self) -> None:
        """log() with LogLevel.DEBUG should work correctly."""

        class TestLogger(NoOpLogger):
            last_level: LogLevel | None = None

            def _log_impl(
                self,
                event: str,
                data: dict,
                file: str | None,
                step: str | None,
                level: LogLevel | None = None,
            ) -> None:
                self.last_level = level

        logger = TestLogger()
        logger.log(LogLevel.DEBUG, 'debug_event', {})
        assert logger.last_level == LogLevel.DEBUG

    def test_log_with_string_raises_type_error(self) -> None:
        """log() with string instead of LogLevel should raise TypeError."""
        logger = NoOpLogger()

        with pytest.raises(TypeError, match='level must be a LogLevel enum'):
            logger.log('info', 'test_event', {'key': 'value'})  # type: ignore


class TestConvenienceMethods:
    """Test that convenience methods (info, debug, warning, error) still work."""

    def test_info_method(self) -> None:
        """info() method should still work."""
        logger = NoOpLogger()
        # Should not raise
        logger.info('test message')

    def test_debug_method(self) -> None:
        """debug() method should still work."""
        logger = NoOpLogger()
        logger.debug('test message')

    def test_warning_method(self) -> None:
        """warning() method should still work."""
        logger = NoOpLogger()
        logger.warning('test message')

    def test_error_method(self) -> None:
        """error() method should still work."""
        logger = NoOpLogger()
        logger.error('test message')

    def test_critical_method(self) -> None:
        """critical() method should still work."""
        logger = NoOpLogger()
        logger.critical('test message')
