"""Run routes."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database import get_db
from app.models.pipeline import PipelineRun
from app.schemas.progress import ProgressUpdate
from app.schemas.run import RunRead, RunUpdate

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/", response_model=list[RunRead])
def list_runs(
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all runs, optionally filtered by status."""
    query = db.query(PipelineRun)
    if status_filter:
        query = query.filter(PipelineRun.status == status_filter)
    runs = query.order_by(PipelineRun.created_at.desc()).offset(skip).limit(limit).all()
    return runs


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get a run by ID."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.patch("/{run_id}", response_model=RunRead)
def update_run(run_id: str, run_update: RunUpdate, db: Session = Depends(get_db)):
    """Update a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    update_data = run_update.model_dump(exclude_unset=True)

    # Convert progress to serializable format
    if "progress" in update_data and update_data["progress"] is not None:
        update_data["progress"] = [p.model_dump() if hasattr(p, "model_dump") else p for p in update_data["progress"]]

    for field, value in update_data.items():
        setattr(run, field, value)

    db.commit()
    db.refresh(run)
    return run


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_run(run_id: str, db: Session = Depends(get_db)):
    """Delete a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    db.delete(run)
    db.commit()


@router.post("/{run_id}/progress", response_model=RunRead)
def report_progress(run_id: str, progress_update: ProgressUpdate, db: Session = Depends(get_db)):
    """Report progress update for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Update current action
    if progress_update.current_action is not None:
        run.current_action = progress_update.current_action
    if progress_update.current_action_index is not None:
        run.current_action_index = progress_update.current_action_index

    # Update status
    if progress_update.status is not None:
        run.status = progress_update.status
        if progress_update.status == "running" and run.started_at is None:
            run.started_at = datetime.utcnow()
        elif progress_update.status in ("completed", "failed", "cancelled"):
            run.completed_at = datetime.utcnow()

    # Update error
    if progress_update.error is not None:
        run.error = progress_update.error

    # Update action progress
    if progress_update.action_progress is not None:
        progress_list = list(run.progress) if run.progress else []
        action_idx = (
            progress_update.current_action_index
            if progress_update.current_action_index is not None
            else run.current_action_index
        )

        if 0 <= action_idx < len(progress_list):
            # Use mode='json' to ensure enums/datetimes are JSON-serializable
            progress_list[action_idx] = progress_update.action_progress.model_dump(mode="json")
            run.progress = progress_list
            flag_modified(run, "progress")

    db.commit()
    db.refresh(run)
    return run


@router.get("/{run_id}/progress")
def get_progress(run_id: str, db: Session = Depends(get_db)):
    """Get current progress for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return {
        "run_id": run.id,
        "status": run.status,
        "current_action": run.current_action,
        "current_action_index": run.current_action_index,
        "progress": run.progress,
        "error": run.error,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


@router.get("/{run_id}/progress/stream")
async def stream_progress(run_id: str, db: Session = Depends(get_db)):
    """Stream progress updates via Server-Sent Events.

    Yields SSE events with progress data until the run completes or fails.
    Each event contains JSON with the current progress state.

    Example SSE format:
        event: progress
        data: {"run_id": "abc123", "status": "running", ...}

        event: complete
        data: {"run_id": "abc123", "status": "completed", ...}
    """
    # Verify run exists
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    async def event_generator():
        """Generate SSE events for progress updates."""
        last_progress_hash = None

        while True:
            # Re-fetch run in each iteration (new session context)
            from app.database import SessionLocal

            with SessionLocal() as session:
                current_run = session.query(PipelineRun).filter(PipelineRun.id == run_id).first()
                if not current_run:
                    yield _format_sse("error", {"error": "Run not found"})
                    break

                progress_data = {
                    "run_id": current_run.id,
                    "pipeline_id": current_run.pipeline_id,
                    "status": current_run.status,
                    "current_action": current_run.current_action,
                    "current_action_index": current_run.current_action_index,
                    "progress": current_run.progress,
                    "error": current_run.error,
                    "started_at": current_run.started_at.isoformat() if current_run.started_at else None,
                    "completed_at": current_run.completed_at.isoformat() if current_run.completed_at else None,
                }

                # Only send if progress changed
                progress_hash = hash(json.dumps(progress_data, sort_keys=True, default=str))
                if progress_hash != last_progress_hash:
                    last_progress_hash = progress_hash

                    if current_run.status in ("completed", "failed", "cancelled"):
                        event_type = current_run.status
                    else:
                        event_type = "progress"

                    yield _format_sse(event_type, progress_data)

                    # Terminal states - stop streaming
                    if current_run.status in ("completed", "failed", "cancelled"):
                        break

            await asyncio.sleep(1.0)  # Poll interval

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _format_sse(event: str, data: dict) -> str:
    """Format data as an SSE event string."""
    json_data = json.dumps(data, default=str)
    return f"event: {event}\ndata: {json_data}\n\n"
