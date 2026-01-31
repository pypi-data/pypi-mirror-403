"""Custom export example using BaseExporter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synapse_sdk.plugins.actions.export.exporter import BaseExporter


class Exporter(BaseExporter):
    """Example custom exporter implementation.

    This example demonstrates:
    1. Custom data conversion (convert_data)
    2. Pre/post-processing hooks (before_convert, after_convert)
    3. Additional file saving (additional_file_saving)
    4. Custom directory structure (setup_output_directories)
    """

    def convert_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Convert data to custom format.

        This example converts annotation data to a simplified format.

        Args:
            data: Input data with annotations.

        Returns:
            Converted data in custom format.
        """
        # Example: Extract only essential fields
        converted = {
            'id': data.get('id'),
            'file_name': self.get_original_file_name(data.get('files', {})),
            'annotations': self._convert_annotations(data.get('data', {})),
            'metadata': {
                'width': data.get('files', {}).get('width'),
                'height': data.get('files', {}).get('height'),
                'project_id': self.params.get('project_id'),
            },
        }

        return converted

    def _convert_annotations(self, annotation_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Convert annotation data to simplified format.

        Args:
            annotation_data: Raw annotation data.

        Returns:
            List of converted annotations.
        """
        # Example conversion logic
        annotations = []

        # Handle different annotation types
        if 'objects' in annotation_data:
            for obj in annotation_data['objects']:
                annotations.append({
                    'type': obj.get('type', 'unknown'),
                    'label': obj.get('label'),
                    'bbox': obj.get('bbox'),
                    'confidence': obj.get('confidence', 1.0),
                })

        return annotations

    def before_convert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Pre-process data before conversion.

        This example adds project configuration to the data.

        Args:
            data: Input data.

        Returns:
            Enriched data.
        """
        # Add project configuration metadata
        if 'configuration' in self.params:
            data['project_config'] = self.params['configuration']

        # Filter out invalid data
        if not data.get('files'):
            self.run.log_dev_event(
                'Skipping item with no files',
                {'item_id': data.get('id')},
            )

        return data

    def after_convert(self, data: dict[str, Any]) -> dict[str, Any]:
        """Post-process data after conversion.

        This example validates and normalizes the converted data.

        Args:
            data: Converted data.

        Returns:
            Validated and normalized data.
        """
        # Ensure annotations field exists
        if 'annotations' not in data:
            data['annotations'] = []

        # Add conversion timestamp
        import time

        data['converted_at'] = time.time()

        return data

    def setup_output_directories(self, unique_export_path: Path, save_original_file_flag: bool) -> dict[str, Path]:
        """Setup custom directory structure.

        This example creates additional subdirectories for different file types.

        Args:
            unique_export_path: Base export path.
            save_original_file_flag: Whether to save original files.

        Returns:
            Dictionary of output paths.
        """
        # Call parent to create default directories
        output_paths = super().setup_output_directories(unique_export_path, save_original_file_flag)

        # Create additional directories
        annotations_path = unique_export_path / 'annotations'
        annotations_path.mkdir(parents=True, exist_ok=True)
        output_paths['annotations_path'] = annotations_path

        metadata_path = unique_export_path / 'metadata'
        metadata_path.mkdir(parents=True, exist_ok=True)
        output_paths['metadata_path'] = metadata_path

        return output_paths

    def additional_file_saving(self, unique_export_path: Path) -> None:
        """Save additional files after export completes.

        This example creates a summary metadata file.

        Args:
            unique_export_path: Export directory path.
        """
        import json

        # Create export summary
        summary = {
            'export_name': self.params.get('name'),
            'total_items': self.params.get('count'),
            'project_id': self.params.get('project_id'),
            'target': self.params.get('target'),
            'filters': self.params.get('filter', {}),
            'save_original_file': self.params.get('save_original_file', False),
        }

        # Save summary file
        summary_path = unique_export_path / 'export_summary.json'
        with summary_path.open('w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        self.run.log_message(f'Export summary saved to {summary_path}')

        # Create README
        readme_path = unique_export_path / 'README.md'
        readme_content = f"""# Export: {self.params.get('name')}

## Summary
- Total Items: {self.params.get('count')}
- Project ID: {self.params.get('project_id')}
- Target: {self.params.get('target')}

## Directory Structure
- `json/`: Converted JSON files
- `annotations/`: Annotation data
- `metadata/`: Metadata files
- `origin_files/`: Original files (if enabled)

## Usage
This export was generated using the custom exporter plugin.
"""
        readme_path.write_text(readme_content, encoding='utf-8')

        self.run.log_message(f'README created at {readme_path}')
