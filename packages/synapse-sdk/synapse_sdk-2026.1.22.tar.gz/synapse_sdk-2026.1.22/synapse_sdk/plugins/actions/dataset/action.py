"""Dataset action with download and convert operations.

A single action class that handles both dataset download and format conversion,
selected via the operation parameter. Designed for pipeline composition.
"""

from __future__ import annotations

import json
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from synapse_sdk.plugins.action import BaseAction
from synapse_sdk.plugins.actions.dataset.log_messages import DatasetLogMessageCode
from synapse_sdk.plugins.enums import PluginCategory
from synapse_sdk.plugins.types import YOLODataset
from synapse_sdk.utils.annotation_models.dm import DMVersion
from synapse_sdk.utils.converters import DatasetFormat, get_converter

if TYPE_CHECKING:
    from synapse_sdk.clients.backend import BackendClient


class DatasetOperation(StrEnum):
    """Dataset operation types."""

    DOWNLOAD = 'download'
    CONVERT = 'convert'


class DatasetParams(BaseModel):
    """Parameters for DatasetAction.

    The operation field determines which operation to perform:
    - download: Downloads dataset from backend
    - convert: Converts dataset from one format to another

    Attributes:
        operation: Which operation to perform.
        dataset: Ground truth dataset ID (for download with annotations).
        splits: Split definitions for categorized download.
        path: Source dataset path (for convert, or set by download).
        source_format: Source format (for convert).
        target_format: Target format (for convert).
        dm_version: Datamaker version (for convert from DM).
        output_dir: Output directory (optional for both).
        is_categorized: Whether dataset has train/valid/test splits.
    """

    operation: DatasetOperation = DatasetOperation.DOWNLOAD

    # Download params
    dataset: int | None = Field(default=None, description='Ground truth dataset ID')
    splits: dict[str, dict[str, Any]] | None = Field(
        default=None,
        description='Split definitions: {"train": {...filters}, "valid": {...}}',
    )

    # Convert params
    path: Path | str | None = Field(default=None, description='Dataset path')
    source_format: str = Field(default='dm_v2', description='Source format')
    target_format: str = Field(default='yolo', description='Target format')
    dm_version: str = Field(default='v2', description='Datamaker version')

    # Shared params
    output_dir: Path | str | None = Field(default=None, description='Output directory')
    is_categorized: bool = Field(default=False, description='Has splits')


class DatasetResult(BaseModel):
    """Result from DatasetAction.

    Contains paths and metadata about the processed dataset.

    Attributes:
        path: Path to dataset directory.
        format: Dataset format (e.g., 'dm_v2', 'yolo').
        is_categorized: Whether dataset has splits.
        config_path: Path to config file (e.g., dataset.yaml for YOLO).
        count: Number of items processed.
        source_path: Original source path (for convert).
        data_path: Computed property returning config_path if set, otherwise path.
    """

    path: Path
    format: str
    is_categorized: bool = False
    config_path: Path | None = None
    count: int | None = None
    source_path: Path | None = None

    @property
    def data_path(self) -> Path:
        """Returns config_path if set, otherwise path.

        Use this for downstream actions that need a single path
        to the dataset (e.g., training with YOLO format).
        """
        return self.config_path if self.config_path is not None else self.path

    class Config:
        arbitrary_types_allowed = True


