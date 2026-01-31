"""Base context for step-based workflows.

Provides the abstract base class for sharing state between workflow steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.log_messages import LogMessageCode

if TYPE_CHECKING:
    from synapse_sdk.plugins.context import RuntimeContext
    from synapse_sdk.plugins.steps.base import StepResult


@dataclass
class BaseStepContext:
    """Abstract base context for step-based workflows.

    Provides the common interface for step contexts. Subclass this
    to add action-specific state fields.

    Attributes:
        runtime_ctx: Parent RuntimeContext with logger, env, client.
        step_results: Results from each executed step.
        errors: Accumulated error messages.
        current_step: Name of the currently executing step (set by Orchestrator).

    Example:
        >>> @dataclass
        ... class UploadContext(BaseStepContext):
        ...     params: dict[str, Any] = field(default_factory=dict)
        ...     uploaded_files: list[str] = field(default_factory=list)
        >>>
        >>> ctx = UploadContext(runtime_ctx=runtime_ctx)
        >>> ctx.log('upload_start', {'count': 10})
    """

    runtime_ctx: RuntimeContext
    step_results: list[StepResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    current_step: str | None = field(default=None, init=False)

    def _set_current_step(self, step_name: str | None) -> None:
        """Set the currently executing step name (internal use by Orchestrator).

        Args:
            step_name: Name of the step being executed, or None to clear.
        """
        self.current_step = step_name

    def log(self, event: str, data: dict[str, Any], file: str | None = None) -> None:
        """Log an event via runtime context.

        Args:
            event: Event name/type.
            data: Dictionary of event data.
            file: Optional file path associated with the event.
        """
        self.runtime_ctx.log(event, data, file)

    def set_progress(self, current: int, total: int, category: str | None = None) -> None:
        """Set progress via runtime context.

        If category is not provided, uses current_step as the category.

        Args:
            current: Current progress value.
            total: Total progress value.
            category: Optional category name. Defaults to current_step if not provided.
        """
        effective_category = category if category is not None else self.current_step
        self.runtime_ctx.set_progress(current, total, effective_category)

    def log_message(
        self,
        message: str | LogMessageCode,
        context: str = 'info',
        **kwargs: Any,
    ) -> None:
        """Log a user-facing message via runtime context.

        Sends a log entry with event='message' to the backend,
        making the message visible to users in the UI.

        Accepts either a plain string or a LogMessageCode enum.
        When a LogMessageCode is used, the message template and level
        are resolved from LOG_MESSAGE_TEMPLATES automatically.

        Args:
            message: Message content string or LogMessageCode enum.
            context: Message context/level ('info', 'warning', 'danger', 'success').
                Ignored when message is a LogMessageCode (level comes from template).
            **kwargs: Format parameters for LogMessageCode message templates.

        Example:
            >>> context.log_message('Custom message', 'info')
            >>> context.log_message(UploadLogMessageCode.UPLOAD_FILES_UPLOADING, count=10)
        """
        self.runtime_ctx.log_message(message, context, **kwargs)

    def set_metrics(self, value: dict[str, Any], category: str | None = None) -> None:
        """Set metrics via runtime context.

        If category is not provided, uses current_step as the category.

        Args:
            value: Dictionary of metric values.
            category: Category name. Defaults to current_step if not provided.

        Raises:
            ValueError: If category is not provided and current_step is None.
        """
        effective_category = category if category is not None else self.current_step
        if effective_category is None:
            raise ValueError('category must be provided when not executing within a step (current_step is None)')
        self.runtime_ctx.set_metrics(value, effective_category)
