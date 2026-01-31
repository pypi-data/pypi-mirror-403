"""Add-task-data log message codes for user-facing UI messages."""

from __future__ import annotations

from synapse_sdk.plugins.log_messages import LogMessageCode, register_log_messages


class AddTaskDataLogMessageCode(LogMessageCode):
    """Log message codes for add-task-data workflows."""

    TASK_DATA_ANNOTATING = ('TASK_DATA_ANNOTATING', 'info')
    TASK_DATA_COMPLETED = ('TASK_DATA_COMPLETED', 'success')
    TASK_DATA_COMPLETED_WITH_FAILURES = ('TASK_DATA_COMPLETED_WITH_FAILURES', 'warning')
    TASK_DATA_PREPROCESSOR_DEPLOYING = ('TASK_DATA_PREPROCESSOR_DEPLOYING', 'warning')


register_log_messages({
    AddTaskDataLogMessageCode.TASK_DATA_ANNOTATING: 'Annotating {count} tasks ({method} method)',
    AddTaskDataLogMessageCode.TASK_DATA_COMPLETED: 'Annotation complete: {count} tasks annotated',
    AddTaskDataLogMessageCode.TASK_DATA_COMPLETED_WITH_FAILURES: (
        'Annotation complete: {success} succeeded, {failed} failed'
    ),
    AddTaskDataLogMessageCode.TASK_DATA_PREPROCESSOR_DEPLOYING: 'Starting pre-processor deployment.',
})


__all__ = ['AddTaskDataLogMessageCode']
