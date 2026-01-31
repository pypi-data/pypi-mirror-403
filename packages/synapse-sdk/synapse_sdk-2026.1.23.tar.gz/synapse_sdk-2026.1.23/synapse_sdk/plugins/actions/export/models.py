"""Export action parameter models.

This module provides parameter validation models for export operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, field_validator
from pydantic_core import PydanticCustomError

from synapse_sdk.clients.exceptions import ClientError
from synapse_sdk.plugins.actions.export.handlers import TargetHandlerFactory

if TYPE_CHECKING:
    from pydantic import ValidationInfo


def non_blank(value: str) -> str:
    """Validate that a string is not blank.

    Args:
        value: String value to validate.

    Returns:
        The original string value if valid.

    Raises:
        ValueError: If the string is empty or contains only whitespace.
    """
    if not value or not value.strip():
        raise ValueError('Value cannot be blank')
    return value


class ExportParams(BaseModel):
    """Export action parameter validation model.

    Defines and validates all parameters required for export operations.
    Uses Pydantic for type validation and custom validators to ensure
    storage and filter resources exist before processing.

    Attributes:
        name: Human-readable name for the export operation.
        description: Optional description of the export.
        storage: Storage ID where exported data will be saved.
        save_original_file: Whether to save the original file.
        path: File system path where exported data will be saved.
        target: The target source to export data from (assignment, ground_truth, task).
        filter: Filter criteria to apply when retrieving data.
        extra_params: Additional parameters for export customization.

    Example:
        >>> params = ExportParams(
        ...     name="Assignment Export",
        ...     storage=1,
        ...     path="/exports/assignments",
        ...     target="assignment",
        ...     filter={"project": 123}
        ... )
    """

    name: Annotated[str, AfterValidator(non_blank)]
    description: str | None = None
    storage: int
    save_original_file: bool = True
    path: str
    target: Literal['assignment', 'ground_truth', 'task']
    filter: dict[str, Any]
    extra_params: dict[str, Any] | None = None

    @field_validator('storage')
    @classmethod
    def check_storage_exists(cls, value: int, info: ValidationInfo) -> int:
        """Validate that storage exists and is accessible.

        Args:
            value: Storage ID to validate.
            info: Validation context containing action reference.

        Returns:
            Validated storage ID.

        Raises:
            PydanticCustomError: If storage cannot be accessed.
        """
        if info.context is None:
            return value
        action = info.context.get('action')
        if action is None:
            return value
        client = action.client
        try:
            client.get_storage(value)
        except ClientError:
            raise PydanticCustomError('client_error', 'Unable to get storage from Synapse backend.')
        return value

    @field_validator('filter')
    @classmethod
    def check_filter_by_target(cls, value: dict[str, Any], info: ValidationInfo) -> dict[str, Any]:
        """Validate filter criteria for the specified target.

        Args:
            value: Filter criteria to validate.
            info: Validation context containing action reference.

        Returns:
            Validated filter criteria.

        Raises:
            PydanticCustomError: If filter is invalid for target.
        """
        if info.context is None:
            return value
        action = info.context.get('action')
        if action is None:
            return value
        client = action.client
        target = info.data.get('target')
        if target is None:
            return value
        handler = TargetHandlerFactory.get_handler(target)
        return handler.validate_filter(value, client)
