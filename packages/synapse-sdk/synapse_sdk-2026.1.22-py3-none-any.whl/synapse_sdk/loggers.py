from __future__ import annotations

import logging
import time
import warnings
from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from synapse_sdk.plugins.models.logger import LogLevel

# Module-level logger for SDK output
_logger = logging.getLogger('synapse_sdk.loggers')

# LogLevel string value → Python logging level mapping
_LOG_LEVEL_MAP: dict[str, int] = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'success': logging.INFO,
    'warning': logging.WARNING,
    'danger': logging.ERROR,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


class LoggerBackend(Protocol):
    """Protocol for logger backends that handle data synchronization."""

    def publish_progress(self, job_id: str, progress: 'ProgressData') -> None: ...
    def publish_metrics(self, job_id: str, metrics: dict[str, Any]) -> None: ...
    def publish_log(self, job_id: str, log_entry: 'LogEntry') -> None: ...


@dataclass
class ProgressData:
    """Immutable progress data snapshot."""

    percent: float
    time_remaining: float | None = None
    elapsed_time: float | None = None
    status: str = 'running'


@dataclass
class LogEntry:
    """Single log entry."""

    event: str
    data: dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    file: str | None = None
    step: str | None = None  # 신규: 로그가 발생한 step
    level: Any = None  # 신규: 로그 레벨 (LogLevel enum, 순환 import 방지를 위해 Any)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'event': self.event,
            'data': self.data,
            'timestamp': self.timestamp,
            'file': self.file,
            'step': self.step,
            'level': self.level.value if self.level else None,
        }


