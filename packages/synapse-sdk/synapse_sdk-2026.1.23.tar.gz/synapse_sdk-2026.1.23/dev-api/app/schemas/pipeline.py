"""Pipeline schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class ActionDefinition(BaseModel):
    """Action definition in a pipeline."""

    name: str = Field(..., description="Action name")
    entrypoint: str = Field(..., description="Module.ClassName entrypoint")
    description: str | None = Field(None, description="Action description")


class PipelineBase(BaseModel):
    """Base pipeline schema."""

    name: str = Field(..., min_length=1, max_length=255, description="Pipeline name")
    description: str | None = Field(None, description="Pipeline description")
    actions: list[ActionDefinition] = Field(default_factory=list, description="List of actions in order")


class PipelineCreate(PipelineBase):
    """Schema for creating a pipeline."""

    pass


class PipelineUpdate(BaseModel):
    """Schema for updating a pipeline."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    actions: list[ActionDefinition] | None = None


class PipelineRead(PipelineBase):
    """Schema for reading a pipeline."""

    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
