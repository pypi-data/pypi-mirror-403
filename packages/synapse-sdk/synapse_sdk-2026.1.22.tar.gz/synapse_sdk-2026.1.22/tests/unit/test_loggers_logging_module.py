"""Test Python logging module integration.

These tests verify that ConsoleLogger and BackendLogger use the
Python logging module instead of print statements.
"""

import logging

from synapse_sdk.loggers import BackendLogger, ConsoleLogger
from synapse_sdk.plugins.models.logger import LogLevel


class TestConsoleLoggerLogging:
    """Test ConsoleLogger uses logging module."""

    def test_console_logger_uses_logging_module(self, caplog: logging.LogRecord) -> None:
        """ConsoleLogger should use logging module for output."""
        logger = ConsoleLogger()

        with caplog.at_level(logging.INFO, logger='synapse_sdk.loggers'):
            logger.log(LogLevel.INFO, 'test_event', {'key': 'value'})

        # Check that a log record was captured
        assert len(caplog.records) >= 1
        # Find the record for our log
        log_messages = [r.message for r in caplog.records]
        assert any('test_event' in msg for msg in log_messages)

    def test_console_logger_respects_log_level(self, caplog: logging.LogRecord) -> None:
        """ConsoleLogger should respect logging level filtering."""
        logger = ConsoleLogger()

        with caplog.at_level(logging.WARNING, logger='synapse_sdk.loggers'):
            logger.log(LogLevel.DEBUG, 'debug_event', {})
            logger.log(LogLevel.INFO, 'info_event', {})
            logger.log(LogLevel.WARNING, 'warning_event', {})
            logger.log(LogLevel.ERROR, 'error_event', {})

        # Only WARNING and ERROR should be captured
        log_messages = [r.message for r in caplog.records]
        assert not any('debug_event' in msg for msg in log_messages)
        assert not any('info_event' in msg for msg in log_messages)
        assert any('warning_event' in msg for msg in log_messages)
        assert any('error_event' in msg for msg in log_messages)


class TestBackendLoggerLogging:
    """Test BackendLogger uses logging module for internal errors."""

    def test_backend_logger_logs_errors_to_logging(self, caplog: logging.LogRecord) -> None:
        """BackendLogger should use logging module for internal errors."""

        class FailingBackend:
            def publish_progress(self, job_id: str, progress) -> None:
                raise RuntimeError('Backend error')

            def publish_metrics(self, job_id: str, metrics) -> None:
                raise RuntimeError('Backend error')

            def publish_log(self, job_id: str, log_entry) -> None:
                raise RuntimeError('Backend error')

        backend = FailingBackend()
        logger = BackendLogger(backend, 'test-job')

        with caplog.at_level(logging.ERROR, logger='synapse_sdk.loggers'):
            logger.set_progress(50, 100, step='test')

        # Should have logged the error
        error_records = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert len(error_records) >= 1