class BaseLogger(ABC):
    """Base class for logging progress, metrics, and events.

    All state is instance-level to prevent cross-instance contamination.
    Uses composition over inheritance for backend communication.
    """

    _start_time: float
    _progress: dict[str, ProgressData]
    _metrics: dict[str, dict[str, Any]]
    _category_start_times: dict[str, float]
    _current_step: str | None
    _is_finished: bool

    def __init__(self) -> None:
        self._start_time = time.monotonic()
        self._progress = {}
        self._metrics = {}
        self._category_start_times = {}
        self._current_step = None
        self._is_finished = False

    def set_step(self, step: str | None) -> None:
        """Set the current step for logging context.

        Args:
            step: The step name, or None to clear.
        """
        self._current_step = step

    def get_step(self) -> str | None:
        """Get the current step.

        Returns:
            The current step name, or None if not set.
        """
        return self._current_step

    def _raise_if_finished(self) -> None:
        if self._is_finished:
            raise RuntimeError('Cannot log to a finished logger')

    def log(
        self,
        level: LogLevel,
        event: str,
        data: dict[str, Any],
        file: str | None = None,
        step: str | None = None,
    ) -> None:
        """Log an event with data.

        Args:
            level: Log level (LogLevel enum).
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
            step: Optional step name. Uses current step if not specified.

        Raises:
            TypeError: If level is not a LogLevel enum or data is not a dictionary.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        # Validate level is a LogLevel enum (duck typing check to avoid circular import)
        if not (isinstance(level, Enum) and hasattr(level, 'value') and level.value in _LOG_LEVEL_MAP):
            raise TypeError(f'level must be a LogLevel enum, got {type(level).__name__}')

        if not isinstance(data, Mapping):
            raise TypeError(f'data must be a dict, got {type(data).__name__}')

        data = dict(data)  # Copy to avoid mutating input
        # Use explicit step or fall back to current step
        effective_step = step if step is not None else self._current_step
        self._log_impl(event, data, file, effective_step, level)

    def info(self, message: str) -> None:
        """Log an info message."""
        from synapse_sdk.plugins.models.logger import LogLevel

        self.log(LogLevel.INFO, 'info', {'message': message})

    def debug(self, message: str) -> None:
        """Log a debug message."""
        from synapse_sdk.plugins.models.logger import LogLevel

        self.log(LogLevel.DEBUG, 'debug', {'message': message})

    def warning(self, message: str) -> None:
        """Log a warning message."""
        from synapse_sdk.plugins.models.logger import LogLevel

        self.log(LogLevel.WARNING, 'warning', {'message': message})

    def error(self, message: str) -> None:
        """Log an error message."""
        from synapse_sdk.plugins.models.logger import LogLevel

        self.log(LogLevel.ERROR, 'error', {'message': message})

    def critical(self, message: str) -> None:
        """Log a critical message."""
        from synapse_sdk.plugins.models.logger import LogLevel

        self.log(LogLevel.CRITICAL, 'critical', {'message': message})

    def set_progress(
        self,
        current: int,
        total: int,
        step: str | None = None,
        category: str | None = None,
    ) -> None:
        """Set progress for the current operation.

        Args:
            current: Current progress value (0 to total).
            total: Total progress value.
            step: Optional step name. Uses current step if not specified.
            category: Deprecated. Use step instead.

        Raises:
            ValueError: If current/total values are invalid.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        if total <= 0:
            raise ValueError(f'total must be > 0, got {total}')
        if not 0 <= current <= total:
            raise ValueError(f'current must be between 0 and {total}, got {current}')

        # Priority: explicit step > current step > category (deprecated)
        effective_key: str | None = None
        if step is not None:
            effective_key = step
            if category is not None:
                warnings.warn(
                    "The 'category' parameter is deprecated. Use 'step' instead. "
                    "'step' takes precedence when both are provided.",
                    DeprecationWarning,
                    stacklevel=2,
                )
        elif self._current_step is not None:
            # Use current step if available
            effective_key = self._current_step
            if category is not None:
                warnings.warn(
                    "The 'category' parameter is deprecated. Use 'step' instead. "
                    'Current step takes precedence over category.',
                    DeprecationWarning,
                    stacklevel=2,
                )
        elif category is not None:
            warnings.warn(
                "The 'category' parameter is deprecated. Use 'step' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            effective_key = category

        key = effective_key or '__default__'
        now = time.monotonic()

        # Initialize start time on first call for this category
        if key not in self._category_start_times or current == 0:
            self._category_start_times[key] = now

        elapsed = now - self._category_start_times[key]
        percent = round((current / total) * 100, 2)

        # Calculate time remaining
        time_remaining = None
        if current > 0:
            rate = elapsed / current
            time_remaining = round(rate * (total - current), 2)

        progress = ProgressData(
            percent=percent,
            time_remaining=time_remaining,
            elapsed_time=round(elapsed, 2),
        )

        self._progress[key] = progress
        self._on_progress(progress, effective_key)

    def set_progress_failed(self, category: str | None = None) -> None:
        """Mark progress as failed.

        Args:
            category: Optional category name.

        Raises:
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        key = category or '__default__'
        elapsed = None

        if key in self._category_start_times:
            elapsed = round(time.monotonic() - self._category_start_times[key], 2)

        progress = ProgressData(
            percent=0.0,
            time_remaining=None,
            elapsed_time=elapsed,
            status='failed',
        )

        self._progress[key] = progress
        self._on_progress(progress, category)

    def set_metrics(
        self,
        value: dict[str, Any],
        step: str | None = None,
        category: str | None = None,
    ) -> None:
        """Set metrics for a step.

        Args:
            value: Dictionary of metric values.
            step: Optional step name. Uses current step if not specified.
            category: Deprecated. Use step instead.

        Raises:
            ValueError: If no step/category is available.
            TypeError: If value is not a dictionary.
            RuntimeError: If logger is already finished.
        """
        self._raise_if_finished()

        if not isinstance(value, Mapping):
            raise TypeError(f'value must be a dict, got {type(value).__name__}')

        # Priority: explicit step > current step > category (deprecated)
        effective_key: str | None = None
        if step is not None:
            effective_key = step
            if category is not None:
                warnings.warn(
                    "The 'category' parameter is deprecated. Use 'step' instead. "
                    "'step' takes precedence when both are provided.",
                    DeprecationWarning,
                    stacklevel=2,
                )
        elif self._current_step is not None:
            # Use current step if available
            effective_key = self._current_step
            if category is not None:
                warnings.warn(
                    "The 'category' parameter is deprecated. Use 'step' instead. "
                    'Current step takes precedence over category.',
                    DeprecationWarning,
                    stacklevel=2,
                )
        elif category is not None:
            warnings.warn(
                "The 'category' parameter is deprecated. Use 'step' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            effective_key = category

        if not effective_key:
            raise ValueError('step must be specified or set via set_step()')

        data = dict(value)  # Copy

        if effective_key not in self._metrics:
            self._metrics[effective_key] = {}
        self._metrics[effective_key].update(data)

        self._on_metrics(effective_key, self._metrics[effective_key])

    def get_progress(self, category: str | None = None) -> ProgressData | None:
        """Get progress for a category."""
        key = category or '__default__'
        return self._progress.get(key)

    def get_metrics(self, category: str | None = None) -> dict[str, Any]:
        """Get metrics, optionally filtered by category."""
        if category:
            return dict(self._metrics.get(category, {}))
        return {k: dict(v) for k, v in self._metrics.items()}

    def finish(self) -> None:
        """Mark the logger as finished. No further logging is allowed."""
        self._is_finished = True
        self._on_finish()

    @abstractmethod
    def _log_impl(
        self,
        event: str,
        data: dict[str, Any],
        file: str | None,
        step: str | None,
        level: LogLevel | None = None,
    ) -> None:
        """Implementation-specific log handling."""
        ...

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        """Hook called when progress is updated. Override in subclasses."""
        pass

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        """Hook called when metrics are updated. Override in subclasses."""
        pass

    def _on_finish(self) -> None:
        """Hook called when logger is finished. Override in subclasses."""
        pass


class ConsoleLogger(BaseLogger):
    """Logger that prints to console using Python logging module."""

    def _log_impl(
        self,
        event: str,
        data: dict[str, Any],
        file: str | None,
        step: str | None,
        level: LogLevel | None = None,
    ) -> None:
        prefix = f'[{step}] ' if step else ''
        level_str = level.value.upper() if level else 'INFO'
        message = f'{level_str}: {prefix}{event} {data}'

        # Use print with flush=True for immediate output
        # This ensures logs are visible in Ray remote workers
        print(message, flush=True)

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        prefix = f'[{category}] ' if category else ''
        print(f'INFO: {prefix}Progress: {progress.percent}% | ETA: {progress.time_remaining}s', flush=True)

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        print(f'INFO: [{category}] Metrics: {metrics}', flush=True)

    def log_event(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event (console-only)."""
        file_info = f' (file: {file})' if file else ''
        print(f'INFO: [{event}] {data}{file_info}', flush=True)

    def log_metric(
        self,
        category: str,
        key: str,
        value: float | int,
        **metrics: Any,
    ) -> None:
        """Log a training metric (console-only)."""
        print(f'INFO: [metric] category={category}, {key}={value}, {metrics}', flush=True)

    def log_visualization(
        self,
        category: str,
        group: str,
        index: int,
        image: str,
        **meta: Any,
    ) -> None:
        """Log a visualization (console-only)."""
        print(f'INFO: [visualization] category={category}, group={group}, index={index}, image={image}', flush=True)

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
        """Log Ray Tune trial progress (console-only)."""
        if data is None:
            data = {'trials': trials or {}, 'best_trial': best_trial}
        print(f'INFO: [trials] {data}', flush=True)

    def log_message(self, message: str, context: str = 'info') -> None:
        """Log a message (console-only)."""
        print(f'{context.upper()}: {message}', flush=True)


class BackendLogger(BaseLogger):
    """Logger that syncs with a remote backend.

    Uses a backend interface for decoupled communication.
    """

    _backend: LoggerBackend | None
    _job_id: str
    _log_queue: list[LogEntry]

    def __init__(self, backend: LoggerBackend | None, job_id: str) -> None:
        super().__init__()
        self._backend = backend
        self._job_id = job_id
        self._log_queue = []

    def _log_impl(
        self,
        event: str,
        data: dict[str, Any],
        file: str | None,
        step: str | None,
        level: LogLevel | None = None,
    ) -> None:
        entry = LogEntry(event=event, data=data, file=file, step=step, level=level)
        self._log_queue.append(entry)
        self._flush_logs()

    def _on_progress(self, progress: ProgressData, category: str | None) -> None:
        if self._backend is None:
            return

        try:
            self._backend.publish_progress(self._job_id, progress)
        except Exception as e:
            _logger.error(f'Failed to publish progress: {e}')

    def _on_metrics(self, category: str, metrics: dict[str, Any]) -> None:
        if self._backend is None:
            return

        try:
            self._backend.publish_metrics(self._job_id, {category: metrics})
        except Exception as e:
            _logger.error(f'Failed to publish metrics: {e}')

    def _flush_logs(self) -> None:
        if self._backend is None or not self._log_queue:
            return

        try:
            for entry in self._log_queue:
                self._backend.publish_log(self._job_id, entry)
            self._log_queue.clear()
        except Exception as e:
            _logger.error(f'Failed to flush logs: {e}')

    def _on_finish(self) -> None:
        self._flush_logs()


class JobLogger(BaseLogger):
    """Logger that prints to console AND reports progress/metrics to the Synapse backend.

    Sends progress_record and metrics_record via BackendClient.update_job(),
    and log entries via BackendClient.create_logs().

    - progress_record: {'record': {steps...}, 'current_progress': {overall, step, percent, time_remaining}}
    - metrics_record: {'record': {'steps': {step: {metrics}}}}

    Backend errors are silently caught to avoid crashing training.
    """

    def __init__(
        self,
        client: Any,
        job_id: str,
        step_proportions: dict[str, int] | None = None,
    ) -> None:
        """Initialize JobLogger.

        Args:
            client: BackendClient instance for API calls.
            job_id: Synapse job ID (UUID, passed as RAY_JOB_ID in the worker).
            step_proportions: Optional mapping of step name to proportion weight.
                If not provided, weights are dynamically assigned based on usage order.
                This is typically auto-configured by Orchestrator from step definitions.
        """
        super().__init__()
        self._client = client
        self._job_id = job_id
        self._step_proportions: dict[str, int] = dict(step_proportions) if step_proportions else {}
        self._progress_record: dict[str, Any] = {
            'steps': {step: {'proportion': prop} for step, prop in self._step_proportions.items()},
        }
        self._current_progress_step: str | None = None
        self._metrics_record: dict[str, Any] = {}
        self._logs_queue: list[dict[str, Any]] = []
        self._step_order: list[str] = []  # Track order of step usage
        self._locked_weights: dict[str, float] = {}  # Cache weights once assigned
        self._data_prep_used: float = 0.0  # Track weight used by dynamic steps
        self._max_overall: float = 0.0  # Ensure progress never decreases

    def set_step_proportions(self, proportions: dict[str, int]) -> None:
        """Set step proportions after initialization.

        Call this before any progress updates to configure expected steps
        and their weights. This is typically called automatically by Orchestrator
        based on registered step definitions.

        Args:
            proportions: Mapping of step name to proportion weight.
                Example: {'initialize': 5, 'upload': 30, 'cleanup': 5}

        Raises:
            RuntimeError: If progress has already been recorded.
        """
        if self._step_order:
            raise RuntimeError(
                'Cannot set step proportions after progress has started. '
                'Call set_step_proportions() before any set_progress() calls.'
            )
        self._step_proportions = dict(proportions)
        self._progress_record = {
            'steps': {step: {'proportion': prop} for step, prop in proportions.items()},
        }

    def _get_current_progress(self) -> dict[str, Any]:
        """Calculate current progress format.

        Weight allocation strategy:
        - Predefined steps use their configured proportions from _step_proportions
        - Dynamic steps (not in _step_proportions) share weight from unused
          predefined proportion (e.g., if 'dataset' is not used, its weight is available)
        - Weights are locked once assigned to prevent recalculation
        - No normalization: if configured proportions sum to 100, final progress = 100%

        Progress is sequential: previous phases=100%, current=actual%, future=0%
        """
        steps = self._progress_record.get('steps', {})
        if not steps or not self._current_progress_step:
            return {'overall': 0}

        ordered = self._step_order.copy()
        if not ordered:
            return {'overall': 0}

        # Assign weights to any new steps (lock them)
        for step in ordered:
            if step in self._locked_weights:
                continue

            if step in self._step_proportions:
                # Predefined step - use its configured proportion
                self._locked_weights[step] = float(self._step_proportions[step])
            else:
                # Dynamic step - shares weight from unused predefined steps
                # Core phases (train, model_upload) are excluded from the pool
                core_phases = {'train', 'model_upload'}
                data_prep_pool = sum(
                    v
                    for k, v in self._step_proportions.items()
                    if k not in core_phases and k not in self._locked_weights
                )
                available_pool = data_prep_pool - self._data_prep_used

                if available_pool >= 5:
                    # Give this step half of remaining pool, minimum 5%
                    weight = max(5.0, available_pool / 2)
                else:
                    # Pool nearly exhausted, give remaining or minimal
                    weight = max(2.0, available_pool) if available_pool > 0 else 2.0

                self._locked_weights[step] = weight
                self._data_prep_used += weight

        # Find current step index
        try:
            current_idx = ordered.index(self._current_progress_step)
        except ValueError:
            current_idx = len(ordered) - 1

        # Calculate overall progress using locked weights
        overall = 0.0
        for i, step in enumerate(ordered):
            weight = self._locked_weights.get(step, 0)
            step_data = steps.get(step, {})

            if i < current_idx:
                # Previous steps: full weight
                overall += weight
            elif i == current_idx:
                # Current step: proportional
                percent = step_data.get('percent', 0)
                overall += weight * percent / 100

        # Ensure progress never decreases (monotonically increasing)
        self._max_overall = max(self._max_overall, overall)
        overall = self._max_overall

        step_record = steps.get(self._current_progress_step, {})

        return {
            'overall': round(min(overall, 100), 2),
            'step': self._current_progress_step,
            'percent': step_record.get('percent', 0),
            'time_remaining': step_record.get('time_remaining'),
        }

    def _log_impl(
        self,
        event: str,
        data: dict[str, Any],
        file: str | None,
        step: str | None,
        level: LogLevel | None = None,
    ) -> None:
        # Always print to console for Ray log visibility
        prefix = f'[{step}] ' if step else ''
        level_str = level.value.upper() if level else 'INFO'
        print(f'{level_str}: {prefix}{event} {data}', flush=True)

        # Queue and send to backend
        import datetime as dt

        log_entry: dict[str, Any] = {
            'event': event,
            'data': data,
            'datetime': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'job': self._job_id,
        }
        if file:
            log_entry['file'] = file

        self._logs_queue.append(log_entry)

        try:
            self._client.create_logs(self._logs_queue)
            self._logs_queue.clear()
        except Exception as e:
            _logger.debug(f'JobLogger: failed to send log to backend: {e}')
            print(f'WARNING: JobLogger failed to send log to backend: {e}', flush=True)

    def _on_progress(self, progress: ProgressData, step: str | None) -> None:
        # Print to console
        prefix = f'[{step}] ' if step else ''
        print(f'INFO: {prefix}Progress: {progress.percent}% | ETA: {progress.time_remaining}s', flush=True)

        # Update step in progress_record
        if step:
            # Track step order (first time we see each step)
            if step not in self._step_order:
                self._step_order.append(step)

            self._current_progress_step = step
            steps = self._progress_record.setdefault('steps', {})
            steps.setdefault(step, {}).update({
                'percent': progress.percent,
                'time_remaining': progress.time_remaining,
            })
        else:
            self._progress_record.update({
                'percent': progress.percent,
                'time_remaining': progress.time_remaining,
            })

        try:
            payload = {
                'record': self._progress_record,
                'current_progress': self._get_current_progress(),
            }
            self._client.update_job(self._job_id, {'progress_record': payload})
        except Exception as e:
            _logger.debug(f'JobLogger: failed to update progress: {e}')
            print(f'WARNING: JobLogger failed to update progress: {e}', flush=True)

    def _on_metrics(self, step: str, metrics: dict[str, Any]) -> None:
        # Print to console
        print(f'INFO: [{step}] Metrics: {metrics}', flush=True)

        if 'steps' not in self._metrics_record:
            self._metrics_record['steps'] = {}
        self._metrics_record['steps'].setdefault(step, {}).update(metrics)

        try:
            self._client.update_job(self._job_id, {'metrics_record': {'record': self._metrics_record}})
        except Exception as e:
            _logger.debug(f'JobLogger: failed to update metrics: {e}')
            print(f'WARNING: JobLogger failed to update metrics: {e}', flush=True)

    # -------------------------------------------------------------------------
    # Legacy-compatible logging methods for metrics/visualization
    # These send logs with specific 'event' types that the backend API expects
    # -------------------------------------------------------------------------

    def log_event(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event with specific event type (legacy-compatible).

        This method sends logs with a specific 'event' field that matches
        the backend API format expected by /logs/?event=<type>.

        Args:
            event: Event type (e.g., 'metric', 'visualization', 'message', 'trials').
            data: Event data dictionary.
            file: Optional file path to attach (will be converted to base64).
        """
        import datetime as dt

        print(f'INFO: [{event}] {data}', flush=True)

        log_entry: dict[str, Any] = {
            'event': event,
            'data': data,
            'datetime': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'),
            'job': self._job_id,
        }
        if file:
            log_entry['file'] = file

        try:
            self._client.create_logs([log_entry])
        except Exception as e:
            _logger.debug(f'JobLogger: failed to send {event} log to backend: {e}')
            print(f'WARNING: JobLogger failed to send {event} log to backend: {e}', flush=True)

    def log_metric(
        self,
        category: str,
        key: str,
        value: float | int,
        **metrics: Any,
    ) -> None:
        """Log a training metric (legacy-compatible).

        Sends a log entry with event='metric' to the backend.

        Args:
            category: Metric category (e.g., 'train', 'val').
            key: Metric key (e.g., 'loss', 'accuracy').
            value: Metric value.
            **metrics: Additional metrics as keyword arguments.

        Example:
            >>> ctx.logger.log_metric('train', 'loss', 0.5, accuracy=0.95)
        """
        data: dict[str, Any] = {
            'category': category,
            'key': key,
            'value': value,
            'metrics': metrics,
        }
        self.log_event('metric', data)

    def log_visualization(
        self,
        category: str,
        group: str,
        index: int,
        image: str,
        **meta: Any,
    ) -> None:
        """Log a visualization image (legacy-compatible).

        Sends a log entry with event='visualization' to the backend.
        The image file is automatically converted to base64.

        Args:
            category: Visualization category (e.g., 'train', 'val').
            group: Group name for organizing visualizations.
            index: Index within the group.
            image: Path to the image file.
            **meta: Additional metadata as keyword arguments.

        Example:
            >>> ctx.logger.log_visualization('train', 'predictions', 0, '/tmp/pred.png')
        """
        data: dict[str, Any] = {
            'category': category,
            'group': group,
            'index': index,
            **meta,
        }
        self.log_event('visualization', data, file=image)

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
        """Log Ray Tune trial progress (legacy-compatible).

        Sends a log entry with event='trials' to the backend.

        Args:
            data: Pre-built payload containing 'trials' key.
            trials: Mapping of trial_id to trial data.
            base: Column names for the base section.
            hyperparameters: Column names for hyperparameters.
            metrics: Column names for metrics.
            best_trial: Trial ID of the best trial.

        Example:
            >>> ctx.logger.log_trials(
            ...     trials={'trial_1': {'loss': 0.1}},
            ...     metrics=['loss'],
            ...     best_trial='trial_1'
            ... )
        """
        if data is None:
            data = {
                'base': base or [],
                'trials': trials or {},
                'hyperparameters': hyperparameters or [],
                'metrics': metrics or [],
                'best_trial': best_trial,
            }
        elif not isinstance(data, dict):
            raise ValueError('log_trials expects a dictionary payload')

        if 'trials' not in data:
            raise ValueError('log_trials payload must include "trials" key')

        self.log_event('trials', data)

    def log_message(self, message: str, context: str = 'info') -> None:
        """Log a message (legacy-compatible).

        Sends a log entry with event='message' to the backend.

        Args:
            message: The message content.
            context: Message context level ('info', 'warning', 'error').

        Example:
            >>> ctx.logger.log_message('Training started', 'info')
        """
        data = {'context': context, 'content': message}
        self.log_event('message', data)


class NoOpLogger(BaseLogger):
    """Logger that does nothing. Useful for testing or disabled logging."""

    def _log_impl(
        self,
        event: str,
        data: dict[str, Any],
        file: str | None,
        step: str | None,
        level: LogLevel | None = None,
    ) -> None:
        pass

    # Legacy-compatible methods (no-op)
    def log_event(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        pass

    def log_metric(self, category: str, key: str, value: float | int, **metrics: Any) -> None:
        pass

    def log_visualization(self, category: str, group: str, index: int, image: str, **meta: Any) -> None:
        pass

    def log_trials(self, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        pass

    def log_message(self, message: str, context: str = 'info') -> None:
        pass


__all__ = [
    'BaseLogger',
    'BackendLogger',
    'ConsoleLogger',
    'JobLogger',
    'LogEntry',
    'LoggerBackend',
    'NoOpLogger',
    'ProgressData',
]
