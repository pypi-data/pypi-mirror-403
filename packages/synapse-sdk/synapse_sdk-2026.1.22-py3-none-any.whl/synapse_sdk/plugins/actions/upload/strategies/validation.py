"""Validation strategy implementations for upload operations.

Provides validation strategies for:
    - Parameter validation
    - File validation against specifications
"""

from __future__ import annotations

from typing import Any

from synapse_sdk.plugins.actions.upload.strategies.base import (
    ValidationResult,
    ValidationStrategy,
)


class DefaultValidationStrategy(ValidationStrategy):
    """Default validation strategy for upload operations.

    Validates:
    - Required parameters are present
    - Files match specifications (required files exist)
    - File extensions match expected types

    Example:
        >>> strategy = DefaultValidationStrategy()
        >>> result = strategy.validate_params({'storage': 1, 'data_collection': 5})
        >>> if result.valid:
        ...     print("Parameters valid")
    """

    def validate_params(self, params: dict[str, Any]) -> ValidationResult:
        """Validate action parameters.

        Checks:
        - storage is present
        - data_collection is present
        - name is present and non-empty
        - path or assets is present depending on mode

        Args:
            params: Action parameters dictionary.

        Returns:
            ValidationResult indicating success or failure with errors.
        """
        errors: list[str] = []

        # Check required parameters
        if not params.get('storage'):
            errors.append('storage parameter is required')

        if not params.get('data_collection'):
            errors.append('data_collection parameter is required')

        if not params.get('name'):
            errors.append('name parameter is required')

        # Check mode-specific parameters
        use_single_path = params.get('use_single_path', True)
        if use_single_path:
            if not params.get('path'):
                errors.append('path parameter is required in single-path mode')
        else:
            assets = params.get('assets')
            if not assets:
                errors.append('assets parameter is required in multi-path mode')

        return ValidationResult(valid=len(errors) == 0, errors=errors)

    def validate_files(
        self,
        files: list[dict[str, Any]],
        specs: list[dict[str, Any]],
    ) -> ValidationResult:
        """Validate organized files against specifications.

        Checks:
        - At least one file group exists
        - Required file types are present in each group
        - File extensions match spec allowed extensions

        Args:
            files: List of organized file dictionaries with structure:
                {'files': {spec_name: Path, ...}, 'meta': {...}}
            specs: File specifications from data collection.

        Returns:
            ValidationResult indicating success or failure with errors.
        """
        errors: list[str] = []

        if not files:
            return ValidationResult(valid=False, errors=['No files to validate'])

        # Build spec lookup
        spec_lookup = {spec['name']: spec for spec in specs}

        # Get required specs
        required_specs = [spec['name'] for spec in specs if spec.get('is_required', False)]

        # Validate each file group
        for idx, file_group in enumerate(files):
            group_files = file_group.get('files', {})

            # Check required files are present
            for required_spec in required_specs:
                if required_spec not in group_files:
                    errors.append(f'File group {idx}: missing required file type "{required_spec}"')

            # Validate file extensions
            for spec_name, file_path in group_files.items():
                if spec_name not in spec_lookup:
                    continue

                spec = spec_lookup[spec_name]
                allowed_extensions = spec.get('extensions', [])

                if allowed_extensions and file_path:
                    file_ext = file_path.suffix.lower().lstrip('.')
                    # Normalize extensions in spec
                    normalized_exts = [ext.lower().lstrip('.') for ext in allowed_extensions]
                    if file_ext not in normalized_exts:
                        errors.append(
                            f'File group {idx}: file "{file_path.name}" has '
                            f'extension ".{file_ext}" but spec "{spec_name}" '
                            f'expects {allowed_extensions}'
                        )

        return ValidationResult(valid=len(errors) == 0, errors=errors)


__all__ = [
    'DefaultValidationStrategy',
]
