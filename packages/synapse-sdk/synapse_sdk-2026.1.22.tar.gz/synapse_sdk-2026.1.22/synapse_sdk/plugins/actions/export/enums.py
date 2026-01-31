"""Export-specific enumerations."""

from __future__ import annotations

from enum import Enum


class ExportStatus(str, Enum):
    """Export processing status enumeration.

    Defines the possible states for export operations, data files, and export items
    throughout the export process.

    Attributes:
        SUCCESS: Export completed successfully.
        FAILED: Export failed with errors.
        STAND_BY: Export waiting to be processed.
    """

    SUCCESS = 'success'
    FAILED = 'failed'
    STAND_BY = 'stand_by'