class DatasetAction(BaseAction[DatasetParams]):
    """Dataset action with download and convert operations.

    A unified action for dataset operations that can be used in pipelines.
    The operation is determined by the params.operation field.

    Type declarations:
        - input_type: None (accepts initial params)
        - output_type: Dynamic based on operation and target_format
          - download: 'dm_dataset'
          - convert to yolo: 'yolo_dataset'
          - convert to coco: 'coco_dataset'

    For download:
        - Requires: dataset
        - Optional: splits, output_dir
        - Returns: path, format='dm_v2', is_categorized, count

    For convert:
        - Requires: path, target_format
        - Optional: source_format, dm_version, output_dir
        - Returns: path, format, config_path, source_path

    Example:
        >>> # Standalone usage
        >>> action = DatasetAction(
        ...     DatasetParams(operation='download', dataset=123),
        ...     ctx,
        ... )
        >>> result = action.execute()
        >>>
        >>> # Pipeline usage
        >>> pipeline = ActionPipeline([DatasetAction, DatasetAction, TrainAction])
        >>> result = pipeline.execute({
        ...     'operation': 'download',
        ...     'dataset': 123,
        ...     'target_format': 'yolo',  # Used by second DatasetAction
        ... }, ctx)
    """

    category = PluginCategory.NEURAL_NET

    @classmethod
    def get_log_message_code_class(cls) -> type[DatasetLogMessageCode]:
        from synapse_sdk.plugins.actions.dataset.log_messages import DatasetLogMessageCode

        return DatasetLogMessageCode

    # Input type is flexible (accepts various initial params)
    input_type = None
    # Output type: use YOLODataset for convert (most common), DMv2Dataset for download
    # For precise typing, use separate DownloadAction/ConvertAction classes
    output_type = YOLODataset  # Default assumes convert to YOLO

    result_model = DatasetResult

    @property
    def client(self) -> BackendClient:
        """Backend client from context."""
        if self.ctx.client is None:
            raise RuntimeError('No backend client in context')
        return self.ctx.client

    def execute(self) -> DatasetResult:
        """Execute the dataset operation based on params.operation."""
        if self.params.operation == DatasetOperation.DOWNLOAD:
            return self.download()
        elif self.params.operation == DatasetOperation.CONVERT:
            return self.convert()
        else:
            raise ValueError(f'Unknown operation: {self.params.operation}')

    def download(self) -> DatasetResult:
        """Download dataset from backend.

        Downloads ground truth events (annotated data) and saves them
        locally in Datamaker format (json/ + original_files/).

        Returns:
            DatasetResult with path, format, count.

        Raises:
            ValueError: If dataset not provided.
        """
        import time

        from synapse_sdk.utils.file import get_temp_path

        if self.params.dataset is None:
            raise ValueError('dataset is required for download operation')

        dataset = self.params.dataset
        splits = self.params.splits
        is_categorized = splits is not None and len(splits) > 0

        # Determine output directory (use timestamp for unique path)
        if self.params.output_dir:
            output_dir = Path(self.params.output_dir)
        else:
            timestamp = int(time.time())
            output_dir = get_temp_path(f'datasets/{dataset}_{timestamp}')
        output_dir = Path(output_dir)

        # Report initial progress
        self.set_progress(0, 100, 'init')

        self.log(
            'download_start',
            {
                'dataset': dataset,
                'is_categorized': is_categorized,
            },
        )
        self.log_message(DatasetLogMessageCode.DATASET_DOWNLOAD_STARTING, dataset_id=dataset)

        # Report init complete
        self.set_progress(1, 100, 'init')

        total_downloaded = 0

        if is_categorized and splits:
            # Download each split separately (category filter)
            for split_name, filters in splits.items():
                split_dir = output_dir / split_name
                # Map split names to API category values
                category = {'train': 'train', 'valid': 'validation', 'test': 'test'}.get(split_name, split_name)
                count = self._download_split(
                    dataset=dataset,
                    output_dir=split_dir,
                    filters={'category': category, **(filters or {})},
                )
                total_downloaded += count
                self.log(
                    'split_downloaded',
                    {
                        'split': split_name,
                        'count': count,
                    },
                )
                self.log_message(DatasetLogMessageCode.DATASET_SPLIT_DOWNLOADED, split_name=split_name, count=count)
        else:
            # Download all ground truth events
            total_downloaded = self._download_split(
                dataset=dataset,
                output_dir=output_dir,
                filters={},
            )

        self.log(
            'download_complete',
            {
                'path': str(output_dir),
                'total_units': total_downloaded,
            },
        )
        self.log_message(DatasetLogMessageCode.DATASET_DOWNLOAD_COMPLETED, count=total_downloaded)

        return DatasetResult(
            path=output_dir,
            format='dm_v2',
            is_categorized=is_categorized,
            count=total_downloaded,
        )

    def _download_split(
        self,
        dataset: int,
        output_dir: Path,
        filters: dict[str, Any],
        max_workers: int = 10,
    ) -> int:
        """Download a single split of the dataset."""
        # Create output directories
        json_dir = output_dir / 'json'
        files_dir = output_dir / 'original_files'
        json_dir.mkdir(parents=True, exist_ok=True)
        files_dir.mkdir(parents=True, exist_ok=True)

        # Report fetching ground truth events
        self.set_progress(2, 100, 'fetch')

        params = {
            'fields': ['category', 'files', 'data'],
            'expand': ['data'],
            'ground_truth_dataset_versions': dataset,
            **filters,
        }
        gt_events_gen, total_count = self.client.list_ground_truth_events(
            params=params,
            list_all=True,
        )

        # Report events fetched
        self.set_progress(5, 100, 'fetch')
        self.log('gt_events_listed', {'total_count': total_count})
        self.log_message(DatasetLogMessageCode.DATASET_GT_EVENTS_FOUND, count=total_count)

        downloaded = 0
        images_found = 0
        images_not_found = 0

        def download_event(event: dict) -> bool:
            """Download a single ground truth event."""
            nonlocal images_found, images_not_found
            try:
                event_id = event.get('id')
                files = event.get('files', {})

                # Copy/download files, tracking the primary image file and annotation JSON
                primary_image_dest = None
                annotation_json_content = None

                # Handle files as dict (keyed by 'image_1', 'data_meta_1', etc.)
                if isinstance(files, dict):
                    for file_key, file_info in files.items():
                        if not isinstance(file_info, dict):
                            # Debug: Log non-dict file_info for first event
                            if images_found == 0 and images_not_found == 0:
                                self.log(
                                    'debug_file_not_dict',
                                    {'file_key': file_key, 'file_info_type': type(file_info).__name__},
                                )
                            continue

                        file_path = file_info.get('path')
                        if not file_path:
                            # Debug: Log missing path for first event
                            if images_found == 0 and images_not_found == 0:
                                self.log(
                                    'debug_file_no_path',
                                    {'file_key': file_key, 'file_info_keys': list(file_info.keys())},
                                )
                            continue

                        file_path_obj = Path(file_path)
                        if not file_path_obj.exists():
                            # Debug: Log non-existent path for first event
                            if images_found == 0 and images_not_found == 0:
                                self.log(
                                    'debug_file_path_not_exists', {'file_key': file_key, 'file_path': str(file_path)}
                                )
                            continue

                        dest = files_dir / file_path_obj.name
                        if not dest.exists():
                            shutil.copy(file_path_obj, dest)

                        # Check file type
                        file_type = file_info.get('file_type')
                        is_image = file_type == 'image' or file_path_obj.suffix.lower() in (
                            '.jpg',
                            '.jpeg',
                            '.png',
                            '.gif',
                            '.bmp',
                            '.webp',
                        )
                        is_primary = file_info.get('is_primary', False)

                        if is_image and (is_primary or primary_image_dest is None):
                            primary_image_dest = dest

                        # Check if this is an annotation JSON file (data_meta_*)
                        if file_key.startswith('data_meta') and file_path_obj.suffix.lower() == '.json':
                            try:
                                annotation_json_content = json.loads(file_path_obj.read_text())
                            except (json.JSONDecodeError, OSError):
                                pass

                # Build DM v2 JSON structure from ground truth event and annotation JSON
                dm_json = self._build_dm_json(event, annotation_json_content)

                # Determine base name from primary image or event ID
                if primary_image_dest:
                    base_name = primary_image_dest.stem
                    images_found += 1
                else:
                    base_name = str(event_id)
                    images_not_found += 1

                # Save JSON with same stem as the image file
                json_path = json_dir / f'{base_name}.json'
                json_path.write_text(json.dumps(dm_json, indent=2, ensure_ascii=False))

                return True
            except Exception as e:
                self.log('download_event_error', {'event_id': event_id, 'error': str(e)})
                return False

        # Process events with thread pool
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            events_fetched = 0

            # Submit downloads as we iterate (reports fetch progress)
            for event in gt_events_gen:
                futures.append(executor.submit(download_event, event))
                events_fetched += 1
                # Report fetch progress (5-50% range)
                if total_count > 0:
                    fetch_progress = 5 + (events_fetched / total_count) * 45
                    if events_fetched % 10 == 0 or events_fetched == total_count:
                        self.set_progress(int(fetch_progress), 100, 'fetch')

            # Process completed downloads (50-100% range)
            for i, future in enumerate(as_completed(futures)):
                if future.result():
                    downloaded += 1
                # Report download progress (50-100% range)
                if total_count > 0:
                    download_progress = 50 + ((i + 1) / total_count) * 50
                    self.set_progress(int(download_progress), 100, 'download')

        self.log('download_stats', {'images_found': images_found, 'images_not_found': images_not_found})
        if images_not_found > 0:
            self.log_message(
                DatasetLogMessageCode.DATASET_DOWNLOAD_PARTIAL,
                downloaded=downloaded,
                missing=images_not_found,
            )
        return downloaded

    def _build_dm_json(self, event: dict, annotation_json: dict | None = None) -> dict[str, Any]:
        # TODO: Refactor format-specific logic (DMv1, DMv2) to synapse_sdk/plugins/datasets/converters/dm/
        """Build Datamaker v2 JSON from a ground truth event.

        Args:
            event: Ground truth event from API.
            annotation_json: Optional annotation JSON content from data_meta_* file.
                Contains 'annotations' and 'annotationsData' with actual annotations.

        Returns:
            DM v2 compatible JSON structure.
        """
        # Get annotations from the annotation JSON file (preferred)
        # The annotation JSON has structure:
        # {
        #   "annotations": {"image": [{"id": "...", "tool": "bounding_box",
        #       "classification": {"class": "car"}, ...}]},
        #   "annotationsData": {"image": [{"id": "...", "tool": "bounding_box",
        #       "coordinate": {"x": 0, "y": 0, "width": 100, "height": 100}}]}
        # }
        annotations_by_image: dict = {}
        annotations_data_by_image: dict = {}

        if annotation_json:
            annotations_by_image = annotation_json.get('annotations', {})
            annotations_data_by_image = annotation_json.get('annotationsData', {})

        # Fallback to event['data'] if no annotation JSON
        if not annotations_by_image:
            data = event.get('data', {})

            # Check if data is already in DMv2 'images' format (direct use)
            if 'images' in data and isinstance(data.get('images'), list):
                # Data is already in DMv2 format, return it directly
                return data

            annotations_by_image = data.get('annotations', {})
            annotations_data_by_image = data.get('annotationsData', {})
            if not annotations_by_image:
                annotations_by_image = event.get('annotations', {})
                annotations_data_by_image = event.get('annotationsData', {})

        dm_image: dict[str, list] = {
            'bounding_box': [],
            'polygon': [],
            'polyline': [],
            'keypoint': [],
            'classification': [],
            'relation': [],
            'group': [],
        }

        # Map tool names to DM annotation types
        tool_to_type = {
            'polygon': 'polygon',
            'bounding_box': 'bounding_box',
            'bbox': 'bounding_box',
            'polyline': 'polyline',
            'keypoint': 'keypoint',
            'point': 'keypoint',
            'classification': 'classification',
        }

        # Build lookup for annotation data by ID
        ann_data_lookup: dict[str, dict] = {}
        for image_key, ann_data_list in annotations_data_by_image.items():
            if isinstance(ann_data_list, list):
                for ann_data in ann_data_list:
                    if isinstance(ann_data, dict) and 'id' in ann_data:
                        ann_data_lookup[ann_data['id']] = ann_data

        # Process annotations for each image key (usually 'image')
        if isinstance(annotations_by_image, dict):
            for image_key, annotations in annotations_by_image.items():
                if not isinstance(annotations, list):
                    continue

                for ann in annotations:
                    if not isinstance(ann, dict):
                        continue

                    tool = ann.get('tool', '')
                    ann_type = tool_to_type.get(tool)
                    if not ann_type or ann_type not in dm_image:
                        continue

                    # Extract classification (can be nested: {class: 'car'} or flat: 'car')
                    classification = ann.get('classification', {})
                    if isinstance(classification, dict):
                        class_name = classification.get('class', '')
                    else:
                        class_name = str(classification) if classification else ''

                    # Get coordinate data from annotationsData lookup
                    ann_id = ann.get('id')
                    coordinate = {}
                    if ann_id and ann_id in ann_data_lookup:
                        ann_data = ann_data_lookup[ann_id]
                        coordinate = ann_data.get('coordinate', {})

                    # Build DM annotation with coordinate data
                    dm_ann: dict[str, Any] = {
                        'classification': class_name,
                    }

                    # Try to get data from annotation directly first (DM v2 format)
                    ann_data_field = ann.get('data')

                    # Add coordinate fields for bounding boxes
                    if ann_type == 'bounding_box':
                        if isinstance(ann_data_field, (list, tuple)) and len(ann_data_field) >= 4:
                            # Format: data = [x, y, w, h]
                            dm_ann['data'] = list(ann_data_field[:4])
                        elif coordinate:
                            # Fallback: coordinate dict with x, y, width, height
                            dm_ann['x'] = coordinate.get('x', 0)
                            dm_ann['y'] = coordinate.get('y', 0)
                            dm_ann['width'] = coordinate.get('width', 0)
                            dm_ann['height'] = coordinate.get('height', 0)
                    elif ann_type == 'polygon':
                        if isinstance(ann_data_field, list) and ann_data_field:
                            # Format: data = [[x1, y1], [x2, y2], ...]
                            dm_ann['data'] = ann_data_field
                        elif coordinate:
                            # Fallback: coordinate dict with points
                            dm_ann['points'] = coordinate.get('points', [])

                    dm_image[ann_type].append(dm_ann)

        # Build classification map from annotations
        classifications: dict[str, set[str]] = {}
        for ann_type, anns in dm_image.items():
            if anns:
                classifications[ann_type] = set()
                for ann in anns:
                    if ann.get('classification'):
                        classifications[ann_type].add(ann['classification'])

        return {
            'classification': {k: sorted(v) for k, v in classifications.items() if v},
            'images': [dm_image],
        }

    def convert(self) -> DatasetResult:
        """Convert dataset from one format to another.

        Converts the dataset at params.path to params.target_format.

        Returns:
            DatasetResult with converted path, format, config_path.

        Raises:
            ValueError: If path not provided.
        """
        if self.params.path is None:
            raise ValueError('path is required for convert operation')

        source_path = Path(self.params.path)
        if not source_path.exists():
            raise FileNotFoundError(f'Dataset path does not exist: {source_path}')

        # Parse formats
        target_format = DatasetFormat(self.params.target_format)
        dm_version = DMVersion.V1 if self.params.dm_version == 'v1' else DMVersion.V2

        # Determine source format
        source_format_str = self.params.source_format
        if source_format_str in ('dm_v1', 'dm_v2', 'dm'):
            src_format = DatasetFormat.DM_V1 if dm_version == DMVersion.V1 else DatasetFormat.DM_V2
        else:
            src_format = DatasetFormat(source_format_str)

        # Determine output directory
        if self.params.output_dir:
            output_dir = Path(self.params.output_dir)
        else:
            output_dir = source_path.parent / f'{source_path.name}_{target_format.value}'

        self.log(
            'convert_start',
            {
                'source_path': str(source_path),
                'source_format': src_format.value,
                'target_format': target_format.value,
                'is_categorized': self.params.is_categorized,
            },
        )
        self.log_message(DatasetLogMessageCode.DATASET_CONVERTING, source=src_format.value, target=target_format.value)

        # Get converter and run conversion
        converter = get_converter(
            source=src_format,
            target=target_format,
            root_dir=source_path,
            is_categorized=self.params.is_categorized,
            dm_version=dm_version,
        )

        converter.convert()
        converter.save_to_folder(output_dir)

        # Get config path from converter (each format defines its own config file)
        config_path = converter.get_config_path(output_dir)

        self.log(
            'convert_complete',
            {
                'output_path': str(output_dir),
                'config_path': str(config_path) if config_path else None,
            },
        )
        self.log_message(DatasetLogMessageCode.DATASET_CONVERSION_COMPLETED)

        return DatasetResult(
            path=output_dir,
            format=target_format.value,
            is_categorized=self.params.is_categorized,
            config_path=config_path,
            source_path=source_path,
        )


__all__ = ['DatasetAction', 'DatasetOperation', 'DatasetParams', 'DatasetResult']
