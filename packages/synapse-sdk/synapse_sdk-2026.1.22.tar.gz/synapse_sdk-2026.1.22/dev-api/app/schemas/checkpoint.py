"""Checkpoint schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.progress import ActionStatus


class CheckpointCreate(BaseModel):
    """Schema for creating a checkpoint."""

    action_name: str = Field(..., description="Action name")
    action_index: int = Field(..., description="Action index in pipeline")
    status: ActionStatus = Field(default=ActionStatus.COMPLETED)
    params_snapshot: dict[str, Any] | None = Field(None, description="Accumulated params at checkpoint")
    result: dict[str, Any] | None = Field(None, description="Action result")
    artifacts_path: str | None = Field(None, description="Path to artifacts")


class CheckpointRead(BaseModel):
    """Schema for reading a checkpoint."""

    id: str
    run_id: str
    action_name: str
    action_index: int
    status: ActionStatus
    params_snapshot: dict[str, Any] | None
    result: dict[str, Any] | None
    artifacts_path: str | None
    created_at: datetime

    class Config:
        from_attributes = True
