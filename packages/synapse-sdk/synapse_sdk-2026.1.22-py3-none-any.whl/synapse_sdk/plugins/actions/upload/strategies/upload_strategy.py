"""Upload strategies for file upload operations.

Provides strategies for uploading files to storage:
    - SyncUploadStrategy: Synchronous upload with presigned URL support
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from synapse_sdk.clients.backend.bulk_upload import PRESIGNED_UPLOAD_PROVIDERS
from synapse_sdk.plugins.actions.upload.enums import LogCode, UploadStatus
from synapse_sdk.plugins.actions.upload.strategies.base import (
    UploadConfig,
    UploadStrategy,
)

if TYPE_CHECKING:
    from synapse_sdk.plugins.actions.upload.context import UploadContext


class SyncUploadStrategy(UploadStrategy):
    """Synchronous upload strategy with presigned URL support.

    Automatically uses presigned URL uploads if the storage provider
    supports it, otherwise falls back to traditional upload through
    the API server.

    Supported presigned upload providers:
        - Amazon S3
        - MinIO
        - Google Cloud Storage (GCS)
        - Azure Blob Storage

    Example:
        >>> strategy = SyncUploadStrategy(context)
        >>> config = UploadConfig(chunked_threshold_mb=100)
        >>> uploaded = strategy.upload(organized_files, config)
    """

    def __init__(self, context: UploadContext):
        """Initialize with upload context.

        Args:
            context: UploadContext with client and parameters.
        """
        super().__init__(context)

    def upload(
        self,
        files: list[dict[str, Any]],
        config: UploadConfig,
    ) -> list[dict[str, Any]]:
        """Upload files synchronously.

        Automatically selects presigned or traditional upload based on
        storage provider capabilities.

        Args:
            files: List of organized file dictionaries to upload.
            config: Upload configuration.

        Returns:
            List of uploaded file information dictionaries.
        """
        if not files:
            return []

        client = self.context.client

        # Check if presigned upload is supported
        if config.use_presigned:
            try:
                storage = client.get_default_storage()
                if self._storage_supports_presigned(storage):
                    return self._upload_with_presigned_urls(files, config)
            except ValueError as e:
                self._log(
                    LogCode.FILE_UPLOAD_FAILED,
                    f'Storage configuration error, falling back to traditional upload: {e}',
                )
            except Exception as e:
                self._log(
                    LogCode.FILE_UPLOAD_FAILED,
                    f'Presigned upload check failed, falling back to traditional upload: {e}',
                )

        # Fallback to traditional upload
        return self._upload_traditional(files, config)

    def _storage_supports_presigned(self, storage: dict[str, Any]) -> bool:
        """Check if storage provider supports presigned uploads."""
        provider = storage.get('provider', '').lower()
        return provider in PRESIGNED_UPLOAD_PROVIDERS

    def _upload_with_presigned_urls(
        self,
        files: list[dict[str, Any]],
        config: UploadConfig,
    ) -> list[dict[str, Any]]:
        """Upload files using presigned URLs.

        Args:
            files: Organized files to upload.
            config: Upload configuration.

        Returns:
            List of uploaded file information.
        """
        client = self.context.client
        collection_id = self.context.params.get('data_collection')

        # Extract file paths and create mapping
        file_paths: list[Path] = []
        file_mapping: dict[Path, dict[str, Any]] = {}

        for organized_file in files:
            for file_key, file_path in organized_file.get('files', {}).items():
                if isinstance(file_path, Path) and file_path.exists():
                    file_paths.append(file_path)
                    file_mapping[file_path] = organized_file

        if not file_paths:
            return []

        try:
            # Upload using bulk upload
            result = client.upload_files_bulk(
                file_paths,
                max_workers=config.max_workers,
                batch_size=200,
            )

            # Build filename to path mapping
            filename_to_path = {path.name: path for path in file_paths}

            # Process results
            uploaded_files = []
            for file_result in result.results:
                # Extract filename from file_key
                filename = file_result.file_key.split('/')[-1] if '/' in file_result.file_key else file_result.file_key
                file_path = filename_to_path.get(filename)

                if not file_path:
                    self._log(
                        LogCode.FILE_UPLOAD_FAILED,
                        f'Received result for unknown file: {file_result.file_key}',
                    )
                    continue

                organized_file = file_mapping.get(file_path)
                if not organized_file:
                    continue

                if file_result.success:
                    self._log_status(organized_file, UploadStatus.SUCCESS)
                    uploaded_files.append({
                        'data_collection': collection_id,
                        'files': {
                            k: {'checksum': file_result.checksum, 'path': str(v)}
                            for k, v in organized_file.get('files', {}).items()
                        },
                        'meta': organized_file.get('meta', {}),
                    })
                else:
                    self._log_status(organized_file, UploadStatus.FAILED)
                    self._log(
                        LogCode.FILE_UPLOAD_FAILED,
                        f'{file_result.file_key}: {file_result.error}',
                    )

            return uploaded_files

        except ValueError as e:
            self._log(
                LogCode.FILE_UPLOAD_FAILED,
                f'Presigned upload configuration error: {e}',
            )
            return self._upload_traditional(files, config)
        except Exception as e:
            self._log(
                LogCode.FILE_UPLOAD_FAILED,
                f'Presigned upload failed: {e}',
            )
            return self._upload_traditional(files, config)

    def _upload_traditional(
        self,
        files: list[dict[str, Any]],
        config: UploadConfig,
    ) -> list[dict[str, Any]]:
        """Upload files using traditional API server method.

        Args:
            files: Organized files to upload.
            config: Upload configuration.

        Returns:
            List of uploaded file information.
        """
        uploaded_files = []
        client = self.context.client
        collection_id = self.context.params.get('data_collection')

        for organized_file in files:
            try:
                use_chunked = self._requires_chunked_upload(organized_file, config)

                # Call client upload method
                uploaded = client.upload_data_file(
                    organized_file,
                    collection_id,
                    use_chunked_upload=use_chunked,
                )

                self._log_status(organized_file, UploadStatus.SUCCESS)
                uploaded_files.append(uploaded)

            except Exception as e:
                self._log_status(organized_file, UploadStatus.FAILED)
                self._log(LogCode.FILE_UPLOAD_FAILED, str(e))
                # Continue with other files

        return uploaded_files

    def _requires_chunked_upload(
        self,
        organized_file: dict[str, Any],
        config: UploadConfig,
    ) -> bool:
        """Check if any file exceeds chunked upload threshold."""
        threshold_bytes = config.chunked_threshold_mb * 1024 * 1024

        for file_path in organized_file.get('files', {}).values():
            if isinstance(file_path, Path):
                try:
                    if file_path.stat().st_size > threshold_bytes:
                        return True
                except (OSError, IOError):
                    pass

        return False

    def _log(self, code: LogCode, message: str) -> None:
        """Log a message using the context's runtime context."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            self.context.log(code.value, {'message': message})

    def _log_status(
        self,
        organized_file: dict[str, Any],
        status: UploadStatus,
    ) -> None:
        """Log file upload status."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            self.context.log(
                LogCode.DATA_FILE_STATUS.value,
                {
                    'files': {k: str(v) for k, v in organized_file.get('files', {}).items()},
                    'status': status.value,
                },
            )


__all__ = [
    'SyncUploadStrategy',
]
