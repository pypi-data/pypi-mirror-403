"""Validation utilities with enhanced error location tracking.

This module provides validation helpers that wrap Pydantic's model_validate
with additional context about where validation errors occurred.
"""

from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import ValidationError as PydanticValidationError

if TYPE_CHECKING:
    from pydantic import BaseModel

T = TypeVar('T', bound='BaseModel')


def validate_params(
    model_cls: type[T],
    data: dict[str, Any],
    *,
    context: str = '',
    validation_context: dict[str, Any] | None = None,
) -> T:
    """Validate parameters with enhanced error location tracking.

    This function wraps Pydantic's model_validate and enhances validation
    errors with information about where the validation was triggered,
    making it easier to debug validation failures.

    Args:
        model_cls: The Pydantic model class to validate against.
        data: The dictionary data to validate.
        context: Optional context string (e.g., action name) to include in error.
        validation_context: Optional context dict passed to Pydantic's model_validate.
            Commonly used to pass {'client': backend_client} for resource validation.

    Returns:
        The validated Pydantic model instance.

    Raises:
        ValidationError: If validation fails, with enhanced location info.

    Example:
        >>> from pydantic import BaseModel
        >>> class TrainParams(BaseModel):
        ...     epochs: int
        ...     learning_rate: float
        >>> params = validate_params(TrainParams, {'epochs': 10, 'learning_rate': 0.01})
        >>> # With client context for resource validation
        >>> params = validate_params(
        ...     TrainParams,
        ...     {'epochs': 10},
        ...     context='TrainAction',
        ...     validation_context={'client': backend_client},
        ... )
    """
    try:
        return model_cls.model_validate(data, context=validation_context)
    except PydanticValidationError as e:
        raise _create_validation_error(model_cls, e, context) from e


def _create_validation_error(
    model_cls: type[T],
    pydantic_error: PydanticValidationError,
    context: str = '',
) -> Exception:
    """Create an enhanced ValidationError with location info.

    Args:
        model_cls: The model class that failed validation.
        pydantic_error: The original Pydantic ValidationError.
        context: Optional context string.

    Returns:
        A ValidationError with enhanced message including location.
    """
    # Get the caller's location (skip internal frames)
    # Stack: _create_validation_error -> validate_params -> actual caller
    stack = traceback.extract_stack()
    location = _find_caller_location(stack)

    # Build error message
    parts = [f'Validation failed for {model_cls.__name__}']
    if context:
        parts.append(f'({context})')
    if location:
        parts.append(f'at {location}')

    header = ' '.join(parts)

    # Format Pydantic errors
    error_details = _format_pydantic_errors(pydantic_error)

    message = f'{header}:\n{error_details}'

    # Lazy import to avoid circular dependency
    from synapse_sdk.plugins.errors import ValidationError

    return ValidationError(message, details=pydantic_error.errors())


def _find_caller_location(stack: list[traceback.FrameSummary]) -> str:
    """Find the caller location from the stack trace.

    Skips internal frames (this module and pydantic) to find
    the actual user/SDK code that triggered validation.

    Args:
        stack: The traceback stack.

    Returns:
        A string like "path/to/file.py:123" or empty if not found.
    """
    # Frames to skip (this module's functions)
    skip_files = {'validation.py'}

    for frame in reversed(stack):
        filename = frame.filename
        # Skip frames from this module
        if any(skip in filename for skip in skip_files):
            continue
        # Skip pydantic internals
        if 'pydantic' in filename:
            continue
        # Skip Python internals
        if filename.startswith('<'):
            continue

        # Extract relative path if possible
        short_path = _shorten_path(filename)
        return f'{short_path}:{frame.lineno}'

    return ''


def _shorten_path(filepath: str) -> str:
    """Shorten a file path for display.

    Tries to show path relative to synapse_sdk or just the filename.

    Args:
        filepath: The full file path.

    Returns:
        A shortened path string.
    """
    # Try to find synapse_sdk in the path
    if 'synapse_sdk' in filepath:
        idx = filepath.find('synapse_sdk')
        return filepath[idx:]

    # Try to find site-packages or common markers
    for marker in ('site-packages/', 'src/', 'lib/'):
        if marker in filepath:
            idx = filepath.find(marker) + len(marker)
            return filepath[idx:]

    # Fall back to just the filename
    return filepath.split('/')[-1]


def _format_pydantic_errors(error: PydanticValidationError) -> str:
    """Format Pydantic validation errors for display.

    Args:
        error: The Pydantic ValidationError.

    Returns:
        A formatted string with each error on its own line.
    """
    lines = []
    for err in error.errors():
        loc = ' -> '.join(str(x) for x in err['loc']) if err['loc'] else 'root'
        msg = err['msg']
        err_type = err['type']
        lines.append(f'  - {loc}: {msg} (type={err_type})')

    return '\n'.join(lines)


__all__ = ['validate_params']
