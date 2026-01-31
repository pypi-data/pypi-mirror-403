import datetime
import json
import os
import shutil
from glob import glob
from typing import IO, Any, Dict

from PIL import Image
from tqdm import tqdm

from synapse_sdk.utils.annotation_models.coco import (
    COCOAnnotation,
    COCOCategory,
    COCODataset,
    COCOImage,
    COCOInfo,
    COCOLicense,
)
from synapse_sdk.utils.converters.base import FromDMConverter


class FromDMToCOCOConverter(FromDMConverter):
    """Convert DM (Data Manager) format annotations to COCO format.
    Designed for easy future extensibility to handle various data types.
    """

    SUPPORTED_TYPES = {
        'img': ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff', '.webp'],
        # 'video': ['.mp4', '.avi', ...],
        # 'audio': ['.wav', '.mp3', ...]
    }

    def __init__(
        self,
        root_dir=None,
        info: COCOInfo | None = None,
        licenses: list[COCOLicense] | None = None,
        data_type='img',
        is_categorized=False,
        is_single_conversion=False,
    ):
        """Args:
        root_dir (str): Root directory containing data.
        info: COCO dataset info (COCOInfo model).
        licenses: List of COCO licenses (COCOLicense models).
        data_type (str): Which data type to use (default: 'img').
        is_categorized (bool): Whether to handle train, test, valid splits.
        is_single_conversion (bool): Whether to use single file conversion mode.
        """
        super().__init__(root_dir, is_categorized, is_single_conversion)
        self.data_type = data_type
        self.info = info or self._default_info()
        self.licenses = licenses or self._default_licenses()
        self.reset_state()

    # --- Helpers & State --- #

    def reset_state(self):
        self.images: list[COCOImage] = []
        self.annotations: list[COCOAnnotation] = []
        self.categories: list[COCOCategory] = []
        self.category_name_to_id: dict[str, int] = {}
        self.annotation_id = 1
        self.img_id = 1
        self.license_id = self.licenses[0].id if self.licenses else 1

    def _default_info(self) -> COCOInfo:
        now = datetime.datetime.now()
        return COCOInfo(
            description='Converted from DM format',
            url='',
            version=self.version,
            year=now.year,
            contributor='',
            date_created=now.strftime('%Y-%m-%d %H:%M:%S'),
        )

    @staticmethod
    def _default_licenses() -> list[COCOLicense]:
        return [COCOLicense(id=1, name='Unknown', url='')]

    @staticmethod
    def ensure_dir(path):
        os.makedirs(path, exist_ok=True)

    # --- File Pairing --- #

    def _collect_files(self):
        """Return {basename: file_path} for all supported files in this data type."""
        exts = self.SUPPORTED_TYPES[self.data_type]
        files = {}
        for ext in exts:
            for f in glob(os.path.join(self.original_file_dir, f'*{ext}')):
                base = os.path.splitext(os.path.basename(f))[0]
                files[base] = f
        return files

    def _find_json_file_pairs(self):
        """Return list of (json_path, data_path) pairs with matching basenames."""
        if not hasattr(self, 'json_dir') or not self.json_dir:
            self._set_directories()

        json_files = sorted(glob(os.path.join(self.json_dir, '*.json')))
        file_map = self._collect_files()
        result = []
        for json_file in json_files:
            file_name = os.path.splitext(os.path.basename(json_file))[0]
            if file_name in file_map:
                result.append((json_file, file_map[file_name]))
        return result

    # --- COCO Info Extraction --- #

    def _image_info(self, img_path) -> COCOImage:
        with Image.open(img_path) as im:
            width, height = im.size
        return COCOImage(
            id=self.img_id,
            file_name=os.path.basename(img_path),
            width=width,
            height=height,
            license=self.license_id,
        )

    @staticmethod
    def _poly_to_bbox(poly):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        x_min, y_min = min(xs), min(ys)
        x_max, y_max = max(xs), max(ys)
        return [x_min, y_min, x_max - x_min, y_max - y_min]

    @staticmethod
    def _poly_to_segmentation(poly):
        return [sum(poly, [])]

    # --- Category Management --- #

    def _get_or_create_category(self, name, keypoints=None) -> int:
        if name not in self.category_name_to_id:
            cid = len(self.category_name_to_id) + 1
            self.category_name_to_id[name] = cid
            cat = COCOCategory(
                id=cid,
                name=name,
                supercategory=name,
                keypoints=keypoints,
                skeleton=[] if keypoints else None,
            )
            self.categories.append(cat)
        return self.category_name_to_id[name]

    # --- Annotation Processing --- #

    def _process_polylines(self, anns):
        for poly in anns.get('polyline', []):
            cat_id = self._get_or_create_category(poly['classification'])
            seg = self._poly_to_segmentation(poly['data'])
            bbox = self._poly_to_bbox(poly['data'])
            self._add_annotation(cat_id, seg, bbox, area=bbox[2] * bbox[3])

    def _process_bboxes(self, anns):
        for box in anns.get('bounding_box', []):
            cat_id = self._get_or_create_category(box['classification'])
            bbox = box['data']
            self._add_annotation(cat_id, [], bbox, area=bbox[2] * bbox[3])

    def _process_keypoints(self, anns):
        if 'keypoint' not in anns:
            return
        keypoints = anns['keypoint']
        cat_id = self._get_or_create_category('keypoints', [kp['classification'] for kp in keypoints])
        kps, xs, ys = [], [], []
        for kp in keypoints:
            x, y = kp['data']
            kps += [x, y, 2]
            xs.append(x)
            ys.append(y)
        bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        ann = COCOAnnotation(
            id=self.annotation_id,
            image_id=self.img_id,
            category_id=cat_id,
            keypoints=kps,
            num_keypoints=len(keypoints),
            bbox=bbox,
            area=0,
            iscrowd=0,
        )
        self.annotations.append(ann)
        self.annotation_id += 1

    def _add_annotation(self, cat_id, segmentation, bbox, area):
        ann = COCOAnnotation(
            id=self.annotation_id,
            image_id=self.img_id,
            category_id=cat_id,
            segmentation=segmentation if segmentation else None,
            bbox=bbox,
            iscrowd=0,
            area=area,
        )
        self.annotations.append(ann)
        self.annotation_id += 1

    # --- Main Conversion Logic --- #

    def convert(self) -> COCODataset | dict[str, COCODataset]:
        """Convert DM format to COCO format, supporting dataset splits.

        Returns:
            COCODataset if not categorized, or dict[str, COCODataset] if categorized.
        """
        if self.is_categorized:
            required_splits = ['train', 'valid']
            optional_splits = ['test']
            split_dirs = self._validate_splits(required_splits, optional_splits)

            result = {}
            for split in split_dirs.keys():
                self._set_directories(split)
                self.reset_state()
                result[split] = self._convert_single_split()

            return result
        else:
            self._set_directories()
            return self._convert_single_split()

    def _convert_single_split(self) -> COCODataset:
        """Convert a single dataset split."""
        self.reset_state()

        pairs = self._find_json_file_pairs()
        if not pairs:
            raise FileNotFoundError(
                f'No matching JSON-{self.data_type} pairs found in {self.json_dir} and {self.original_file_dir}'
            )

        for json_path, data_path in tqdm(pairs, desc=f'Converting to COCO ({self.data_type})'):
            try:
                with open(json_path, encoding='utf-8') as jf:
                    data = json.load(jf)

                self.images.append(self._image_info(data_path))
                anns = data.get('images', [{}])[0]

                self._process_polylines(anns)
                self._process_bboxes(anns)
                self._process_keypoints(anns)
                self.img_id += 1

            except Exception as e:
                print(f'[ERROR] {json_path}: {e}')
                continue

        return COCODataset(
            info=self.info,
            licenses=self.licenses,
            images=self.images,
            annotations=self.annotations,
            categories=self.categories,
        )

    def save_to_folder(self, output_dir):
        """Save the converted COCO data and original files to the specified folder."""
        super().save_to_folder(output_dir)

        if self.is_categorized:
            for split, coco_data in self.converted_data.items():
                split_output_dir = os.path.join(output_dir, split)
                self._save_annotations_and_images(
                    coco_data, split_output_dir, os.path.join(self.root_dir, split, 'original_files')
                )
        else:
            self._save_annotations_and_images(
                self.converted_data, output_dir, os.path.join(self.root_dir, 'original_files')
            )

    def _save_annotations_and_images(self, coco_data: COCODataset, output_dir, original_file_dir):
        """Helper method to save annotations and copy original images."""
        self.ensure_dir(output_dir)

        # Save annotations using Pydantic model's to_json method
        json_path = os.path.join(output_dir, 'annotations.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(coco_data.to_json(indent=4))
        print(f'COCO annotations saved to {json_path}')

        # Copy original images
        for image in coco_data.images:
            src_path = os.path.join(original_file_dir, image.file_name)
            dst_path = os.path.join(output_dir, image.file_name)
            if os.path.exists(src_path):
                shutil.copy(src_path, dst_path)
            else:
                print(f'[WARNING] Image not found: {src_path}')

    def convert_single_file(self, data: Dict[str, Any], original_file: IO, file_name: str) -> COCODataset:
        """Convert a single DM data dict and corresponding image file object to COCO format.

        Args:
            data: DM format data dictionary (JSON content)
            original_file: File object for the corresponding original image
            file_name: Name of the image file

        Returns:
            COCODataset containing COCO format data for the single file
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file is only available when is_single_conversion=True')

        self.reset_state()

        # Process the image file
        with Image.open(original_file) as im:
            width, height = im.size

        image_info = COCOImage(
            id=self.img_id,
            file_name=file_name,
            width=width,
            height=height,
            license=self.license_id,
        )
        self.images.append(image_info)

        # Process annotations from the first (and only) image in data
        if 'images' in data and len(data['images']) > 0:
            anns = data['images'][0]
            self._process_polylines(anns)
            self._process_bboxes(anns)
            self._process_keypoints(anns)

        return COCODataset(
            info=self.info,
            licenses=self.licenses,
            images=self.images,
            annotations=self.annotations,
            categories=self.categories,
        )
