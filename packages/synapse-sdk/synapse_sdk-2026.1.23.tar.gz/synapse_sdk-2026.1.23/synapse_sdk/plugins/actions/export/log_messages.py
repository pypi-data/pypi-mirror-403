"""Export log message codes for user-facing UI messages."""

from __future__ import annotations

from synapse_sdk.plugins.log_messages import LogMessageCode, register_log_messages


class ExportLogMessageCode(LogMessageCode):
    """Log message codes for export workflows."""

    EXPORT_INITIALIZED = ('EXPORT_INITIALIZED', 'info')
    EXPORT_NO_RESULTS = ('EXPORT_NO_RESULTS', 'warning')
    EXPORT_RESULTS_FETCHED = ('EXPORT_RESULTS_FETCHED', 'info')
    EXPORT_CONVERTING = ('EXPORT_CONVERTING', 'info')
    EXPORT_CONVERTED = ('EXPORT_CONVERTED', 'info')
    EXPORT_SAVING_FILES = ('EXPORT_SAVING_FILES', 'info')
    EXPORT_FILES_SAVED = ('EXPORT_FILES_SAVED', 'info')
    EXPORT_FILES_SAVED_WITH_FAILURES = ('EXPORT_FILES_SAVED_WITH_FAILURES', 'warning')
    EXPORT_COMPLETED = ('EXPORT_COMPLETED', 'success')
    EXPORT_COMPLETED_WITH_FAILURES = ('EXPORT_COMPLETED_WITH_FAILURES', 'warning')
    EXPORT_SAVING_ORIGINAL = ('EXPORT_SAVING_ORIGINAL', 'info')
    EXPORT_SAVING_JSON = ('EXPORT_SAVING_JSON', 'info')
    EXPORT_STARTING = ('EXPORT_STARTING', 'info')
    EXPORT_CONVERTING_DATASET = ('EXPORT_CONVERTING_DATASET', 'info')


register_log_messages({
    ExportLogMessageCode.EXPORT_INITIALIZED: 'Export storage and paths initialized',
    ExportLogMessageCode.EXPORT_NO_RESULTS: 'No results found for export',
    ExportLogMessageCode.EXPORT_RESULTS_FETCHED: 'Retrieved {count} results for export',
    ExportLogMessageCode.EXPORT_CONVERTING: 'Converting {count} items',
    ExportLogMessageCode.EXPORT_CONVERTED: 'Converted {count} items',
    ExportLogMessageCode.EXPORT_SAVING_FILES: 'Saving {count} files',
    ExportLogMessageCode.EXPORT_FILES_SAVED: 'Saved {count} files',
    ExportLogMessageCode.EXPORT_FILES_SAVED_WITH_FAILURES: 'Saved {success} files, {failed} failed',
    ExportLogMessageCode.EXPORT_COMPLETED: 'Export complete: {count} items exported',
    ExportLogMessageCode.EXPORT_COMPLETED_WITH_FAILURES: 'Export complete: {exported} exported, {failed} failed',
    ExportLogMessageCode.EXPORT_SAVING_ORIGINAL: 'Saving original file.',
    ExportLogMessageCode.EXPORT_SAVING_JSON: 'Saving json file.',
    ExportLogMessageCode.EXPORT_STARTING: 'Starting export process.',
    ExportLogMessageCode.EXPORT_CONVERTING_DATASET: 'Converting dataset.',
})


__all__ = ['ExportLogMessageCode']
