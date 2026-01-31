# Pipeline API

** dev only **

FastAPI for pipeline proof-of-concept.

## Quick Start

```bash
# Install dependencies
cd dev-api
uv sync

# Run the server
uv run uvicorn app.main:app --reload --port 8100

# Open API docs
open http://localhost:8100/docs
```

## API Endpoints

### Health
- `GET /health` - Health check

### Pipelines
- `POST /api/v1/pipelines/` - Create pipeline
- `GET /api/v1/pipelines/` - List pipelines
- `GET /api/v1/pipelines/{id}` - Get pipeline
- `PUT /api/v1/pipelines/{id}` - Update pipeline
- `DELETE /api/v1/pipelines/{id}` - Delete pipeline

### Runs
- `POST /api/v1/pipelines/{id}/runs/` - Create run
- `GET /api/v1/pipelines/{id}/runs/` - List runs for pipeline
- `GET /api/v1/runs/` - List all runs
- `GET /api/v1/runs/{run_id}` - Get run
- `PATCH /api/v1/runs/{run_id}` - Update run
- `DELETE /api/v1/runs/{run_id}` - Delete run

### Progress
- `POST /api/v1/runs/{run_id}/progress` - Report progress
- `GET /api/v1/runs/{run_id}/progress` - Get progress

### Checkpoints
- `POST /api/v1/runs/{run_id}/checkpoints/` - Create checkpoint
- `GET /api/v1/runs/{run_id}/checkpoints/` - List checkpoints
- `GET /api/v1/runs/{run_id}/checkpoints/latest` - Get latest
- `GET /api/v1/runs/{run_id}/checkpoints/{action}` - Get by action

### Logs
- `POST /api/v1/runs/{run_id}/logs` - Append logs
- `GET /api/v1/runs/{run_id}/logs` - Get logs

## Database

SQLite database stored at `./data/pipeline.db`. Tables are auto-created on startup.
