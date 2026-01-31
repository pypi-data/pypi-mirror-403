"""Presigned URL upload strategy.

This module implements bulk uploads using presigned URLs for direct-to-storage
file transfers, bypassing the API server for file data.
"""

from __future__ import annotations

import hashlib
import mimetypes
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.bulk_upload.base import BulkUploadStrategy
from synapse_sdk.clients.backend.bulk_upload.models import (
    PRESIGNED_UPLOAD_PROVIDERS,
    ConfirmFileResult,
    ConfirmUploadResponse,
    PresignedFileInfo,
    PresignedUploadResponse,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from synapse_sdk.clients.backend.bulk_upload.config import BulkUploadConfig


@dataclass
class PresignedUploadResult:
    """Result of uploading a file to a presigned URL.

    Attributes:
        checksum: SHA1 hex digest of the uploaded file.
        size: File size in bytes.
    """

    checksum: str
    size: int


class PresignedUploadStrategy(BulkUploadStrategy):
    """Upload strategy using presigned URLs for direct-to-storage uploads.

    Bypasses the API server for file data transfer by:
    1. Requesting presigned URLs from the API
    2. Uploading files directly to cloud storage in parallel
    3. Confirming uploads to create DataFile records

    Supports:
        - Amazon S3 / MinIO
        - Google Cloud Storage
        - Azure Blob Storage
        - Multipart uploads for files >5GB

    Example:
        >>> strategy = PresignedUploadStrategy(client)
        >>> config = BulkUploadConfig(max_workers=16)
        >>> result = strategy.upload_files(file_paths, config)
    """

    strategy_name = 'presigned'
    supported_providers = PRESIGNED_UPLOAD_PROVIDERS

    def supports_storage(self, storage: dict[str, Any]) -> bool:
        """Check if storage supports presigned uploads."""
        provider = storage.get('provider', '').lower()
        return provider in self.supported_providers

    def upload_files(
        self,
        file_paths: list[Path],
        config: 'BulkUploadConfig',
        *,
        on_progress: 'Callable[[int, int], None] | None' = None,
    ) -> ConfirmUploadResponse:
        """Upload files using presigned URLs.

        Processes files in batches, uploading in parallel within each batch.

        Args:
            file_paths: List of local file paths to upload.
            config: Upload configuration.
            on_progress: Optional progress callback(completed, total).

        Returns:
            ConfirmUploadResponse with upload results.
        """
        if not file_paths:
            return ConfirmUploadResponse(results=[], created_count=0, failed_count=0)

        total_files = len(file_paths)
        all_results: list[ConfirmFileResult] = []
        total_completed = 0

        # Process files in batches
        for batch_start in range(0, total_files, config.batch_size):
            batch_end = min(batch_start + config.batch_size, total_files)
            batch_paths = file_paths[batch_start:batch_end]

            # Prepare file info for this batch
            files_info = []
            for path in batch_paths:
                mime_type, _ = mimetypes.guess_type(str(path))
                files_info.append({
                    'filename': path.name,
                    'size': path.stat().st_size,
                    'content_type': mime_type,
                })

            # Request presigned URLs for this batch
            presigned = self.request_presigned_upload(
                files_info,
                expiration=config.url_expiration,
            )

            # Upload files in parallel
            upload_results: list[dict[str, Any]] = []

            with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
                future_to_file = {}

                for file_info, local_path in zip(presigned.files, batch_paths):
                    if file_info.presigned_url:
                        future = executor.submit(
                            self.upload_file_to_presigned_url,
                            file_info.presigned_url,
                            local_path,
                            files_info[batch_paths.index(local_path)].get('content_type'),
                            config.timeout,
                        )
                        future_to_file[future] = (file_info, local_path)
                    elif file_info.multipart:
                        future = executor.submit(
                            self._upload_multipart,
                            file_info,
                            local_path,
                            config.timeout,
                        )
                        future_to_file[future] = (file_info, local_path)

                for future in as_completed(future_to_file):
                    file_info, local_path = future_to_file[future]
                    try:
                        result = future.result()
                        if isinstance(result, PresignedUploadResult):
                            upload_results.append({
                                'file_key': file_info.file_key,
                                'checksum': result.checksum,
                                'size': result.size,
                            })
                        else:
                            upload_results.append(result)
                    except FileNotFoundError:
                        upload_results.append({
                            'file_key': file_info.file_key,
                            'error': f'File not found: {local_path}',
                        })
                    except Exception as e:
                        error_msg = str(e)
                        if 'HTTPStatusError' in type(e).__name__:
                            error_msg = f'HTTP error during upload: {error_msg}'
                        elif 'TimeoutException' in type(e).__name__ or 'Timeout' in error_msg:
                            error_msg = f'Upload timeout: {error_msg}'
                        upload_results.append({
                            'file_key': file_info.file_key,
                            'error': error_msg,
                        })

                    total_completed += 1
                    if on_progress:
                        on_progress(total_completed, total_files)

            # Confirm successful uploads for this batch
            successful = [r for r in upload_results if 'error' not in r]

            if successful:
                batch_confirm = self.confirm_presigned_upload(successful)
                all_results.extend(batch_confirm.results)

            # Add failed results
            for failed in upload_results:
                if 'error' in failed:
                    all_results.append(
                        ConfirmFileResult(
                            file_key=failed['file_key'],
                            checksum='',
                            success=False,
                            error=failed['error'],
                        )
                    )

        # Calculate final counts
        created_count = sum(1 for r in all_results if r.success)
        failed_count = len(all_results) - created_count

        return ConfirmUploadResponse(
            results=all_results,
            created_count=created_count,
            failed_count=failed_count,
        )

    def request_presigned_upload(
        self,
        files: list[dict[str, Any]],
        expiration: int = 3600,
    ) -> PresignedUploadResponse:
        """Request presigned URLs for direct-to-storage uploads.

        Args:
            files: List of file information dictionaries. Each dict should contain:
                - filename (str): Original filename
                - size (int): File size in bytes
                - content_type (str, optional): MIME type
            expiration: URL expiration time in seconds. Default is 3600 (1 hour).

        Returns:
            PresignedUploadResponse containing presigned URLs and file keys.
        """
        response = self.client._post(
            'data_files/presigned_upload/upload/',
            data={'files': files, 'expiration': expiration},
        )
        return PresignedUploadResponse.model_validate(response)

    def confirm_presigned_upload(
        self,
        files: list[dict[str, Any]],
    ) -> ConfirmUploadResponse:
        """Confirm uploaded files and create DataFile records.

        Args:
            files: List of uploaded file information. Each dict should contain:
                - file_key (str): Storage key from presigned response
                - checksum (str): SHA1 checksum of uploaded file
                - size (int): File size in bytes
                - multipart (dict, optional): Multipart upload details

        Returns:
            ConfirmUploadResponse with created DataFile IDs and any errors.
        """
        response = self.client._post(
            'data_files/presigned_upload/confirm_upload/',
            data={'files': files},
        )
        return ConfirmUploadResponse.model_validate(response)

    def upload_file_to_presigned_url(
        self,
        presigned_url: str,
        file_path: Path,
        content_type: str | None = None,
        timeout: float = 300.0,
    ) -> PresignedUploadResult:
        """Upload a file directly to storage using a presigned URL.

        Args:
            presigned_url: The presigned URL to upload to.
            file_path: Local path to the file to upload.
            content_type: Optional Content-Type header value.
            timeout: Upload timeout in seconds.

        Returns:
            PresignedUploadResult with checksum and size.
        """
        import httpx

        # Calculate checksum while reading file in chunks
        hasher = hashlib.sha1()
        file_size = file_path.stat().st_size

        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)

        checksum = hasher.hexdigest()

        # Upload file using streaming
        headers = {}
        if content_type:
            headers['Content-Type'] = content_type

        with open(file_path, 'rb') as f:
            response = httpx.put(
                presigned_url,
                content=f,
                headers=headers,
                timeout=timeout,
            )
        response.raise_for_status()

        return PresignedUploadResult(checksum=checksum, size=file_size)

    def _upload_multipart(
        self,
        file_info: PresignedFileInfo,
        local_path: Path,
        timeout: float = 300.0,
    ) -> dict[str, Any]:
        """Upload a large file using multipart upload.

        Args:
            file_info: Presigned file information with multipart details.
            local_path: Local path to the file to upload.
            timeout: Upload timeout per part in seconds.

        Returns:
            Dictionary containing file_key, checksum, size, and multipart info.
        """
        import httpx

        if not file_info.multipart:
            msg = 'No multipart info provided'
            raise ValueError(msg)

        multipart = file_info.multipart
        part_size = multipart.part_size
        parts_result = []

        hasher = hashlib.sha1()

        with open(local_path, 'rb') as f:
            for part in multipart.parts:
                chunk = f.read(part_size)
                if not chunk:
                    break

                hasher.update(chunk)

                response = httpx.put(
                    part.presigned_url,
                    content=chunk,
                    timeout=timeout,
                )
                response.raise_for_status()

                etag = response.headers.get('ETag', '')
                parts_result.append({
                    'part_number': part.part_number,
                    'etag': etag,
                })

        return {
            'file_key': file_info.file_key,
            'checksum': hasher.hexdigest(),
            'size': local_path.stat().st_size,
            'multipart': {
                'upload_id': multipart.upload_id,
                'parts': parts_result,
            },
        }


__all__ = ['PresignedUploadResult', 'PresignedUploadStrategy']
