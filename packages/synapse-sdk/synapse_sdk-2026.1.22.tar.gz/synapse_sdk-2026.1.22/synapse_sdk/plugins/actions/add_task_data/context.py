"""Context for add_task_data workflows."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from synapse_sdk.plugins.steps import BaseStepContext


@dataclass
class AddTaskDataContext(BaseStepContext):
    """Shared state for add_task_data execution.

    Attributes:
        params: Flattened parameters from the action.
        data_collection: Data collection metadata for the project.
        task_ids: IDs of tasks to annotate.
        inference: Cached inference context (code/version) when using inference mode.
        failures: Per-task failure records.
        success_count: Number of successfully processed tasks.
        failed_count: Number of failed tasks.
    """

    params: dict[str, Any] = field(default_factory=dict)
    data_collection: dict[str, Any] | None = None
    task_ids: list[int] = field(default_factory=list)
    inference: dict[str, Any] | None = None
    failures: list[dict[str, Any]] = field(default_factory=list)
    success_count: int = 0
    failed_count: int = 0

    @property
    def total_tasks(self) -> int:
        """Total discovered tasks.

        Returns:
            int: Number of task IDs collected for processing.
        """
        return len(self.task_ids)
