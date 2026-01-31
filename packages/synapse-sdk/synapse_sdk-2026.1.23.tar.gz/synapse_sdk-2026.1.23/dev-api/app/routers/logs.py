"""Log routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.log import LogEntry
from app.models.pipeline import PipelineRun
from app.schemas.log import LogEntryBatch, LogEntryRead, LogLevel

router = APIRouter(prefix="/runs/{run_id}/logs", tags=["logs"])


@router.post("/", response_model=list[LogEntryRead], status_code=status.HTTP_201_CREATED)
def append_logs(run_id: str, batch: LogEntryBatch, db: Session = Depends(get_db)):
    """Append log entries for a run (batch)."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    created_logs = []
    for entry in batch.entries:
        db_log = LogEntry(
            run_id=run_id,
            action_name=entry.action_name,
            level=entry.level,
            message=entry.message,
            timestamp=entry.timestamp or datetime.utcnow(),
        )
        db.add(db_log)
        created_logs.append(db_log)

    db.commit()
    for log in created_logs:
        db.refresh(log)

    return created_logs


@router.get("/", response_model=list[LogEntryRead])
def get_logs(
    run_id: str,
    action_name: str | None = Query(None, description="Filter by action name"),
    level: LogLevel | None = Query(None, description="Filter by log level"),
    since: datetime | None = Query(None, description="Filter logs after this timestamp"),
    limit: int = Query(1000, ge=1, le=10000, description="Max logs to return"),
    db: Session = Depends(get_db),
):
    """Get logs for a run with optional filters."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    query = db.query(LogEntry).filter(LogEntry.run_id == run_id)

    if action_name:
        query = query.filter(LogEntry.action_name == action_name)
    if level:
        query = query.filter(LogEntry.level == level)
    if since:
        query = query.filter(LogEntry.timestamp > since)

    logs = query.order_by(LogEntry.timestamp).limit(limit).all()
    return logs
