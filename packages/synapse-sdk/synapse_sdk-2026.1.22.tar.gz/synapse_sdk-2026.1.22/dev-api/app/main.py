"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: cleanup if needed


app = FastAPI(
    title=settings.app_name,
    description="Pipeline orchestration PoC service for Synapse SDK",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS - allow all for PoC
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.app_name}


# Import and include routers after app is created to avoid circular imports
from app.routers import checkpoints, logs, pipelines, runs  # noqa: E402

app.include_router(pipelines.router, prefix=settings.api_prefix)
app.include_router(runs.router, prefix=settings.api_prefix)
app.include_router(checkpoints.router, prefix=settings.api_prefix)
app.include_router(logs.router, prefix=settings.api_prefix)
