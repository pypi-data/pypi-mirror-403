"""Pipeline status enums."""

from enum import Enum

__all__ = ['RunStatus', 'ActionStatus']


class RunStatus(str, Enum):
    """Status of a pipeline run."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class ActionStatus(str, Enum):
    """Status of an individual action."""

    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'
