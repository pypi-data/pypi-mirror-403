"""Base log message codes for user-facing UI messages.

Provides:
    - LogMessageCode: Base StrEnum with embedded log level for all log message codes
    - CommonLogMessageCode: General/shared message codes
    - register_log_messages: Register plugin-specific templates
    - resolve_log_message: Resolve code + kwargs into (message, level)

Each plugin defines its own LogMessageCode subclass (e.g., UploadLogMessageCode)
in its own log_messages.py module. Each member carries its log level
(e.g., 'info', 'warning', 'success'). Templates are registered at import time
via register_log_messages().
"""

from __future__ import annotations

from enum import StrEnum


class LogMessageCode(StrEnum):
    """Base class for all log message codes.

    Each member is defined as ``NAME = ('VALUE', 'level')`` where *level*
    is the UI context level (``'info'``, ``'warning'``, ``'success'``, ``'danger'``).
    The level is accessible via the ``level`` property.

    Python StrEnum allows subclassing only when the parent has no members.

    Example:
        >>> class UploadLogMessageCode(LogMessageCode):
        ...     UPLOAD_INITIALIZED = ('UPLOAD_INITIALIZED', 'info')
        ...     UPLOAD_COMPLETED = ('UPLOAD_COMPLETED', 'success')
        >>> UploadLogMessageCode.UPLOAD_INITIALIZED.level
        'info'
    """

    def __new__(cls, value: str, level: str = 'info') -> LogMessageCode:
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._level = level
        return obj

    @property
    def level(self) -> str:
        """UI context level for this log message code."""
        return self._level


class CommonLogMessageCode(LogMessageCode):
    """General/shared log message codes used across all plugins."""

    PLUGIN_RUN_COMPLETE = ('PLUGIN_RUN_COMPLETE', 'info')


# Global template registry: maps LogMessageCode members to template strings.
# Each plugin's log_messages module calls register_log_messages() at import time.
_TEMPLATE_REGISTRY: dict[LogMessageCode, str] = {}


def register_log_messages(templates: dict[LogMessageCode, str]) -> None:
    """Register log message templates into the global registry.

    Called at import time by each plugin's log_messages module.

    Args:
        templates: Mapping of code -> template_string.

    Example:
        >>> register_log_messages({
        ...     UploadLogMessageCode.UPLOAD_INITIALIZED: 'Storage initialized',
        ... })
    """
    _TEMPLATE_REGISTRY.update(templates)


def resolve_log_message(code: LogMessageCode, **kwargs: object) -> tuple[str, str]:
    """Resolve a log message code into a formatted message and level.

    The level is read from ``code.level`` (embedded in the enum member).

    Args:
        code: The log message code to resolve.
        **kwargs: Format parameters for the message template.

    Returns:
        Tuple of (formatted_message, level).

    Example:
        >>> resolve_log_message(UploadLogMessageCode.UPLOAD_FILES_UPLOADING, count=10)
        ('Uploading 10 files', 'info')
    """
    template = _TEMPLATE_REGISTRY[code]
    message = template.format(**kwargs)
    return message, code.level


# Register common templates
register_log_messages({
    CommonLogMessageCode.PLUGIN_RUN_COMPLETE: 'Plugin run is complete.',
})


__all__ = [
    'LogMessageCode',
    'CommonLogMessageCode',
    'register_log_messages',
    'resolve_log_message',
]
