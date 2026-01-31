"""Dataset log message codes for user-facing UI messages."""

from __future__ import annotations

from synapse_sdk.plugins.log_messages import LogMessageCode, register_log_messages


class DatasetLogMessageCode(LogMessageCode):
    """Log message codes for dataset download and conversion workflows."""

    DATASET_DOWNLOAD_STARTING = ('DATASET_DOWNLOAD_STARTING', 'info')
    DATASET_SPLIT_DOWNLOADED = ('DATASET_SPLIT_DOWNLOADED', 'info')
    DATASET_DOWNLOAD_COMPLETED = ('DATASET_DOWNLOAD_COMPLETED', 'success')
    DATASET_GT_EVENTS_FOUND = ('DATASET_GT_EVENTS_FOUND', 'info')
    DATASET_DOWNLOAD_PARTIAL = ('DATASET_DOWNLOAD_PARTIAL', 'warning')
    DATASET_CONVERTING = ('DATASET_CONVERTING', 'info')
    DATASET_CONVERSION_COMPLETED = ('DATASET_CONVERSION_COMPLETED', 'success')


register_log_messages({
    DatasetLogMessageCode.DATASET_DOWNLOAD_STARTING: 'Starting dataset download (ID: {dataset_id})',
    DatasetLogMessageCode.DATASET_SPLIT_DOWNLOADED: 'Downloaded {split_name} split: {count} items',
    DatasetLogMessageCode.DATASET_DOWNLOAD_COMPLETED: 'Dataset download complete: {count} items',
    DatasetLogMessageCode.DATASET_GT_EVENTS_FOUND: 'Found {count} ground truth events',
    DatasetLogMessageCode.DATASET_DOWNLOAD_PARTIAL: 'Downloaded {downloaded} items ({missing} missing images)',
    DatasetLogMessageCode.DATASET_CONVERTING: 'Converting dataset: {source} \u2192 {target}',
    DatasetLogMessageCode.DATASET_CONVERSION_COMPLETED: 'Dataset conversion complete',
})


__all__ = ['DatasetLogMessageCode']
