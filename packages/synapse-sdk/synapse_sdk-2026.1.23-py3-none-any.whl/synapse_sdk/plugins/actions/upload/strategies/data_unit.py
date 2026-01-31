"""Data unit generation strategies for upload operations.

Provides strategies for creating data units from uploaded files:
    - SingleDataUnitStrategy: Create data units one at a time
    - BatchDataUnitStrategy: Create data units in batches
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from synapse_sdk.plugins.actions.upload.enums import LogCode, UploadStatus
from synapse_sdk.plugins.actions.upload.strategies.base import DataUnitStrategy

if TYPE_CHECKING:
    from synapse_sdk.plugins.actions.upload.context import UploadContext


def get_batched_list(items: list[Any], batch_size: int) -> list[list[Any]]:
    """Split a list into batches of specified size.

    Args:
        items: List to split.
        batch_size: Maximum items per batch.

    Returns:
        List of batches.
    """
    if batch_size <= 0:
        batch_size = 1
    return [items[i : i + batch_size] for i in range(0, len(items), batch_size)]


class SingleDataUnitStrategy(DataUnitStrategy):
    """Single data unit generation strategy.

    Creates data units one at a time, providing maximum control
    and error isolation per file.

    Example:
        >>> strategy = SingleDataUnitStrategy(context)
        >>> data_units = strategy.generate(uploaded_files, batch_size=1)
    """

    def __init__(self, context: UploadContext):
        """Initialize with upload context.

        Args:
            context: UploadContext with client access.
        """
        super().__init__(context)

    def generate(
        self,
        uploaded_files: list[dict[str, Any]],
        batch_size: int = 1,
    ) -> list[dict[str, Any]]:
        """Generate data units individually.

        Creates one data unit at a time, logging success/failure
        for each operation.

        Args:
            uploaded_files: List of uploaded file information.
            batch_size: Ignored (always 1 for single strategy).

        Returns:
            List of created data unit dictionaries.
        """
        if not uploaded_files:
            return []

        client = self.context.client
        generated_data_units: list[dict[str, Any]] = []

        for uploaded_file in uploaded_files:
            try:
                # Create single data unit
                created = client.create_data_units([uploaded_file])
                generated_data_units.extend(created)

                # Log success for each created data unit
                for data_unit in created:
                    self._log_data_unit(
                        data_unit.get('id'),
                        UploadStatus.SUCCESS,
                        data_unit.get('meta'),
                    )

            except Exception as e:
                self._log(LogCode.DATA_UNIT_BATCH_FAILED, str(e))
                self._log_data_unit(None, UploadStatus.FAILED, None)

        return generated_data_units

    def _log(self, code: LogCode, message: str) -> None:
        """Log a message using the context's runtime context."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            self.context.log(code.value, {'message': message})

    def _log_data_unit(
        self,
        data_unit_id: int | None,
        status: UploadStatus,
        meta: dict[str, Any] | None,
    ) -> None:
        """Log data unit creation status."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            now = datetime.now(timezone.utc)
            self.context.log(
                LogCode.DATA_UNIT_STATUS.value,
                {
                    'id': data_unit_id,
                    'data': {
                        'status': status.value,
                        'created': now.isoformat(),
                        'data_unit_id': data_unit_id,
                        'data_unit_meta': meta,
                    },
                    'datetime': now.isoformat(),
                },
            )


class BatchDataUnitStrategy(DataUnitStrategy):
    """Batch data unit generation strategy.

    Creates data units in batches for improved performance with
    large numbers of files.

    Example:
        >>> strategy = BatchDataUnitStrategy(context)
        >>> data_units = strategy.generate(uploaded_files, batch_size=50)
    """

    def __init__(self, context: UploadContext):
        """Initialize with upload context.

        Args:
            context: UploadContext with client access.
        """
        super().__init__(context)

    def generate(
        self,
        uploaded_files: list[dict[str, Any]],
        batch_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Generate data units in batches.

        Creates data units in batches of specified size for
        better performance with large file sets.

        Args:
            uploaded_files: List of uploaded file information.
            batch_size: Number of data units to create per batch.

        Returns:
            List of created data unit dictionaries.
        """
        if not uploaded_files:
            return []

        client = self.context.client
        generated_data_units: list[dict[str, Any]] = []

        # Split into batches
        batches = get_batched_list(uploaded_files, batch_size)

        for batch in batches:
            try:
                # Create batch of data units
                created = client.create_data_units(batch)
                generated_data_units.extend(created)

                # Log success for each created data unit
                for data_unit in created:
                    self._log_data_unit(
                        data_unit.get('id'),
                        UploadStatus.SUCCESS,
                        data_unit.get('meta'),
                    )

            except Exception as e:
                self._log(LogCode.DATA_UNIT_BATCH_FAILED, str(e))
                # Log failure for each item in batch
                for _ in batch:
                    self._log_data_unit(None, UploadStatus.FAILED, None)

        return generated_data_units

    def _log(self, code: LogCode, message: str) -> None:
        """Log a message using the context's runtime context."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            self.context.log(code.value, {'message': message})

    def _log_data_unit(
        self,
        data_unit_id: int | None,
        status: UploadStatus,
        meta: dict[str, Any] | None,
    ) -> None:
        """Log data unit creation status."""
        if hasattr(self.context, 'runtime_ctx') and self.context.runtime_ctx:
            now = datetime.now(timezone.utc)
            self.context.log(
                LogCode.DATA_UNIT_STATUS.value,
                {
                    'id': data_unit_id,
                    'data': {
                        'status': status.value,
                        'created': now.isoformat(),
                        'data_unit_id': data_unit_id,
                        'data_unit_meta': meta,
                    },
                    'datetime': now.isoformat(),
                },
            )


__all__ = [
    'get_batched_list',
    'SingleDataUnitStrategy',
    'BatchDataUnitStrategy',
]
