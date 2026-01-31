import os
from typing import IO, Any, Dict, List, Optional, Tuple

from PIL import Image

from synapse_sdk.utils.annotation_models.pascal import PascalAnnotation
from synapse_sdk.utils.converters.base import ToDMConverter


class PascalToDMConverter(ToDMConverter):
    """Convert Pascal VOC formatted datasets to DM format."""

    IMG_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp']

    def __init__(self, root_dir: str = None, is_categorized: bool = False, is_single_conversion: bool = False):
        super().__init__(root_dir, is_categorized, is_single_conversion)

    def convert(self):
        """Convert the Pascal VOC dataset to DM format."""
        if self.is_categorized:
            splits = self._validate_splits(['train', 'valid'], ['test'])
            all_split_data = {}
            for split, split_dir in splits.items():
                split_data = self._convert_pascal_split_to_dm(split_dir)
                all_split_data[split] = split_data
            self.converted_data = all_split_data
            return all_split_data
        else:
            split_data = self._convert_pascal_split_to_dm(self.root_dir)
            self.converted_data = split_data
            return split_data

    def _find_image_path(self, images_dir: str, filename: str) -> Optional[str]:
        """Find the image file in the specified directory."""
        img_path = os.path.join(images_dir, filename)
        if os.path.exists(img_path):
            return img_path
        base = os.path.splitext(filename)[0]
        for ext in self.IMG_EXTENSIONS:
            img_path = os.path.join(images_dir, base + ext)
            if os.path.exists(img_path):
                return img_path
        return None

    @staticmethod
    def _get_image_size(image_path: str) -> Tuple[int, int]:
        """Get the size of the image."""
        with Image.open(image_path) as img:
            return img.size

    def _parse_pascal_xml(self, xml_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """Parse a Pascal VOC XML file and return the filename and objects using PascalAnnotation model."""
        # Read XML file
        with open(xml_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # Use PascalAnnotation.from_xml() to parse
        pascal_annotation = PascalAnnotation.from_xml(xml_content)

        # Extract filename
        filename = pascal_annotation.filename

        # Convert PascalObject instances to DM format
        objects = []
        for obj in pascal_annotation.objects:
            xmin = obj.bndbox.xmin
            ymin = obj.bndbox.ymin
            xmax = obj.bndbox.xmax
            ymax = obj.bndbox.ymax
            width = xmax - xmin
            height = ymax - ymin
            objects.append({'classification': obj.name, 'data': [xmin, ymin, width, height]})

        return filename, objects

    def _convert_pascal_split_to_dm(self, split_dir: str) -> Dict[str, Any]:
        """Convert a single Pascal VOC split directory to DM format."""
        annotations_dir = None
        for candidate in ['Annotations', 'annotations']:
            candidate_path = os.path.join(split_dir, candidate)
            if os.path.isdir(candidate_path):
                annotations_dir = candidate_path
                break
        if annotations_dir is None:
            raise FileNotFoundError(
                f"No annotations directory found in {split_dir} (tried 'Annotations', 'annotations')."
            )
        images_dir = None
        for candidate in ['Images', 'images', 'JPEGImages']:
            candidate_path = os.path.join(split_dir, candidate)
            if os.path.isdir(candidate_path):
                images_dir = candidate_path
                break
        if images_dir is None:
            raise FileNotFoundError(
                f"No images directory found in {split_dir} (tried 'Images', 'images', 'JPEGImages')."
            )
        result = {}
        for xml_filename in os.listdir(annotations_dir):
            if not xml_filename.endswith('.xml'):
                continue
            xml_path = os.path.join(annotations_dir, xml_filename)
            try:
                filename, objects = self._parse_pascal_xml(xml_path)
                if filename is None:
                    print(f'[WARNING] No filename found in {xml_filename}, skipping.')
                    continue
                img_path = self._find_image_path(images_dir, filename)
                if img_path is None:
                    print(f'[WARNING] Image not found for {filename}, skipping.')
                    continue
                # Prepare DM annotation structure
                dm_img = {
                    'bounding_box': [],
                    'polygon': [],
                    'keypoint': [],
                    'relation': [],
                    'group': [],
                }
                for obj in objects:
                    dm_img['bounding_box'].append({
                        'id': self._generate_unique_id(),
                        'classification': obj['classification'],
                        'attrs': [],
                        'data': obj['data'],
                    })
                dm_json = {'images': [dm_img]}
                result[os.path.basename(img_path)] = (dm_json, img_path)
            except ValueError as e:
                print(f'[WARNING] Failed to parse {xml_filename}: {e}, skipping.')
                continue
            except Exception as e:
                print(f'[WARNING] Error processing {xml_filename}: {e}, skipping.')
                continue
        return result

    def convert_single_file(self, data: str | PascalAnnotation, original_file: IO) -> Dict[str, Any]:
        """Convert a single Pascal VOC XML data and corresponding image to DM format.

        Args:
            data: Pascal VOC XML content as string or PascalAnnotation Pydantic model
            original_file: File object for the corresponding original image

        Returns:
            Dictionary containing DM format data for the single file
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file is only available when is_single_conversion=True')

        # Get filename from original_file
        img_path = getattr(original_file, 'name', None)
        if not img_path:
            raise ValueError('original_file must have a "name" attribute representing its path or filename.')

        img_filename = os.path.basename(img_path)

        # Parse XML data from string using PascalAnnotation model
        try:
            if isinstance(data, str):
                pascal_annotation = PascalAnnotation.from_xml(data)
            else:
                pascal_annotation = data
        except Exception as e:
            raise ValueError(f'Failed to parse Pascal VOC XML data: {e}')

        # Extract objects from PascalAnnotation model
        objects = []
        for obj in pascal_annotation.objects:
            xmin = obj.bndbox.xmin
            ymin = obj.bndbox.ymin
            xmax = obj.bndbox.xmax
            ymax = obj.bndbox.ymax
            width = xmax - xmin
            height = ymax - ymin
            objects.append({'classification': obj.name, 'data': [xmin, ymin, width, height]})

        # Prepare DM annotation structure
        dm_img = {
            'bounding_box': [],
            'polygon': [],
            'keypoint': [],
            'relation': [],
            'group': [],
        }

        for obj in objects:
            dm_img['bounding_box'].append({
                'id': self._generate_unique_id(),
                'classification': obj['classification'],
                'attrs': [],
                'data': obj['data'],
            })

        dm_json = {'images': [dm_img]}
        return {
            'dm_json': dm_json,
            'image_path': img_path,
            'image_name': img_filename,
        }
