from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.context.env import PluginEnvironment
from synapse_sdk.plugins.log_messages import CommonLogMessageCode, LogMessageCode

if TYPE_CHECKING:
    from synapse_sdk.clients.agent import AgentClient
    from synapse_sdk.clients.backend import BackendClient
    from synapse_sdk.loggers import BaseLogger


@dataclass
class RuntimeContext:
    """Runtime context injected into actions.

    Provides access to logging, environment, and client dependencies.
    All action dependencies are accessed through this context object.

    Attributes:
        logger: Logger instance for progress, metrics, and event logging.
        env: Environment variables and configuration as PluginEnvironment.
        job_id: Optional job identifier for tracking.
        client: Optional backend client for API access.
        agent_client: Optional agent client for Ray operations.
        checkpoint: Optional checkpoint info for pretrained models.
            Contains 'category' ('base' or fine-tuned) and 'path' to model.

    Example:
        >>> ctx = RuntimeContext(
        ...     logger=ConsoleLogger(),
        ...     env=PluginEnvironment.from_environ(),
        ...     job_id='job-123',
        ...     checkpoint={'category': 'base', 'path': '/models/yolov8n.pt'},
        ... )
        >>> ctx.set_progress(50, 100)
        >>> ctx.log('checkpoint', {'epoch': 5})
    """

    logger: BaseLogger
    env: PluginEnvironment
    job_id: str | None = None
    client: BackendClient | None = None
    agent_client: AgentClient | None = None
    checkpoint: dict[str, Any] | None = None

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event with data.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
        """
        from synapse_sdk.plugins.models.logger import LogLevel

        self.logger.log(LogLevel.INFO, event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress for the current operation.

        Args:
            current: Current progress value (0 to total).
            total: Total progress value.
            category: Optional category name for multi-phase progress.
        """
        self.logger.set_progress(current, total, category)

    def set_metrics(self, value: dict[str, Any], category: str) -> None:
        """Set metrics for a category.

        Args:
            value: Dictionary of metric values.
            category: Non-empty category name.
        """
        self.logger.set_metrics(value, category)

    def log_message(
        self,
        message: str | LogMessageCode,
        context: str = 'info',
        **kwargs: Any,
    ) -> None:
        """Log a user-facing message.

        Sends a log entry with event='message' to the backend.

        Accepts either a plain string or a LogMessageCode enum.
        When a LogMessageCode is used, the message template and level
        are resolved from the global template registry automatically.

        Args:
            message: Message content string or LogMessageCode enum.
            context: Message context/level ('info', 'warning', 'danger', 'success').
                Ignored when message is a LogMessageCode (level comes from template).
            **kwargs: Format parameters for LogMessageCode message templates.

        Example:
            >>> ctx.log_message('Custom message', 'info')
            >>> ctx.log_message(UploadLogMessageCode.UPLOAD_FILES_UPLOADING, count=10)
        """
        if isinstance(message, LogMessageCode):
            from synapse_sdk.plugins.log_messages import resolve_log_message

            message, context = resolve_log_message(message, **kwargs)

        if hasattr(self.logger, 'log_message'):
            self.logger.log_message(message, context)
        else:
            from synapse_sdk.plugins.models.logger import LogLevel

            self.logger.log(LogLevel.INFO, 'message', {'context': context, 'content': message})

    def log_metric(
        self,
        category: str,
        key: str,
        value: float | int,
        **metrics: Any,
    ) -> None:
        """Log a training metric.

        Sends a log entry with event='metric' to the backend.

        Args:
            category: Metric category (e.g., 'train', 'val').
            key: Metric key (e.g., 'loss', 'accuracy').
            value: Metric value.
            **metrics: Additional metrics as keyword arguments.

        Example:
            >>> ctx.log_metric('train', 'loss', 0.5, accuracy=0.95)
        """
        if hasattr(self.logger, 'log_metric'):
            self.logger.log_metric(category, key, value, **metrics)
        else:
            from synapse_sdk.plugins.models.logger import LogLevel

            data = {'category': category, 'key': key, 'value': value, 'metrics': metrics}
            self.logger.log(LogLevel.INFO, 'metric', data)

    def log_visualization(
        self,
        category: str,
        group: str,
        index: int,
        image: str,
        **meta: Any,
    ) -> None:
        """Log a visualization image.

        Sends a log entry with event='visualization' to the backend.
        The image file is automatically converted to base64.

        Args:
            category: Visualization category (e.g., 'train', 'val').
            group: Group name for organizing visualizations.
            index: Index within the group.
            image: Path to the image file.
            **meta: Additional metadata as keyword arguments.

        Example:
            >>> ctx.log_visualization('train', 'predictions', 0, '/tmp/pred.png')
        """
        if hasattr(self.logger, 'log_visualization'):
            self.logger.log_visualization(category, group, index, image, **meta)
        else:
            from synapse_sdk.plugins.models.logger import LogLevel

            data = {'category': category, 'group': group, 'index': index, **meta}
            self.logger.log(LogLevel.INFO, 'visualization', data, image)

    def log_trials(
        self,
        data: dict[str, Any] | None = None,
        *,
        trials: dict[str, Any] | None = None,
        base: list[str] | None = None,
        hyperparameters: list[str] | None = None,
        metrics: list[str] | None = None,
        best_trial: str = '',
    ) -> None:
        """Log Ray Tune trial progress.

        Sends a log entry with event='trials' to the backend.

        Args:
            data: Pre-built payload containing 'trials' key.
            trials: Mapping of trial_id to trial data.
            base: Column names for the base section.
            hyperparameters: Column names for hyperparameters.
            metrics: Column names for metrics.
            best_trial: Trial ID of the best trial.

        Example:
            >>> ctx.log_trials(
            ...     trials={'trial_1': {'loss': 0.1}},
            ...     metrics=['loss'],
            ...     best_trial='trial_1'
            ... )
        """
        if hasattr(self.logger, 'log_trials'):
            self.logger.log_trials(
                data, trials=trials, base=base, hyperparameters=hyperparameters, metrics=metrics, best_trial=best_trial
            )
        else:
            from synapse_sdk.plugins.models.logger import LogLevel

            if data is None:
                data = {
                    'base': base or [],
                    'trials': trials or {},
                    'hyperparameters': hyperparameters or [],
                    'metrics': metrics or [],
                    'best_trial': best_trial,
                }
            self.logger.log(LogLevel.INFO, 'trials', data)

    def log_dev_event(self, message: str, data: dict[str, Any] | None = None) -> None:
        """Log a development/debug event.

        For plugin developers to log custom events during execution.
        Not shown to end users by default.

        Args:
            message: Event message.
            data: Optional additional data.
        """
        from synapse_sdk.plugins.models.logger import LogLevel

        self.logger.log(LogLevel.DEBUG, 'dev_event', {'message': message, 'data': data})

    def end_log(self) -> None:
        """Signal that plugin execution is complete."""
        self.log_message(CommonLogMessageCode.PLUGIN_RUN_COMPLETE)


__all__ = ['PluginEnvironment', 'RuntimeContext']
