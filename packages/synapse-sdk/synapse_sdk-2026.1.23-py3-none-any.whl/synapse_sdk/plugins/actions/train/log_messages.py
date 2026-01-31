"""Train log message codes for user-facing UI messages."""

from __future__ import annotations

from synapse_sdk.plugins.log_messages import LogMessageCode, register_log_messages


class TrainLogMessageCode(LogMessageCode):
    """Log message codes for training workflows."""

    TRAIN_STARTING = ('TRAIN_STARTING', 'info')
    TRAIN_EPOCH_PROGRESS = ('TRAIN_EPOCH_PROGRESS', 'info')
    TRAIN_VALIDATION_METRICS = ('TRAIN_VALIDATION_METRICS', 'info')
    TRAIN_COMPLETED = ('TRAIN_COMPLETED', 'success')
    TRAIN_MODEL_SAVED = ('TRAIN_MODEL_SAVED', 'info')
    TRAIN_MODEL_UPLOADED = ('TRAIN_MODEL_UPLOADED', 'success')


register_log_messages({
    TrainLogMessageCode.TRAIN_STARTING: 'Starting training for {epochs} epochs',
    TrainLogMessageCode.TRAIN_EPOCH_PROGRESS: 'Training epoch {epoch}/{total_epochs}',
    TrainLogMessageCode.TRAIN_VALIDATION_METRICS: 'Validation mAP50: {map50:.3f}, mAP50-95: {map50_95:.3f}',
    TrainLogMessageCode.TRAIN_COMPLETED: 'Training complete, uploading model...',
    TrainLogMessageCode.TRAIN_MODEL_SAVED: 'Model weights saved',
    TrainLogMessageCode.TRAIN_MODEL_UPLOADED: 'Model upload complete',
})


__all__ = ['TrainLogMessageCode']
