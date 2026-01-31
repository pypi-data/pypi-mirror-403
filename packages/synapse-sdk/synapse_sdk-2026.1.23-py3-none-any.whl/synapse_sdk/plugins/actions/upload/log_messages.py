"""Upload log message codes for user-facing UI messages."""

from __future__ import annotations

from synapse_sdk.plugins.log_messages import LogMessageCode, register_log_messages


class UploadLogMessageCode(LogMessageCode):
    """Log message codes for upload workflows."""

    UPLOAD_INITIALIZED = ('UPLOAD_INITIALIZED', 'info')
    UPLOAD_METADATA_LOADED = ('UPLOAD_METADATA_LOADED', 'info')
    UPLOAD_COLLECTION_ANALYZED = ('UPLOAD_COLLECTION_ANALYZED', 'info')
    UPLOAD_FILES_ORGANIZED = ('UPLOAD_FILES_ORGANIZED', 'info')
    UPLOAD_NO_FILES_FOUND = ('UPLOAD_NO_FILES_FOUND', 'warning')
    UPLOAD_VALIDATION_PASSED = ('UPLOAD_VALIDATION_PASSED', 'info')
    UPLOAD_FILES_UPLOADING = ('UPLOAD_FILES_UPLOADING', 'info')
    UPLOAD_FILES_COMPLETED = ('UPLOAD_FILES_COMPLETED', 'success')
    UPLOAD_FILES_COMPLETED_WITH_FAILURES = ('UPLOAD_FILES_COMPLETED_WITH_FAILURES', 'warning')
    UPLOAD_DATA_UNITS_CREATING = ('UPLOAD_DATA_UNITS_CREATING', 'info')
    UPLOAD_DATA_UNITS_COMPLETED = ('UPLOAD_DATA_UNITS_COMPLETED', 'success')
    UPLOAD_DATA_UNITS_COMPLETED_WITH_FAILURES = ('UPLOAD_DATA_UNITS_COMPLETED_WITH_FAILURES', 'warning')
    UPLOAD_COMPLETED = ('UPLOAD_COMPLETED', 'success')


register_log_messages({
    UploadLogMessageCode.UPLOAD_INITIALIZED: 'Storage and paths initialized',
    UploadLogMessageCode.UPLOAD_METADATA_LOADED: 'Loaded metadata for {count} files',
    UploadLogMessageCode.UPLOAD_COLLECTION_ANALYZED: 'Data collection analyzed: {count} file specifications',
    UploadLogMessageCode.UPLOAD_FILES_ORGANIZED: 'Organized {count} file groups',
    UploadLogMessageCode.UPLOAD_NO_FILES_FOUND: 'No files found to organize',
    UploadLogMessageCode.UPLOAD_VALIDATION_PASSED: 'Validation passed: {count} file groups',
    UploadLogMessageCode.UPLOAD_FILES_UPLOADING: 'Uploading {count} files',
    UploadLogMessageCode.UPLOAD_FILES_COMPLETED: 'Upload complete: {success} files uploaded',
    UploadLogMessageCode.UPLOAD_FILES_COMPLETED_WITH_FAILURES: 'Upload complete: {success} succeeded, {failed} failed',
    UploadLogMessageCode.UPLOAD_DATA_UNITS_CREATING: 'Creating {count} data units',
    UploadLogMessageCode.UPLOAD_DATA_UNITS_COMPLETED: '{count} data units created',
    UploadLogMessageCode.UPLOAD_DATA_UNITS_COMPLETED_WITH_FAILURES: (
        'Data units created: {success} succeeded, {failed} failed'
    ),
    UploadLogMessageCode.UPLOAD_COMPLETED: 'Upload complete: {files} files, {data_units} data units',
})


__all__ = ['UploadLogMessageCode']
