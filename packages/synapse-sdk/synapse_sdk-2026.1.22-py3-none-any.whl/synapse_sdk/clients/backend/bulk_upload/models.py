"""Pydantic models for bulk upload operations.

This module contains data models used by bulk upload strategies:
- Presigned URL upload models
- Multipart upload models
- Upload confirmation models
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class PresignedUploadPart(BaseModel):
    """Individual part information for multipart upload.

    Attributes:
        part_number: Sequential part number starting from 1.
        presigned_url: Presigned URL for uploading this specific part.
    """

    model_config = ConfigDict(extra='ignore')

    part_number: int
    presigned_url: str


class MultipartUploadInfo(BaseModel):
    """Multipart upload metadata for large files.

    Attributes:
        upload_id: Unique identifier for the multipart upload session.
        part_size: Size of each part in bytes (typically 100MB).
        parts: List of part information with presigned URLs.
    """

    model_config = ConfigDict(extra='ignore')

    upload_id: str
    part_size: int
    parts: list[PresignedUploadPart]


class PresignedFileInfo(BaseModel):
    """Presigned URL information for a single file.

    Attributes:
        filename: Original filename.
        file_key: Storage key where the file will be stored.
        presigned_url: Presigned URL for direct upload (for files <=5GB).
        multipart: Multipart upload information (for files >5GB).
    """

    model_config = ConfigDict(extra='ignore')

    filename: str
    file_key: str
    presigned_url: str | None = None
    multipart: MultipartUploadInfo | None = None


class PresignedUploadResponse(BaseModel):
    """Response from presigned upload request endpoint.

    Attributes:
        files: List of presigned file information for each requested file.
        expires_at: ISO 8601 timestamp when presigned URLs expire.
    """

    model_config = ConfigDict(extra='ignore')

    files: list[PresignedFileInfo]
    expires_at: str


class ConfirmFileResult(BaseModel):
    """Result for a single file confirmation.

    Attributes:
        file_key: Storage key of the file.
        checksum: SHA1 checksum of the uploaded file.
        data_file_id: Created DataFile ID if successful.
        success: Whether the confirmation was successful.
        error: Error message if confirmation failed.
    """

    model_config = ConfigDict(extra='ignore')

    file_key: str
    checksum: str
    data_file_id: int | None = None
    success: bool
    error: str | None = None


class ConfirmUploadResponse(BaseModel):
    """Response from upload confirmation endpoint.

    Attributes:
        results: List of confirmation results for each file.
        created_count: Number of successfully created DataFile records.
        failed_count: Number of failed file confirmations.
    """

    model_config = ConfigDict(extra='ignore')

    results: list[ConfirmFileResult]
    created_count: int
    failed_count: int


# Storage providers that support presigned URL uploads
PRESIGNED_UPLOAD_PROVIDERS = frozenset({
    'amazon_s3',
    's3',
    'minio',
    'gcp',
    'gcs',
    'azure',
})

# Default part size for multipart uploads (100MB)
DEFAULT_PART_SIZE = 100 * 1024 * 1024


__all__ = [
    'PresignedUploadPart',
    'MultipartUploadInfo',
    'PresignedFileInfo',
    'PresignedUploadResponse',
    'ConfirmFileResult',
    'ConfirmUploadResponse',
    'PRESIGNED_UPLOAD_PROVIDERS',
    'DEFAULT_PART_SIZE',
]
