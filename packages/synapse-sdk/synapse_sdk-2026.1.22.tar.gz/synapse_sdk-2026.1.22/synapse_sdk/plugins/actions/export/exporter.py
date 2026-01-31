"""Base exporter class for plugin developers.

This module provides a template-based interface for implementing custom export logic,
adapted from the legacy synapse-sdk to work with synapse-sdk-v2's architecture.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import requests

from synapse_sdk.plugins.actions.export.enums import ExportStatus
from synapse_sdk.plugins.actions.export.log_messages import ExportLogMessageCode
from synapse_sdk.plugins.models.logger import LogLevel

if TYPE_CHECKING:
    from synapse_sdk.loggers import BaseLogger
    from synapse_sdk.plugins.context import RuntimeContext


class MetricsRecord:
    """Metrics record for tracking export progress.

    Tracks the status distribution of export operations (success, failed, stand_by).

    Attributes:
        stand_by: Number of items waiting to be processed.
        success: Number of successfully processed items.
        failed: Number of failed items.
    """

    def __init__(self, stand_by: int = 0, success: int = 0, failed: int = 0) -> None:
        """Initialize metrics record.

        Args:
            stand_by: Number of items waiting to be processed.
            success: Number of successfully processed items.
            failed: Number of failed items.
        """
        self.stand_by = stand_by
        self.success = success
        self.failed = failed

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary for metrics logging.

        Returns:
            Dictionary with 'stand_by', 'success', and 'failed' keys.
        """
        return {
            'stand_by': self.stand_by,
            'success': self.success,
            'failed': self.failed,
        }


class ExporterRunAdapter:
    """Adapter to make BaseLogger compatible with legacy 'run' interface.

    This adapter provides backward compatibility with the legacy BaseExporter
    interface while delegating to the new BaseLogger implementation.
    """

    MetricsRecord = MetricsRecord

    def __init__(self, logger: BaseLogger) -> None:
        """Initialize the adapter.

        Args:
            logger: BaseLogger instance to delegate to.
        """
        self._logger = logger

    def log_message(self, message: str) -> None:
        """Log a simple message.

        Args:
            message: Message to log.
        """
        self._logger.info(message)

    def log_export_event(self, event_code: str, item_id: int) -> None:
        """Log an export event.

        Args:
            event_code: Event code identifier.
            item_id: ID of the item being exported.
        """
        from synapse_sdk.plugins.models.logger import LogLevel

        self._logger.log(LogLevel.INFO, event_code, {'item_id': item_id})

    def log_dev_event(self, message: str, data: dict[str, Any] | None = None, level: Any = None) -> None:
        """Log a development event.

        Args:
            message: Event message.
            data: Additional event data.
            level: Log level (legacy Context enum or LogLevel).
        """
        from synapse_sdk.plugins.models.logger import LogLevel

        if data is None:
            data = {}

        # Map legacy Context enum to LogLevel
        log_level = self._map_level(level) or LogLevel.INFO
        self._logger.log(log_level, message, data)

    def set_progress(self, current: int, total: int, category: str = 'default') -> None:
        """Track progress.

        Args:
            current: Current progress value.
            total: Total expected value.
            category: Progress category name.
        """
        self._logger.set_progress(current, total, category=category)

    def log_metrics(self, record: MetricsRecord, category: str) -> None:
        """Log metrics record.

        Args:
            record: Metrics record to log.
            category: Metrics category name.
        """
        self._logger.set_metrics(
            value=record.to_dict(),
            category=category,
        )

    def export_log_original_file(
        self, item_id: int, file_info: dict[str, Any], status: ExportStatus, error_msg: str
    ) -> None:
        """Log original file export status.

        Args:
            item_id: ID of the item.
            file_info: File information dict.
            status: Export status.
            error_msg: Error message if failed.
        """
        import json
        from datetime import datetime

        from synapse_sdk.plugins.models.logger import LogLevel

        self._logger.log(
            LogLevel.INFO,
            'export_original_file',
            {
                'target_id': item_id,
                'original_file_info': json.dumps(file_info),
                'status': status.value,
                'error': error_msg,
                'created': datetime.now().isoformat(),
            },
        )

    def export_log_data_file(
        self, item_id: int, file_info: dict[str, Any], status: ExportStatus, error_msg: str
    ) -> None:
        """Log data file export status.

        Args:
            item_id: ID of the item.
            file_info: File information dict.
            status: Export status.
            error_msg: Error message if failed.
        """
        import json
        from datetime import datetime

        from synapse_sdk.plugins.models.logger import LogLevel

        self._logger.log(
            LogLevel.INFO,
            'export_data_file',
            {
                'target_id': item_id,
                'data_file_info': json.dumps(file_info),
                'status': status.value,
                'error': error_msg,
                'created': datetime.now().isoformat(),
            },
        )

    def end_log(self) -> None:
        """Mark logging complete."""
        self._logger.finish()

    @staticmethod
    def _map_level(old_level: Any) -> LogLevel | None:
        """Map legacy Context enum to new LogLevel.

        Args:
            old_level: Legacy Context enum value or LogLevel.

        Returns:
            LogLevel instance or None.
        """
        if old_level is None:
            return None

        # If already LogLevel, return as-is
        if isinstance(old_level, LogLevel):
            return old_level

        # Map legacy Context enum values
        # Context.SUCCESS -> LogLevel.INFO
        # Context.WARNING -> LogLevel.WARNING
        # Context.DANGER -> LogLevel.ERROR
        level_map = {
            'success': LogLevel.INFO,
            'warning': LogLevel.WARNING,
            'danger': LogLevel.ERROR,
            'info': LogLevel.INFO,
            'error': LogLevel.ERROR,
        }

        # Try to get value from enum
        if hasattr(old_level, 'value'):
            level_str = old_level.value.lower()
        else:
            level_str = str(old_level).lower()

        return level_map.get(level_str, LogLevel.INFO)


