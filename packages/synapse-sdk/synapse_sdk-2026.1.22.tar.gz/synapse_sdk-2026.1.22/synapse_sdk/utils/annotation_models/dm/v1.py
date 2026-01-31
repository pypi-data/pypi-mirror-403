"""DataMaker V1 schema models (event-based, per-assignment structure).

DMv1 uses an event-based structure where annotations are keyed by asset.
Supports classifications, relations, groups, and supplementary data.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class DMv1Classification(BaseModel):
    """V1 classification as flat key-value pairs.

    Structure defined by admin but stored flat.
    """

    model_config = {'extra': 'allow'}


class DMv1AnnotationBase(BaseModel):
    """V1 base annotation object.

    Attributes:
        id: Unique annotation ID.
        tool: Name of the tool used.
        isLocked: Whether annotation is locked.
        isVisible: Whether annotation is visible.
        classification: Flat key-value classification attributes.
    """

    id: str
    tool: str
    isLocked: bool = False
    isVisible: bool = True
    classification: DMv1Classification | None = None

    model_config = {'extra': 'allow'}


class DMv1RelationItem(BaseModel):
    """V1 relation (edge) between annotations.

    Attributes:
        id: Unique relation ID.
        tool: Always 'relation'.
        annotationId: Source annotation ID.
        targetAnnotationId: Target annotation ID.
        classification: Attributes assigned to the relation.
    """

    id: str
    tool: str = 'relation'
    isLocked: bool = False
    isVisible: bool = True
    annotationId: str
    targetAnnotationId: str
    classification: DMv1Classification | None = None


class DMv1GroupMemberItem(BaseModel):
    """V1 group member with optional hierarchy.

    Attributes:
        annotationId: ID of annotation in group.
        children: Sub-groups or hierarchical structure.
    """

    annotationId: str
    children: list[DMv1GroupMemberItem] = Field(default_factory=list)


class DMv1AnnotationGroupItem(BaseModel):
    """V1 annotation group.

    Attributes:
        id: Unique group ID.
        tool: Always 'annotationGroup'.
        classification: Group classification.
        annotationList: List of group members.
    """

    id: str
    tool: str = 'annotationGroup'
    isLocked: bool = False
    classification: DMv1Classification | None = None
    annotationList: list[DMv1GroupMemberItem] = Field(default_factory=list)


class DMv1AnnotationDataItem(BaseModel):
    """V1 supplementary annotation data (frames, model results).

    Attributes:
        frameIndex: Frame number for video/time-series.
        section: Start/end frame range.
        input: Prompt input.
        output: Model output.
    """

    frameIndex: int | None = None
    section: dict[str, int] | None = None  # {startFrame, endFrame}
    input: str | None = None
    output: str | None = None


class DMv1Dataset(BaseModel):
    """DataMaker V1 dataset schema (event-based).

    Per-assignment structure with annotations keyed by asset.

    Attributes:
        assignmentId: Optional job identifier.
        extra: Asset-level additional metadata.
        annotations: Annotations per asset (Record<string, AnnotationBase[]>).
        relations: Relationships between annotations.
        annotationGroups: Grouping information.
        annotationsData: Supplementary data (frames, model results).

    Example:
        >>> dataset = DMv1Dataset(
        ...     assignmentId='job-123',
        ...     annotations={'image_0': [annotation1, annotation2]},
        ... )
    """

    assignmentId: str | None = None
    extra: dict | None = None
    annotations: dict[str, list[DMv1AnnotationBase]] = Field(default_factory=dict)
    relations: dict[str, list[DMv1RelationItem]] = Field(default_factory=dict)
    annotationGroups: dict[str, list[DMv1AnnotationGroupItem]] = Field(default_factory=dict)
    annotationsData: dict[str, list[DMv1AnnotationDataItem]] = Field(default_factory=dict)


__all__ = [
    'DMv1AnnotationBase',
    'DMv1AnnotationDataItem',
    'DMv1AnnotationGroupItem',
    'DMv1Classification',
    'DMv1Dataset',
    'DMv1GroupMemberItem',
    'DMv1RelationItem',
]
