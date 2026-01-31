"""Log schemas."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class LogLevel(StrEnum):
    """Log level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogEntryCreate(BaseModel):
    """Schema for creating a log entry."""

    action_name: str | None = Field(None, description="Action that generated the log")
    level: LogLevel = Field(default=LogLevel.INFO)
    message: str = Field(..., description="Log message")
    timestamp: datetime | None = Field(None, description="Timestamp (defaults to now)")


class LogEntryBatch(BaseModel):
    """Schema for batch log creation."""

    entries: list[LogEntryCreate] = Field(..., description="List of log entries")


class LogEntryRead(BaseModel):
    """Schema for reading a log entry."""

    id: str
    run_id: str
    action_name: str | None
    level: LogLevel
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True
