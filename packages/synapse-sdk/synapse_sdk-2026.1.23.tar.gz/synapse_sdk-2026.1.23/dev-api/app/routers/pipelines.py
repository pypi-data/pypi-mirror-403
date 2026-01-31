"""Pipeline routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.pipeline import Pipeline, PipelineRun
from app.schemas.pipeline import PipelineCreate, PipelineRead, PipelineUpdate
from app.schemas.run import RunCreate, RunRead

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


@router.post("/", response_model=PipelineRead, status_code=status.HTTP_201_CREATED)
def create_pipeline(pipeline: PipelineCreate, db: Session = Depends(get_db)):
    """Create a new pipeline definition."""
    db_pipeline = Pipeline(
        name=pipeline.name,
        description=pipeline.description,
        actions=[a.model_dump() for a in pipeline.actions],
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


@router.get("/", response_model=list[PipelineRead])
def list_pipelines(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all pipelines."""
    pipelines = db.query(Pipeline).offset(skip).limit(limit).all()
    return pipelines


@router.get("/{pipeline_id}", response_model=PipelineRead)
def get_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Get a pipeline by ID."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineRead)
def update_pipeline(pipeline_id: str, pipeline_update: PipelineUpdate, db: Session = Depends(get_db)):
    """Update a pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    update_data = pipeline_update.model_dump(exclude_unset=True)
    if "actions" in update_data and update_data["actions"] is not None:
        update_data["actions"] = [a.model_dump() if hasattr(a, "model_dump") else a for a in update_data["actions"]]

    for field, value in update_data.items():
        setattr(pipeline, field, value)

    db.commit()
    db.refresh(pipeline)
    return pipeline


@router.delete("/{pipeline_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_pipeline(pipeline_id: str, db: Session = Depends(get_db)):
    """Delete a pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    db.delete(pipeline)
    db.commit()


@router.post("/{pipeline_id}/runs/", response_model=RunRead, status_code=status.HTTP_201_CREATED)
def create_run(pipeline_id: str, run: RunCreate, db: Session = Depends(get_db)):
    """Create a new run for a pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Initialize progress for each action
    initial_progress = []
    for i, action in enumerate(pipeline.actions):
        initial_progress.append(
            {
                "name": action.get("name", f"action_{i}"),
                "status": "pending",
                "progress": 0.0,
                "progress_category": None,
                "message": None,
                "metrics": {},
                "started_at": None,
                "completed_at": None,
            }
        )

    db_run = PipelineRun(
        pipeline_id=pipeline_id,
        params=run.params,
        work_dir=run.work_dir,
        progress=initial_progress,
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run


@router.get("/{pipeline_id}/runs/", response_model=list[RunRead])
def list_pipeline_runs(pipeline_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all runs for a pipeline."""
    pipeline = db.query(Pipeline).filter(Pipeline.id == pipeline_id).first()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    runs = db.query(PipelineRun).filter(PipelineRun.pipeline_id == pipeline_id).offset(skip).limit(limit).all()
    return runs
