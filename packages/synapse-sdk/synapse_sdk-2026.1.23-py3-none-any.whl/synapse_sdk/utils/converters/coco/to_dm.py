import os
from typing import IO, Any, Dict

from synapse_sdk.utils.annotation_models.coco import COCODataset
from synapse_sdk.utils.converters.base import ToDMConverter


class COCOToDMConverter(ToDMConverter):
    """Convert COCO format annotations to DM (Data Manager) format."""

    def __init__(self, root_dir: str = None, is_categorized: bool = False, is_single_conversion: bool = False):
        super().__init__(root_dir, is_categorized, is_single_conversion)

    def convert(self):
        if self.is_categorized:
            splits = self._validate_splits(['train', 'valid'], ['test'])
            all_split_data = {}
            for split, split_dir in splits.items():
                annotation_path = os.path.join(split_dir, 'annotations.json')
                if not os.path.exists(annotation_path):
                    raise FileNotFoundError(f'annotations.json not found in {split_dir}')
                with open(annotation_path, 'r', encoding='utf-8') as f:
                    coco_data = COCODataset.from_json(f.read())
                split_data = self._convert_coco_ann_to_dm(coco_data, split_dir)
                all_split_data[split] = split_data
            self.converted_data = all_split_data
            return all_split_data
        else:
            annotation_path = os.path.join(self.root_dir, 'annotations.json')
            if not os.path.exists(annotation_path):
                raise FileNotFoundError(f'annotations.json not found in {self.root_dir}')
            with open(annotation_path, 'r', encoding='utf-8') as f:
                coco_data = COCODataset.from_json(f.read())
            converted_data = self._convert_coco_ann_to_dm(coco_data, self.root_dir)
            self.converted_data = converted_data
            return converted_data

    def _convert_coco_ann_to_dm(self, coco_data: COCODataset, base_dir):
        """Convert COCO annotations to DM format.

        Args:
            coco_data: COCODataset Pydantic model
            base_dir: Base directory containing images

        Returns:
            Dictionary mapping image filenames to (dm_json, img_path) tuples
        """
        # COCO format is primarily for images, so we process as image data
        return self._process_image_data(coco_data, base_dir)

    def _process_image_data(self, coco_data: COCODataset, img_base_dir):
        """Process COCO image data and convert to DM format.

        Args:
            coco_data: COCODataset Pydantic model
            img_base_dir: Base directory containing images

        Returns:
            Dictionary mapping image filenames to (dm_json, img_path) tuples
        """
        # Build category map
        cat_map = {cat.id: cat for cat in coco_data.categories}

        # Build image_id -> annotation list mapping using helper method
        ann_by_img_id = {}
        for ann in coco_data.annotations:
            ann_by_img_id.setdefault(ann.image_id, []).append(ann)

        result = {}
        for img in coco_data.images:
            img_id = img.id
            img_filename = img.file_name
            img_path = os.path.join(img_base_dir, img_filename)
            anns = ann_by_img_id.get(img_id, [])

            # DM image structure
            dm_img = {
                'bounding_box': [],
                'keypoint': [],
                'relation': [],
                'group': [],
            }

            # Handle bounding_box
            bbox_ids = []
            for ann in anns:
                cat = cat_map.get(ann.category_id)
                if ann.bbox:
                    bbox_id = self._generate_unique_id()
                    bbox_ids.append(bbox_id)
                    dm_img['bounding_box'].append({
                        'id': bbox_id,
                        'classification': cat.name if cat else str(ann.category_id),
                        'attrs': [],  # COCO doesn't have attrs in standard format
                        'data': list(ann.bbox),
                    })

            # Handle keypoints
            for ann in anns:
                cat = cat_map.get(ann.category_id)
                if ann.keypoints:
                    kp_names = cat.keypoints if cat and cat.keypoints else []
                    kps = ann.keypoints
                    keypoint_ids = []
                    for idx in range(min(len(kps) // 3, len(kp_names) if kp_names else len(kps) // 3)):
                        x, y, v = kps[idx * 3 : idx * 3 + 3]
                        kp_id = self._generate_unique_id()
                        keypoint_ids.append(kp_id)
                        dm_img['keypoint'].append({
                            'id': kp_id,
                            'classification': kp_names[idx] if idx < len(kp_names) else f'keypoint_{idx}',
                            'attrs': [],
                            'data': [x, y],
                        })
                    group_ids = bbox_ids + keypoint_ids
                    if group_ids:
                        dm_img['group'].append({
                            'id': self._generate_unique_id(),
                            'classification': cat.name if cat else str(ann.category_id),
                            'attrs': [],
                            'data': group_ids,
                        })

            dm_json = {'images': [dm_img]}
            result[img_filename] = (dm_json, img_path)
        return result

    def convert_single_file(
        self, data: COCODataset | Dict[str, Any], original_file: IO, original_image_name: str
    ) -> Dict[str, Any]:
        """Convert a single COCO annotation data and corresponding image to DM format.

        Args:
            data: COCODataset Pydantic model or COCO format data dictionary (JSON content)
            original_file: File object for the corresponding original image
            original_image_name: Original image name

        Returns:
            Dictionary containing DM format data for the single file
        """
        if not self.is_single_conversion:
            raise RuntimeError('convert_single_file is only available when is_single_conversion=True')

        # Support both COCODataset model and dict for backward compatibility
        if isinstance(data, dict):
            data = COCODataset.model_validate(data)

        if not data.images:
            raise ValueError('No images found in COCO data')

        # Get file name from original_file
        img_path = getattr(original_file, 'name', None)
        if not img_path:
            raise ValueError('original_file must have a "name" attribute representing its path or filename.')
        img_basename = os.path.basename(img_path)

        # Find the matching image info in COCO images by comparing file name
        matched_img = None
        for img in data.images:
            if os.path.basename(img.file_name) == original_image_name:
                matched_img = img
                break

        if not matched_img:
            raise ValueError(f'No matching image found in COCO data for file: {img_basename}')

        img_id = matched_img.id
        cat_map = {cat.id: cat for cat in data.categories}
        anns = [ann for ann in data.annotations if ann.image_id == img_id]

        dm_img = {
            'bounding_box': [],
            'keypoint': [],
            'relation': [],
            'group': [],
        }

        bbox_ids = []
        for ann in anns:
            cat = cat_map.get(ann.category_id)
            if ann.bbox:
                bbox_id = self._generate_unique_id()
                bbox_ids.append(bbox_id)
                dm_img['bounding_box'].append({
                    'id': bbox_id,
                    'classification': cat.name if cat else str(ann.category_id),
                    'attrs': [],  # COCO doesn't have attrs in standard format
                    'data': list(ann.bbox),
                })

        for ann in anns:
            cat = cat_map.get(ann.category_id)
            if ann.keypoints:
                kp_names = cat.keypoints if cat and cat.keypoints else []
                kps = ann.keypoints
                keypoint_ids = []
                for idx in range(min(len(kps) // 3, len(kp_names) if kp_names else len(kps) // 3)):
                    x, y, _ = kps[idx * 3 : idx * 3 + 3]
                    kp_id = self._generate_unique_id()
                    keypoint_ids.append(kp_id)
                    dm_img['keypoint'].append({
                        'id': kp_id,
                        'classification': kp_names[idx] if idx < len(kp_names) else f'keypoint_{idx}',
                        'attrs': [],
                        'data': [x, y],
                    })
                group_ids = bbox_ids + keypoint_ids
                if group_ids:
                    dm_img['group'].append({
                        'id': self._generate_unique_id(),
                        'classification': cat.name if cat else str(ann.category_id),
                        'attrs': [],
                        'data': group_ids,
                    })

        dm_json = {'images': [dm_img]}
        return {
            'dm_json': dm_json,
            'image_path': img_path,
            'image_name': img_basename,
        }
