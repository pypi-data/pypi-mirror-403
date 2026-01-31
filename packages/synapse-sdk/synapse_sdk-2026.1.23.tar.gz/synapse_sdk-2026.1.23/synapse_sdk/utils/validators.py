"""Pydantic validators for common validation patterns."""

from __future__ import annotations


def non_blank(value: str) -> str:
    """Validate that a string is not blank (empty or whitespace only).

    For use with Pydantic's AfterValidator.

    Args:
        value: String value to validate.

    Returns:
        The original value if valid.

    Raises:
        ValueError: If the value is blank.

    Example:
        >>> from typing import Annotated
        >>> from pydantic import AfterValidator, BaseModel
        >>> from synapse_sdk.utils.validators import non_blank
        >>>
        >>> class MyModel(BaseModel):
        ...     name: Annotated[str, AfterValidator(non_blank)]
        >>>
        >>> MyModel(name="valid")  # OK
        >>> MyModel(name="  ")  # Raises ValidationError
    """
    if not value or not value.strip():
        raise ValueError('Value cannot be blank')
    return value
