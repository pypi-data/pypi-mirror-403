"""Run schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.progress import ActionProgress


class RunStatus(StrEnum):
    """Pipeline run status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunCreate(BaseModel):
    """Schema for creating a run."""

    params: dict[str, Any] | None = Field(None, description="Initial parameters")
    work_dir: str | None = Field(None, description="Working directory path")


class RunUpdate(BaseModel):
    """Schema for updating a run."""

    status: RunStatus | None = None
    current_action: str | None = None
    current_action_index: int | None = None
    progress: list[ActionProgress] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class RunRead(BaseModel):
    """Schema for reading a run."""

    id: str
    pipeline_id: str
    status: RunStatus
    params: dict[str, Any] | None
    current_action: str | None
    current_action_index: int
    progress: list[ActionProgress] | None
    result: dict[str, Any] | None
    error: str | None
    work_dir: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
