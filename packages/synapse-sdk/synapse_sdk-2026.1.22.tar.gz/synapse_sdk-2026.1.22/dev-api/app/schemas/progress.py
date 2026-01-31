"""Progress schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ActionStatus(StrEnum):
    """Action execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ActionProgress(BaseModel):
    """Progress for a single action."""

    name: str = Field(..., description="Action name")
    status: ActionStatus = Field(default=ActionStatus.PENDING)
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Progress 0.0-1.0")
    progress_category: str | None = Field(None, description="Current phase (e.g., 'download', 'train')")
    message: str | None = Field(None, description="Current status message")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Action metrics")
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = Field(None, description="Error message if action failed")


class ProgressUpdate(BaseModel):
    """Schema for reporting progress update."""

    current_action: str | None = Field(None, description="Current action name")
    current_action_index: int | None = Field(None, description="Current action index")
    action_progress: ActionProgress | None = Field(None, description="Progress for current action")
    status: str | None = Field(None, description="Overall run status")
    error: str | None = Field(None, description="Error message if failed")
