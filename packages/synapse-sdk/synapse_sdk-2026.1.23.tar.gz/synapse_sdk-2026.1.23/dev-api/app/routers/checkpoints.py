"""Checkpoint routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.checkpoint import Checkpoint
from app.models.pipeline import PipelineRun
from app.schemas.checkpoint import CheckpointCreate, CheckpointRead

router = APIRouter(prefix="/runs/{run_id}/checkpoints", tags=["checkpoints"])


@router.post("/", response_model=CheckpointRead, status_code=status.HTTP_201_CREATED)
def create_checkpoint(run_id: str, checkpoint: CheckpointCreate, db: Session = Depends(get_db)):
    """Create a checkpoint for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    db_checkpoint = Checkpoint(
        run_id=run_id,
        action_name=checkpoint.action_name,
        action_index=checkpoint.action_index,
        status=checkpoint.status,
        params_snapshot=checkpoint.params_snapshot,
        result=checkpoint.result,
        artifacts_path=checkpoint.artifacts_path,
    )
    db.add(db_checkpoint)
    db.commit()
    db.refresh(db_checkpoint)
    return db_checkpoint


@router.get("/", response_model=list[CheckpointRead])
def list_checkpoints(run_id: str, db: Session = Depends(get_db)):
    """List all checkpoints for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    checkpoints = db.query(Checkpoint).filter(Checkpoint.run_id == run_id).order_by(Checkpoint.action_index).all()
    return checkpoints


@router.get("/latest", response_model=CheckpointRead)
def get_latest_checkpoint(run_id: str, db: Session = Depends(get_db)):
    """Get the latest checkpoint for a run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    checkpoint = (
        db.query(Checkpoint).filter(Checkpoint.run_id == run_id).order_by(Checkpoint.action_index.desc()).first()
    )
    if not checkpoint:
        raise HTTPException(status_code=404, detail="No checkpoints found")
    return checkpoint


@router.get("/{action_name}", response_model=CheckpointRead)
def get_checkpoint_by_action(run_id: str, action_name: str, db: Session = Depends(get_db)):
    """Get checkpoint for a specific action."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    checkpoint = db.query(Checkpoint).filter(Checkpoint.run_id == run_id, Checkpoint.action_name == action_name).first()
    if not checkpoint:
        raise HTTPException(status_code=404, detail="Checkpoint not found")
    return checkpoint
