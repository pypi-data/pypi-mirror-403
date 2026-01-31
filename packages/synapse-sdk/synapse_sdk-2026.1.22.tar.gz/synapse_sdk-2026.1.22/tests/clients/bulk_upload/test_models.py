"""Tests for bulk upload Pydantic models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from synapse_sdk.clients.backend.bulk_upload.models import (
    DEFAULT_PART_SIZE,
    PRESIGNED_UPLOAD_PROVIDERS,
    ConfirmFileResult,
    ConfirmUploadResponse,
    MultipartUploadInfo,
    PresignedFileInfo,
    PresignedUploadPart,
    PresignedUploadResponse,
)


class TestPresignedUploadPart:
    """Tests for PresignedUploadPart model."""

    def test_valid_creation(self) -> None:
        """Test creating a valid PresignedUploadPart."""
        part = PresignedUploadPart(
            part_number=1,
            presigned_url='https://s3.amazonaws.com/bucket/key?signature=xxx',
        )

        assert part.part_number == 1
        assert part.presigned_url == 'https://s3.amazonaws.com/bucket/key?signature=xxx'

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            PresignedUploadPart()  # type: ignore

    def test_extra_fields_ignored(self) -> None:
        """Test that extra fields are ignored."""
        part = PresignedUploadPart(
            part_number=1,
            presigned_url='https://example.com',
            extra_field='should be ignored',  # type: ignore
        )

        assert not hasattr(part, 'extra_field')


class TestMultipartUploadInfo:
    """Tests for MultipartUploadInfo model."""

    def test_valid_creation(self) -> None:
        """Test creating a valid MultipartUploadInfo."""
        parts = [
            PresignedUploadPart(part_number=1, presigned_url='https://example.com/1'),
            PresignedUploadPart(part_number=2, presigned_url='https://example.com/2'),
        ]
        info = MultipartUploadInfo(
            upload_id='abc123',
            part_size=100 * 1024 * 1024,
            parts=parts,
        )

        assert info.upload_id == 'abc123'
        assert info.part_size == 100 * 1024 * 1024
        assert len(info.parts) == 2
        assert info.parts[0].part_number == 1

    def test_empty_parts_list(self) -> None:
        """Test creating with empty parts list."""
        info = MultipartUploadInfo(
            upload_id='abc123',
            part_size=100 * 1024 * 1024,
            parts=[],
        )

        assert info.parts == []


class TestPresignedFileInfo:
    """Tests for PresignedFileInfo model."""

    def test_valid_creation_with_presigned_url(self) -> None:
        """Test creating with presigned URL for small file."""
        info = PresignedFileInfo(
            filename='test.jpg',
            file_key='uploads/test.jpg',
            presigned_url='https://s3.amazonaws.com/bucket/uploads/test.jpg?signature=xxx',
        )

        assert info.filename == 'test.jpg'
        assert info.file_key == 'uploads/test.jpg'
        assert info.presigned_url is not None
        assert info.multipart is None

    def test_valid_creation_with_multipart(self) -> None:
        """Test creating with multipart info for large file."""
        multipart = MultipartUploadInfo(
            upload_id='abc123',
            part_size=100 * 1024 * 1024,
            parts=[PresignedUploadPart(part_number=1, presigned_url='https://example.com/1')],
        )
        info = PresignedFileInfo(
            filename='large_file.zip',
            file_key='uploads/large_file.zip',
            multipart=multipart,
        )

        assert info.filename == 'large_file.zip'
        assert info.presigned_url is None
        assert info.multipart is not None
        assert info.multipart.upload_id == 'abc123'

    def test_optional_fields_default_to_none(self) -> None:
        """Test that optional fields default to None."""
        info = PresignedFileInfo(
            filename='test.jpg',
            file_key='uploads/test.jpg',
        )

        assert info.presigned_url is None
        assert info.multipart is None


class TestPresignedUploadResponse:
    """Tests for PresignedUploadResponse model."""

    def test_valid_creation(self) -> None:
        """Test creating a valid response."""
        files = [
            PresignedFileInfo(
                filename='test1.jpg',
                file_key='uploads/test1.jpg',
                presigned_url='https://example.com/1',
            ),
            PresignedFileInfo(
                filename='test2.jpg',
                file_key='uploads/test2.jpg',
                presigned_url='https://example.com/2',
            ),
        ]
        response = PresignedUploadResponse(
            files=files,
            expires_at='2024-01-01T12:00:00Z',
        )

        assert len(response.files) == 2
        assert response.expires_at == '2024-01-01T12:00:00Z'

    def test_empty_files_list(self) -> None:
        """Test creating with empty files list."""
        response = PresignedUploadResponse(
            files=[],
            expires_at='2024-01-01T12:00:00Z',
        )

        assert response.files == []


class TestConfirmFileResult:
    """Tests for ConfirmFileResult model."""

    def test_successful_result(self) -> None:
        """Test creating a successful confirmation result."""
        result = ConfirmFileResult(
            file_key='uploads/test.jpg',
            checksum='abc123def456',
            data_file_id=12345,
            success=True,
        )

        assert result.file_key == 'uploads/test.jpg'
        assert result.checksum == 'abc123def456'
        assert result.data_file_id == 12345
        assert result.success is True
        assert result.error is None

    def test_failed_result(self) -> None:
        """Test creating a failed confirmation result."""
        result = ConfirmFileResult(
            file_key='uploads/test.jpg',
            checksum='abc123def456',
            success=False,
            error='File not found in storage',
        )

        assert result.success is False
        assert result.error == 'File not found in storage'
        assert result.data_file_id is None


class TestConfirmUploadResponse:
    """Tests for ConfirmUploadResponse model."""

    def test_valid_response(self) -> None:
        """Test creating a valid confirmation response."""
        results = [
            ConfirmFileResult(
                file_key='uploads/test1.jpg',
                checksum='abc123',
                data_file_id=1,
                success=True,
            ),
            ConfirmFileResult(
                file_key='uploads/test2.jpg',
                checksum='def456',
                success=False,
                error='Upload failed',
            ),
        ]
        response = ConfirmUploadResponse(
            results=results,
            created_count=1,
            failed_count=1,
        )

        assert len(response.results) == 2
        assert response.created_count == 1
        assert response.failed_count == 1

    def test_all_successful(self) -> None:
        """Test response with all successful uploads."""
        results = [
            ConfirmFileResult(file_key=f'uploads/test{i}.jpg', checksum='abc', success=True, data_file_id=i)
            for i in range(5)
        ]
        response = ConfirmUploadResponse(
            results=results,
            created_count=5,
            failed_count=0,
        )

        assert response.created_count == 5
        assert response.failed_count == 0


class TestConstants:
    """Tests for module constants."""

    def test_presigned_upload_providers(self) -> None:
        """Test PRESIGNED_UPLOAD_PROVIDERS contains expected providers."""
        expected = {'amazon_s3', 's3', 'minio', 'gcp', 'gcs', 'azure'}
        assert PRESIGNED_UPLOAD_PROVIDERS == frozenset(expected)

    def test_default_part_size(self) -> None:
        """Test DEFAULT_PART_SIZE is 100MB."""
        assert DEFAULT_PART_SIZE == 100 * 1024 * 1024
