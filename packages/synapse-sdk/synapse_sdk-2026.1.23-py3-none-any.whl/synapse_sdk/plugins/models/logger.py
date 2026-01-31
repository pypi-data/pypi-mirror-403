"""Logger models and enums.

This module re-exports core logger types from synapse_sdk.loggers
and defines additional logger-related models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

# Re-export core logger types from loggers.py to avoid circular imports
from synapse_sdk.loggers import LogEntry, LoggerBackend, ProgressData

if TYPE_CHECKING:
    from synapse_sdk.plugins.models.pipeline import ActionStatus

__all__ = [
    'LogLevel',
    'ProgressData',
    'LogEntry',
    'LoggerBackend',
    'ActionProgress',
    'PipelineProgress',
    'Checkpoint',
]


class LogLevel(str, Enum):
    """Log level for logger."""

    DEBUG = 'debug'
    INFO = 'info'
    SUCCESS = 'success'
    WARNING = 'warning'
    DANGER = 'danger'
    ERROR = 'error'
    CRITICAL = 'critical'


@dataclass
class ActionProgress:
    """Progress state for a single action."""

    name: str
    status: ActionStatus = None  # type: ignore[assignment]
    progress: float = 0.0
    progress_category: str | None = None
    message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        # Lazy import to avoid circular imports
        if self.status is None:
            from synapse_sdk.plugins.models.pipeline import ActionStatus

            self.status = ActionStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'name': self.name,
            'status': self.status.value,
            'progress': self.progress,
            'progress_category': self.progress_category,
            'message': self.message,
            'metrics': self.metrics,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionProgress:
        """Create from dictionary."""
        from synapse_sdk.plugins.models.pipeline import ActionStatus

        return cls(
            name=data['name'],
            status=ActionStatus(data['status']),
            progress=data.get('progress', 0.0),
            progress_category=data.get('progress_category'),
            message=data.get('message'),
            metrics=data.get('metrics', {}),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
        )


@dataclass
class PipelineProgress:
    """Overall pipeline progress state."""

    run_id: str
    status: Any = None  # RunStatus, but lazy loaded
    actions: dict[str, ActionProgress] = field(default_factory=dict)
    current_action: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if self.status is None:
            from synapse_sdk.plugins.models.pipeline import RunStatus

            self.status = RunStatus.PENDING

    @property
    def overall_progress(self) -> float:
        """Calculate overall progress across all actions."""
        if not self.actions:
            return 0.0
        return sum(a.progress for a in self.actions.values()) / len(self.actions)

    @property
    def completed_actions(self) -> int:
        """Count completed actions."""
        from synapse_sdk.plugins.models.pipeline import ActionStatus

        return sum(1 for a in self.actions.values() if a.status == ActionStatus.COMPLETED)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API serialization."""
        return {
            'run_id': self.run_id,
            'status': self.status.value,
            'actions': {k: v.to_dict() for k, v in self.actions.items()},
            'current_action': self.current_action,
            'overall_progress': self.overall_progress,
            'completed_actions': self.completed_actions,
            'total_actions': len(self.actions),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error': self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineProgress:
        """Create from dictionary."""
        from synapse_sdk.plugins.models.pipeline import RunStatus

        return cls(
            run_id=data['run_id'],
            status=RunStatus(data['status']),
            actions={k: ActionProgress.from_dict(v) for k, v in data.get('actions', {}).items()},
            current_action=data.get('current_action'),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            error=data.get('error'),
        )


@dataclass
class Checkpoint:
    """Checkpoint for pipeline state persistence."""

    run_id: str
    action_name: str
    result: Any
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'run_id': self.run_id,
            'action_name': self.action_name,
            'result': self.result,
            'created_at': self.created_at.isoformat(),
        }
