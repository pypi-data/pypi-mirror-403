from __future__ import annotations

from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from synapse_sdk.utils.file import decode_base64_data, download_file, get_temp_path, is_base64_data


class FileField(str):
    """Pydantic field type that automatically downloads files from URLs or decodes base64 data.

    When used as a type annotation in a Pydantic model, URLs are automatically
    downloaded and base64 data URIs are decoded during validation, replacing
    the original value with a local file path.

    The files are cached in /tmp/datamaker/media/ using a hash of
    the URL/data as the filename, preventing redundant processing.

    Examples:
        >>> from pydantic import BaseModel
        >>> from synapse_sdk.enums import FileField
        >>>
        >>> class InferenceParams(BaseModel):
        ...     input_file: FileField
        ...     config_file: FileField | None = None
        >>>
        >>> # URL is automatically downloaded during validation
        >>> params = InferenceParams(input_file="https://example.com/image.jpg")
        >>> params.input_file  # "/tmp/datamaker/media/abc123def.jpg"
        >>>
        >>> # Base64 data URI is automatically decoded
        >>> params = InferenceParams(input_file="data:image/png;base64,iVBORw0KGgo...")
        >>> params.input_file  # "/tmp/datamaker/media/abc123def.png"

    Note:
        - Processing happens synchronously during validation
        - Files are cached by content hash (same content = same local path)
        - The field value becomes a string path to the local file
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.with_info_before_validator_function(
            cls._validate,
            core_schema.str_schema(),
        )

    @classmethod
    def _validate(cls, value: Any, info: core_schema.ValidationInfo) -> str:
        """Download file from URL or decode base64 data and return local path.

        Args:
            value: URL string or base64 data URI (e.g., "data:image/png;base64,...").
            info: Pydantic validation context (unused but required by protocol).

        Returns:
            String path to the local file.

        Raises:
            requests.HTTPError: If URL download fails.
            ValueError: If value is not a valid string.
        """
        if not isinstance(value, str):
            raise ValueError(f'FileField expects a URL string, got {type(value).__name__}')

        if not value:
            raise ValueError('FileField URL cannot be empty')

        path_download = get_temp_path('media')
        path_download.mkdir(parents=True, exist_ok=True)

        if is_base64_data(value):
            return str(decode_base64_data(value, path_download))
        return str(download_file(value, path_download))


__all__ = ['FileField']