class BaseExporter:
    """Base class for export plugins with common functionality.

    This class provides a template-based interface for plugin developers
    to implement custom export logic. It adapts to synapse-sdk-v2's
    architecture while preserving the legacy interface.

    Core Methods:
        export(): Main export workflow.
        process_data_conversion(): Data conversion pipeline.
        process_file_saving(): File saving operations.
        setup_output_directories(): Directory setup.

    Template Methods (override in subclasses):
        convert_data(): Transform data during export.
        before_convert(): Pre-process data before conversion.
        after_convert(): Post-process data after conversion.
        save_original_file(): Save original files.
        save_as_json(): Save data as JSON files.
        additional_file_saving(): Post-export file operations.

    Helper Methods:
        _process_original_file_saving(): Handle original file saving with metrics.
        _process_json_file_saving(): Handle JSON file saving with metrics.

    Attributes:
        ctx: Runtime context with logger and client.
        export_items: Generator of items to export.
        path_root: Root path for export output.
        params: Additional parameters dict.
        run: Logger adapter (for backward compatibility).
    """

    def __init__(
        self,
        ctx: RuntimeContext,
        export_items: Generator,
        path_root: Path | str,
        **params: Any,
    ) -> None:
        """Initialize the base export class.

        Args:
            ctx: Runtime context with logger and client.
            export_items: Export items generator.
            path_root: Root path for export output.
            **params: Additional parameters:
                - name (str): The name of the action.
                - description (str | None): The description of the action.
                - storage (int): The storage ID to save the exported data.
                - save_original_file (bool): Whether to save the original file.
                - path (str): The path to save the exported data.
                - target (str): The target source to export data from.
                - filter (dict): The filter criteria to apply.
                - extra_params (dict | None): Additional parameters.
                - count (int): Total number of results.
                - results (list): List of results fetched through the list API.
                - project_id (int): Project ID.
                - configuration (dict): Project configuration.
        """
        self.ctx = ctx
        self.export_items = export_items
        self.path_root = Path(path_root)
        self.params = params

        # Adapter: expose logger as 'run' for compatibility
        self.run = ExporterRunAdapter(ctx.logger)

    def _create_unique_export_path(self, base_name: str) -> Path:
        """Create a unique export path to avoid conflicts.

        Args:
            base_name: Base name for the export directory.

        Returns:
            Path to the unique export directory (created).
        """
        export_path = self.path_root / base_name
        unique_export_path = export_path
        counter = 1
        while unique_export_path.exists():
            unique_export_path = export_path.with_name(f'{export_path.name}({counter})')
            counter += 1
        unique_export_path.mkdir(parents=True)
        return unique_export_path

    def _save_error_list(
        self, export_path: Path, errors_json_file_list: list[Any], errors_original_file_list: list[Any]
    ) -> None:
        """Save error list files if there are any errors.

        Args:
            export_path: Path to the export directory.
            errors_json_file_list: List of JSON file errors.
            errors_original_file_list: List of original file errors.
        """
        if len(errors_json_file_list) > 0 or len(errors_original_file_list) > 0:
            export_error_file = {
                'json_file_name': errors_json_file_list,
                'origin_file_name': errors_original_file_list,
            }
            with (export_path / 'error_file_list.json').open('w', encoding='utf-8') as f:
                json.dump(export_error_file, f, indent=4, ensure_ascii=False)

    def get_original_file_name(self, files: dict[str, Any]) -> str:
        """Retrieve the original file path from the given file information.

        Args:
            files: A dictionary containing file information.

        Returns:
            The original file name extracted from the file information.
        """
        return files['file_name_original']

    def save_original_file(self, result: dict[str, Any], base_path: Path, error_file_list: list[Any]) -> ExportStatus:
        """Save the original file.

        Args:
            result: API response data containing file information.
            base_path: The directory where the file will be saved.
            error_file_list: A list to store error files.

        Returns:
            ExportStatus indicating success or failure.
        """
        file_url = result['files']['url']
        file_name = self.get_original_file_name(result['files'])
        response = requests.get(file_url, timeout=30)
        file_info = {'file_name': file_name}
        error_msg = ''
        try:
            with (base_path / file_name).open('wb') as file:
                file.write(response.content)
            status = ExportStatus.SUCCESS
        except Exception as e:
            error_msg = str(e)
            error_file_list.append([file_name, error_msg])
            status = ExportStatus.FAILED

        self.run.export_log_original_file(result['id'], file_info, status, error_msg)
        return status

    def save_as_json(self, result: dict[str, Any], base_path: Path, error_file_list: list[Any]) -> ExportStatus:
        """Save the data as a JSON file.

        Args:
            result: API response data containing file information.
            base_path: The directory where the file will be saved.
            error_file_list: A list to store error files.

        Returns:
            ExportStatus indicating success or failure.
        """
        file_name = Path(self.get_original_file_name(result['files'])).stem
        json_data = result['data']
        file_info = {'file_name': f'{file_name}.json'}

        if json_data is None:
            error_msg = 'data is Null'
            error_file_list.append([f'{file_name}.json', error_msg])
            status = ExportStatus.FAILED
            self.run.log_export_event('NULL_DATA_DETECTED', result['id'])
            self.run.export_log_data_file(result['id'], file_info, status, error_msg)
            return status

        error_msg = ''
        try:
            with (base_path / f'{file_name}.json').open('w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=4, ensure_ascii=False)
            status = ExportStatus.SUCCESS
        except Exception as e:
            error_msg = str(e)
            error_file_list.append([f'{file_name}.json', str(e)])
            status = ExportStatus.FAILED

        self.run.export_log_data_file(result['id'], file_info, status, error_msg)
        return status

    # Template methods that should be implemented by subclasses
    def convert_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert the data. Should be implemented by subclasses.

        Args:
            data: Input data to convert.

        Returns:
            Converted data.
        """
        return data

    def before_convert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Preprocess the data before conversion. Should be implemented by subclasses.

        Args:
            data: Input data.

        Returns:
            Preprocessed data.
        """
        return data

    def after_convert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Post-process the data after conversion. Should be implemented by subclasses.

        Args:
            data: Converted data.

        Returns:
            Post-processed data.
        """
        return data

    def _process_original_file_saving(
        self,
        final_data: dict[str, Any],
        origin_files_output_path: Path,
        errors_original_file_list: list[Any],
        original_file_metrics_record: MetricsRecord,
        no: int,
    ) -> bool:
        """Process original file saving with metrics tracking.

        Args:
            final_data: Converted data to save.
            origin_files_output_path: Path to save original files.
            errors_original_file_list: List to collect errors.
            original_file_metrics_record: Metrics record for tracking.
            no: Current item number for logging.

        Returns:
            True if processing should continue, False if should skip to next item.
        """
        if no == 1:
            self.run.log_message(ExportLogMessageCode.EXPORT_SAVING_ORIGINAL)
        original_status = self.save_original_file(final_data, origin_files_output_path, errors_original_file_list)

        original_file_metrics_record.stand_by -= 1
        if original_status == ExportStatus.FAILED:
            original_file_metrics_record.failed += 1
            return False  # Skip to next item
        else:
            original_file_metrics_record.success += 1
            return True  # Continue processing

    def _process_json_file_saving(
        self,
        final_data: dict[str, Any],
        json_output_path: Path,
        errors_json_file_list: list[Any],
        data_file_metrics_record: MetricsRecord,
        no: int,
    ) -> bool:
        """Process JSON file saving with metrics tracking.

        Args:
            final_data: Converted data to save.
            json_output_path: Path to save JSON files.
            errors_json_file_list: List to collect errors.
            data_file_metrics_record: Metrics record for tracking.
            no: Current item number for logging.

        Returns:
            True if processing should continue, False if should skip to next item.
        """
        if no == 1:
            self.run.log_message(ExportLogMessageCode.EXPORT_SAVING_JSON)
        data_status = self.save_as_json(final_data, json_output_path, errors_json_file_list)

        data_file_metrics_record.stand_by -= 1
        if data_status == ExportStatus.FAILED:
            data_file_metrics_record.failed += 1
            return False  # Skip to next item
        else:
            data_file_metrics_record.success += 1
            return True  # Continue processing

    def setup_output_directories(self, unique_export_path: Path, save_original_file_flag: bool) -> dict[str, Path]:
        """Setup output directories for export.

        This method can be overridden by subclasses to customize directory structure.
        The default implementation creates 'json' and 'origin_files' directories.

        Args:
            unique_export_path: Base path for export.
            save_original_file_flag: Whether original files will be saved.

        Returns:
            Dictionary containing paths for different file types.
            Example: {'json_output_path': Path, 'origin_files_output_path': Path}
        """
        # Path to save JSON files
        json_output_path = unique_export_path / 'json'
        json_output_path.mkdir(parents=True, exist_ok=True)

        output_paths = {'json_output_path': json_output_path}

        # Path to save original files
        if save_original_file_flag:
            origin_files_output_path = unique_export_path / 'origin_files'
            origin_files_output_path.mkdir(parents=True, exist_ok=True)
            output_paths['origin_files_output_path'] = origin_files_output_path

        return output_paths

    def process_data_conversion(self, export_item: dict[str, Any]) -> dict[str, Any]:
        """Process data conversion pipeline for a single export item.

        This method handles the complete data conversion process:
        before_convert -> convert_data -> after_convert

        Args:
            export_item: Single export item to process.

        Returns:
            Final processed data ready for saving.
        """
        preprocessed_data = self.before_convert(export_item)
        converted_data = self.convert_data(preprocessed_data)
        final_data = self.after_convert(converted_data)
        return final_data

    def process_file_saving(
        self,
        final_data: dict[str, Any],
        unique_export_path: Path,
        save_original_file_flag: bool,
        errors_json_file_list: list[Any],
        errors_original_file_list: list[Any],
        original_file_metrics_record: MetricsRecord,
        data_file_metrics_record: MetricsRecord,
        no: int,
    ) -> bool:
        """Process file saving operations for a single export item.

        This method can be overridden by subclasses to implement custom file saving logic.
        The default implementation saves original files and JSON files based on configuration.

        Args:
            final_data: Converted data ready for saving.
            unique_export_path: Base path for export.
            save_original_file_flag: Whether to save original files.
            errors_json_file_list: List to collect JSON file errors.
            errors_original_file_list: List to collect original file errors.
            original_file_metrics_record: Metrics record for original files.
            data_file_metrics_record: Metrics record for JSON files.
            no: Current item number for logging.

        Returns:
            True if processing should continue, False if should skip to next item.
        """
        json_output_path = unique_export_path / 'json'
        origin_files_output_path = unique_export_path / 'origin_files' if save_original_file_flag else None
        total = self.params['count']

        if save_original_file_flag:
            # 원본 파일 저장 progress
            self.run.set_progress(no, total, category='original_file')
            should_continue = self._process_original_file_saving(
                final_data, origin_files_output_path, errors_original_file_list, original_file_metrics_record, no
            )
            self.run.log_metrics(record=original_file_metrics_record, category='original_file')
            if not should_continue:
                return False

        # JSON 파일 저장 progress
        self.run.set_progress(no, total, category='data_file')
        should_continue = self._process_json_file_saving(
            final_data, json_output_path, errors_json_file_list, data_file_metrics_record, no
        )
        self.run.log_metrics(record=data_file_metrics_record, category='data_file')

        return should_continue

    def additional_file_saving(self, unique_export_path: Path) -> None:
        """Save additional files after processing all export items.

        This method is called after the main export loop completes and is intended
        for saving files that need to be created based on the collective data from
        all processed export items (e.g., metadata files, configuration files,
        summary files, etc.).

        Args:
            unique_export_path: The unique export directory path where
                additional files should be saved.
        """
        pass

    def export(
        self, export_items: Generator | None = None, results: list[Any] | None = None, **_kwargs: Any
    ) -> dict[str, Any]:
        """Main export method that can be overridden by subclasses for custom logic.

        This default implementation provides standard file saving functionality.
        Subclasses can override this method to implement custom export logic
        while still using the helper methods for specific operations.

        Subclasses can override process_file_saving() method to implement custom file saving logic.

        Args:
            export_items: Optional export items to process. If not provided, uses self.export_items.
            results: Optional results data to process alongside export_items.
            **_kwargs: Additional parameters for export customization (unused in base implementation).

        Returns:
            Export result dict containing export path and status information.
        """
        # Use provided export_items or fall back to instance variable
        items_to_process = export_items if export_items is not None else self.export_items

        unique_export_path = self._create_unique_export_path(self.params['name'])

        self.run.log_message(ExportLogMessageCode.EXPORT_STARTING)

        save_original_file_flag = self.params.get('save_original_file', False)
        errors_json_file_list: list[Any] = []
        errors_original_file_list: list[Any] = []

        # Setup output directories (can be customized by subclasses)
        self.setup_output_directories(unique_export_path, save_original_file_flag)

        total = self.params['count']

        if save_original_file_flag:
            original_file_metrics_record = self.run.MetricsRecord(stand_by=total, success=0, failed=0)
        else:
            original_file_metrics_record = self.run.MetricsRecord(stand_by=0, success=0, failed=0)
        data_file_metrics_record = self.run.MetricsRecord(stand_by=total, success=0, failed=0)

        # progress init - 모든 카테고리 0%로 초기화
        self.run.set_progress(0, total, category='dataset_conversion')
        if save_original_file_flag:
            self.run.set_progress(0, total, category='original_file')
        self.run.set_progress(0, total, category='data_file')

        for no, export_item in enumerate(items_to_process, start=1):
            self.run.set_progress(min(no, total), total, category='dataset_conversion')
            if no == 1:
                self.run.log_message(ExportLogMessageCode.EXPORT_CONVERTING_DATASET)

            final_data = self.process_data_conversion(export_item)

            # Process file saving (can be overridden by subclasses)
            should_continue = self.process_file_saving(
                final_data,
                unique_export_path,
                save_original_file_flag,
                errors_json_file_list,
                errors_original_file_list,
                original_file_metrics_record,
                data_file_metrics_record,
                no,
            )
            if not should_continue:
                continue

        self.additional_file_saving(unique_export_path)

        # Save error list files
        self._save_error_list(unique_export_path, errors_json_file_list, errors_original_file_list)

        return {'export_path': str(self.path_root)}
