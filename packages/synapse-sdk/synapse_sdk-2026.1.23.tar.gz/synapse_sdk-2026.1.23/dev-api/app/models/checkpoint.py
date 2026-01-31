"""Checkpoint model."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Checkpoint(Base):
    """Action checkpoint for pipeline resume."""

    __tablename__ = "checkpoints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    run_id: Mapped[str] = mapped_column(String(36), ForeignKey("pipeline_runs.id"), nullable=False)

    # Action info
    action_name: Mapped[str] = mapped_column(String(255), nullable=False)
    action_index: Mapped[int] = mapped_column(Integer, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "completed", "failed", "skipped", name="checkpoint_status"),
        default="pending",
    )

    # Data
    params_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Accumulated params at this point
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # Action result
    artifacts_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # Path to artifacts

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    run: Mapped["PipelineRun"] = relationship("PipelineRun", back_populates="checkpoints")


from app.models.pipeline import PipelineRun  # noqa: E402, F811
