"""Convert Datamaker format to ImageFolder format.

ImageFolder format is the standard PyTorch image classification format:
- split/class_name/image.jpg

Supports:
- DMv1 and DMv2 schemas
- Classification annotations only
- Categorized (train/valid/test splits) and non-categorized datasets
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from synapse_sdk.utils.annotation_models.dm import DMVersion
from synapse_sdk.utils.converters.base import DatasetFormat, FromDMConverter


class FromDMToImageFolderConverter(FromDMConverter):
    """Convert Datamaker dataset format to ImageFolder format.

    ImageFolder is the standard format for PyTorch image classification:
    - output_dir/split/class_name/image.jpg

    Works with both DMv1 and DMv2 schemas containing classification annotations.

    Example:
        >>> converter = FromDMToImageFolderConverter(
        ...     root_dir='/data/dm_dataset',
        ...     is_categorized=True,
        ...     dm_version=DMVersion.V2,
        ... )
        >>> converter.convert()
        >>> converter.save_to_folder('/data/imagefolder_output')
    """

    target_format = DatasetFormat.IMAGEFOLDER

    def get_config_path(self, output_dir: str | Path) -> Path | None:
        """Return classes.txt path if exists."""
        config_path = Path(output_dir) / 'classes.txt'
        return config_path if config_path.exists() else None

    def __init__(
        self,
        root_dir: str | Path | None = None,
        is_categorized: bool = False,
        is_single_conversion: bool = False,
        dm_version: DMVersion = DMVersion.V2,
    ) -> None:
        """Initialize converter.

        Args:
            root_dir: Root directory containing DM data.
            is_categorized: Whether dataset has train/valid/test splits.
            is_single_conversion: Whether converting single files only.
            dm_version: Datamaker schema version (V1 or V2).
        """
        super().__init__(root_dir, is_categorized, is_single_conversion, dm_version)

    @staticmethod
    def get_all_classes(list_of_dirs: list[Path], dm_version: DMVersion = DMVersion.V2) -> list[str]:
        """Collect all unique class names from directories.

        Args:
            list_of_dirs: List of directories to scan.
            dm_version: Datamaker schema version.

        Returns:
            Sorted list of unique class names (sorted for ImageFolder compatibility).
        """
        classes: set[str] = set()

        for d in list_of_dirs:
            if not d or not d.is_dir():
                continue

            json_dir = d / 'json' if (d / 'json').is_dir() else d

            for jfile in json_dir.glob('*.json'):
                with open(jfile, encoding='utf-8') as f:
                    data = json.load(f)

                if dm_version == DMVersion.V2:
                    for img_ann in data.get('images', []):
                        for ann in img_ann.get('classification', []):
                            if 'classification' in ann:
                                classes.add(ann['classification'])
                else:
                    # V1: annotations keyed by asset
                    for anns in data.get('annotations', {}).values():
                        for ann in anns:
                            classification = ann.get('classification', {})
                            if isinstance(classification, dict):
                                class_val = classification.get('class')
                                if class_val:
                                    classes.add(class_val)

        # Sort alphabetically for ImageFolder compatibility
        return sorted(classes)

    def _get_classification_from_dm_json(self, data: dict[str, Any]) -> str | None:
        """Extract classification label from DM JSON data.

        Args:
            data: DM format JSON data.

        Returns:
            Classification label or None if not found.
        """
        if self.dm_version == DMVersion.V2:
            if 'images' in data and data['images']:
                img_ann = data['images'][0]
                classifications = img_ann.get('classification', [])
                if classifications and isinstance(classifications, list):
                    first_classification = classifications[0]
                    if isinstance(first_classification, dict):
                        return first_classification.get('classification')
        else:
            # V1: annotations keyed by asset
            for anns in data.get('annotations', {}).values():
                if anns and isinstance(anns, list):
                    for ann in anns:
                        classification = ann.get('classification', {})
                        if isinstance(classification, dict):
                            class_val = classification.get('class')
                            if class_val:
                                return class_val
        return None

    def _convert_split_dir(self, split_dir: Path, split_name: str) -> list[dict[str, Any]]:
        """Convert one split folder to ImageFolder format entries."""
        json_dir = split_dir / 'json'
        img_dir = split_dir / 'original_files'
        entries = []

        json_files = list(json_dir.glob('*.json')) if json_dir.exists() else []
        img_files = list(img_dir.glob('*')) if img_dir.exists() else []

        print(f'[{split_name}] Found {len(json_files)} JSON files in {json_dir}')
        print(f'[{split_name}] Found {len(img_files)} files in {img_dir}')

        matched = 0
        unmatched = 0
        no_classification = 0

        for jfile in json_files:
            base = jfile.stem

            # Find corresponding image
            img_path = self.find_image_for_label(base, img_dir)
            if not img_path:
                unmatched += 1
                if unmatched <= 3:
                    print(f'[{split_name}] Image for {base} not found, skipping.')
                continue

            with open(jfile, encoding='utf-8') as f:
                data = json.load(f)

            classification = self._get_classification_from_dm_json(data)
            if not classification:
                no_classification += 1
                if no_classification <= 3:
                    print(f'[{split_name}] No classification found for {base}, skipping.')
                continue

            matched += 1
            entries.append({
                'img_path': img_path,
                'img_name': img_path.name,
                'classification': classification,
            })

        print(f'[{split_name}] Matched: {matched}, Unmatched: {unmatched}, No class: {no_classification}')
        return entries

    def _convert_root_dir(self) -> list[dict[str, Any]]:
        """Convert non-categorized dataset to ImageFolder format."""
        return self._convert_split_dir(self.root_dir, 'root')

    def convert(self) -> dict[str, list[dict[str, Any]]] | list[dict[str, Any]]:
        """Convert DM format to ImageFolder format.

        Returns:
            If categorized: dict mapping split names to list of entries.
            If not categorized: list of entries.
            Each entry contains img_path, img_name, classification.
        """
        if self.is_categorized:
            splits = self._validate_splits(['train', 'valid'], ['test', 'validation'])
            self.class_names = self.get_all_classes(list(splits.values()), self.dm_version)
            self.class_map = {name: idx for idx, name in enumerate(self.class_names)}

            result = {}
            for split, split_dir in splits.items():
                result[split] = self._convert_split_dir(split_dir, split)
            self.converted_data = result
        else:
            self._validate_splits([], [])
            self.class_names = self.get_all_classes([self.root_dir], self.dm_version)
            self.class_map = {name: idx for idx, name in enumerate(self.class_names)}

            result = self._convert_root_dir()
            self.converted_data = result

        print(f'[convert] Found {len(self.class_names)} classes: {self.class_names}')
        return self.converted_data

    def save_to_folder(self, output_dir: str | Path | None = None) -> None:
        """Save converted ImageFolder data to folder.

        Creates structure: output_dir/split/class_name/image.jpg

        Args:
            output_dir: Output directory. Defaults to root_dir.
        """
        output_dir = Path(output_dir) if output_dir else self.root_dir
        self.ensure_dir(output_dir)

        if self.converted_data is None:
            self.converted_data = self.convert()

        print(f'[save_to_folder] output_dir: {output_dir}')
        print(f'[save_to_folder] is_categorized: {self.is_categorized}')

        # Ensure all class directories exist in all splits
        if self.is_categorized:
            for split, entries in self.converted_data.items():
                split_dir = output_dir / split

                # Create class directories
                for class_name in self.class_names:
                    self.ensure_dir(split_dir / class_name)

                # Copy images to class directories
                for entry in entries:
                    class_dir = split_dir / entry['classification']
                    shutil.copy(entry['img_path'], class_dir / entry['img_name'])

                print(f'[save_to_folder] {split}: {len(entries)} images saved')
        else:
            # Non-categorized: save to root directly
            for class_name in self.class_names:
                self.ensure_dir(output_dir / class_name)

            for entry in self.converted_data:
                class_dir = output_dir / entry['classification']
                shutil.copy(entry['img_path'], class_dir / entry['img_name'])

            print(f'[save_to_folder] Saved {len(self.converted_data)} images')

        # Write classes.txt for reference
        (output_dir / 'classes.txt').write_text('\n'.join(self.class_names) + '\n')
        print(f'[save_to_folder] Classes: {self.class_names}')


__all__ = ['FromDMToImageFolderConverter']
