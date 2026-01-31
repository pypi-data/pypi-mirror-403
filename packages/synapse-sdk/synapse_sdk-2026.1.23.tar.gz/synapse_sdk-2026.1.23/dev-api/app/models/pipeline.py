"""Pipeline and PipelineRun models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Pipeline(Base):
    """Pipeline definition model."""

    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    actions: Mapped[dict] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    runs: Mapped[list["PipelineRun"]] = relationship(
        "PipelineRun", back_populates="pipeline", cascade="all, delete-orphan"
    )


class PipelineRun(Base):
    """Pipeline execution run model."""

    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    pipeline_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipelines.id"), nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "completed", "failed", "cancelled", name="run_status"),
        default="pending",
    )

    # Execution state
    params: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_action: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_action_index: Mapped[int] = mapped_column(default=0)
    progress: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # ActionProgress list
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Working directory
    work_dir: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Timestamps
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    pipeline: Mapped["Pipeline"] = relationship("Pipeline", back_populates="runs")
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        "Checkpoint", back_populates="run", cascade="all, delete-orphan"
    )
    logs: Mapped[list["LogEntry"]] = relationship("LogEntry", back_populates="run", cascade="all, delete-orphan")


# Import for type hints
from app.models.checkpoint import Checkpoint  # noqa: E402
from app.models.log import LogEntry  # noqa: E402
