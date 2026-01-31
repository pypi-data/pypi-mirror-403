# Custom Exporter Example

This example demonstrates how to create a custom export plugin using the `BaseExporter` class.

## Overview

The `BaseExporter` class provides a template-based interface for implementing custom export logic. It handles common export tasks like:

- Progress tracking
- File saving (original files and JSON)
- Error handling and logging
- Metrics collection
- Directory structure setup

## File Structure

```
custom_exporter/
├── README.md              # This file
├── plugin/
│   ├── __init__.py       # Plugin package init
│   └── export.py         # Exporter implementation
└── requirements.txt       # Dependencies (optional)
```

## Implementation

The example `Exporter` class in `plugin/export.py` demonstrates:

1. **Custom Data Conversion** (`convert_data`):
   - Extracts essential fields from input data
   - Converts annotations to simplified format

2. **Pre-processing** (`before_convert`):
   - Enriches data with project configuration
   - Filters out invalid data

3. **Post-processing** (`after_convert`):
   - Validates converted data
   - Adds conversion timestamp

4. **Custom Directory Structure** (`setup_output_directories`):
   - Creates additional subdirectories for annotations and metadata

5. **Additional Files** (`additional_file_saving`):
   - Generates export summary JSON
   - Creates README file

## Usage

### In an Export Action

```python
from pathlib import Path
from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.context import RuntimeContext
from plugin.export import Exporter

class MyExportAction(BaseAction):
    action_name = 'my_export'

    def execute(self) -> dict:
        # Fetch data to export (example)
        export_items = self._fetch_export_items()

        # Create exporter instance
        exporter = Exporter(
            ctx=self.ctx,
            export_items=export_items,
            path_root=Path('/tmp/exports'),
            name='my_custom_export',
            count=100,
            save_original_file=True,
            project_id=123,
            configuration={'name': 'My Project'},
        )

        # Run export
        result = exporter.export()

        return result

    def _fetch_export_items(self):
        # Yield export items
        for i in range(10):
            yield {
                'id': i,
                'files': {
                    'url': f'https://example.com/file_{i}.jpg',
                    'file_name_original': f'image_{i}.jpg',
                    'width': 1920,
                    'height': 1080,
                },
                'data': {
                    'objects': [
                        {
                            'type': 'bbox',
                            'label': 'person',
                            'bbox': [100, 100, 200, 200],
                            'confidence': 0.95,
                        }
                    ]
                },
            }
```

### Standalone Usage

```python
from pathlib import Path
from synapse_sdk.plugins.context import RuntimeContext
from synapse_sdk.loggers import ConsoleLogger
from plugin.export import Exporter

# Create runtime context
ctx = RuntimeContext(
    logger=ConsoleLogger(),
    plugin_name='my_export',
)

# Create export items generator
def export_items_generator():
    for i in range(10):
        yield {
            'id': i,
            'files': {
                'url': f'https://example.com/file_{i}.jpg',
                'file_name_original': f'image_{i}.jpg',
                'width': 1920,
                'height': 1080,
            },
            'data': {
                'objects': [
                    {
                        'type': 'bbox',
                        'label': 'person',
                        'bbox': [100, 100, 200, 200],
                    }
                ]
            },
        }

# Create exporter
exporter = Exporter(
    ctx=ctx,
    export_items=export_items_generator(),
    path_root=Path('/tmp/exports'),
    name='my_custom_export',
    count=10,
    save_original_file=True,
    project_id=123,
    configuration={'name': 'My Project'},
)

# Run export
result = exporter.export()
print(f"Export completed: {result}")
```

## Output Structure

After running the export, the output directory will have this structure:

```
/tmp/exports/my_custom_export/
├── json/                      # Converted JSON files
│   ├── image_0.json
│   ├── image_1.json
│   └── ...
├── origin_files/              # Original files (if enabled)
│   ├── image_0.jpg
│   ├── image_1.jpg
│   └── ...
├── annotations/               # Custom: Annotations directory
├── metadata/                  # Custom: Metadata directory
├── export_summary.json        # Custom: Export summary
├── README.md                  # Custom: Export README
└── error_file_list.json       # Error list (if any errors)
```

## Customization

### Override Methods

You can override these methods to customize behavior:

- `convert_data(data)`: Transform data format
- `before_convert(data)`: Pre-process data
- `after_convert(data)`: Post-process data
- `save_original_file(result, base_path, error_list)`: Custom file saving
- `save_as_json(result, base_path, error_list)`: Custom JSON saving
- `setup_output_directories(path, flag)`: Custom directory structure
- `process_file_saving(...)`: Custom file saving workflow
- `additional_file_saving(path)`: Post-export operations

### Logging

The `self.run` adapter provides logging methods:

```python
# Simple message
self.run.log_message('Processing item...')

# Event logging
self.run.log_export_event('ITEM_PROCESSED', item_id=123)

# Development logging
self.run.log_dev_event(
    'Custom event',
    {'key': 'value'},
    level=LogLevel.INFO
)

# Progress tracking
self.run.set_progress(current=50, total=100, category='conversion')

# Metrics tracking
metrics = self.run.MetricsRecord(stand_by=10, success=90, failed=0)
self.run.log_metrics(record=metrics, category='export')
```

## Migration from Legacy SDK

If you have an existing exporter from the legacy synapse-sdk, the migration is straightforward:

### Legacy (synapse-sdk)
```python
class Exporter(BaseExporter):
    def __init__(self, run, export_items, path_root, **params):
        super().__init__(run, export_items, path_root, **params)
```

### V2 (synapse-sdk-v2)
```python
class Exporter(BaseExporter):
    def __init__(self, ctx, export_items, path_root, **params):
        super().__init__(ctx, export_items, path_root, **params)
```

**Changes**:
- Replace `run` parameter with `ctx` (RuntimeContext)
- `self.run` still available via adapter (no code changes needed)
- Use `Path` objects instead of strings for paths

## See Also

- [BaseExporter API Documentation](../../../synapse_sdk/plugins/actions/export/exporter.py)
- [Export Action Documentation](../../../synapse_sdk/plugins/actions/export/action.py)
- [EXPORTER_MIGRATION.md](../../../EXPORTER_MIGRATION.md) - Full migration guide
