"""Ultralytics YOLO callback implementations for autolog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synapse_sdk.integrations._context import get_autolog_context
from synapse_sdk.plugins.actions.train.log_messages import TrainLogMessageCode


def on_train_epoch_end(trainer: Any) -> None:
    """Log training metrics at end of each epoch.

    Logs:
        - Progress: epoch/total_epochs
        - Metrics: box_loss, cls_loss, dfl_loss (category='train')

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    epoch = trainer.epoch + 1
    total_epochs = ctx.total_epochs or getattr(trainer, 'epochs', 100)

    # Update progress
    action.set_progress(epoch, total_epochs, 'train')

    # Log epoch message (every 10 epochs or first/last)
    if epoch == 1 or epoch == total_epochs or epoch % 10 == 0:
        action.log_message(TrainLogMessageCode.TRAIN_EPOCH_PROGRESS, epoch=epoch, total_epochs=total_epochs)

    # Log loss metrics with event='metric'
    if hasattr(trainer, 'loss_items') and trainer.loss_items is not None:
        loss_items = trainer.loss_items
        if hasattr(loss_items, 'cpu'):
            loss_items = loss_items.cpu().numpy()

        action.log_metric(
            'train',
            'epoch',
            epoch,
            box_loss=float(loss_items[0]),
            cls_loss=float(loss_items[1]),
            dfl_loss=float(loss_items[2]),
        )


def on_fit_epoch_end(trainer: Any) -> None:
    """Log validation metrics after validation pass.

    Logs:
        - Metrics: mAP50, mAP50_95 (category='validation')
        - Files: validation batch prediction images

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    epoch = trainer.epoch + 1
    metrics = trainer.metrics

    if metrics:
        mAP50 = metrics.get('metrics/mAP50(B)', 0)
        mAP50_95 = metrics.get('metrics/mAP50-95(B)', 0)

        # Log validation metrics with event='metric'
        action.log_metric(
            'validation',
            'epoch',
            epoch,
            mAP50=mAP50,
            mAP50_95=mAP50_95,
        )

        # Log validation message (every 10 epochs or first)
        total_epochs = ctx.total_epochs or getattr(trainer, 'epochs', 100)
        if epoch == 1 or epoch == total_epochs or epoch % 10 == 0:
            action.log_message(TrainLogMessageCode.TRAIN_VALIDATION_METRICS, map50=mAP50, map50_95=mAP50_95)

        # Log validation sample images with event='visualization'
        save_dir = Path(trainer.save_dir)
        for i in range(3):
            img_path = save_dir / f'val_batch{i}_pred.jpg'
            if img_path.exists():
                action.log_visualization(
                    'validation',
                    str(epoch),
                    i,
                    str(img_path),
                )

    # Ray Tune integration
    env = action.ctx.env
    if hasattr(env, 'get_bool'):
        is_tune = env.get_bool('IS_TUNE', default=False)
    else:
        # Handle case where env is a dict (e.g., remote execution)
        is_tune = str(env.get('IS_TUNE', 'false')).lower() in ('true', '1', 'yes')
    if is_tune and metrics:
        try:
            from ray import tune

            tune.report(**metrics)
        except ImportError:
            pass


def on_train_end(trainer: Any) -> None:
    """Log final artifacts when training completes.

    Logs:
        - Progress: model_upload complete (to reach 100% overall)
        - Files: best.pt weights, results.csv

    Args:
        trainer: Ultralytics trainer instance.
    """
    ctx = get_autolog_context()
    if ctx is None:
        return

    action = ctx.action
    save_dir = Path(trainer.save_dir)

    action.log_message(TrainLogMessageCode.TRAIN_COMPLETED)

    # Start model upload phase
    action.set_progress(0, 1, 'model_upload')

    # Log final model weights
    best_pt = save_dir / 'weights' / 'best.pt'
    if best_pt.exists():
        action.log('model_weights', {'type': 'best'}, file=str(best_pt))
        action.log_message(TrainLogMessageCode.TRAIN_MODEL_SAVED)

    # Log training results CSV
    results_csv = save_dir / 'results.csv'
    if results_csv.exists():
        action.log('training_results', {}, file=str(results_csv))

    # Mark model upload complete (this brings overall progress to 100%)
    action.set_progress(1, 1, 'model_upload')
    action.log_message(TrainLogMessageCode.TRAIN_MODEL_UPLOADED)


__all__ = ['on_train_epoch_end', 'on_fit_epoch_end', 'on_train_end']
