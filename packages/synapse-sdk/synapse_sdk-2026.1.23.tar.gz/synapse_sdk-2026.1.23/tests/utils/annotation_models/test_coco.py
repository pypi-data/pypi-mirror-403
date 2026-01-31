"""Tests for COCO annotation models."""

from __future__ import annotations

import json

import pytest

from synapse_sdk.utils.annotation_models.coco import (
    COCOAnnotation,
    COCOCategory,
    COCODataset,
    COCOImage,
    COCOInfo,
    COCOLicense,
)


class TestCOCOInfo:
    """Tests for COCOInfo model."""

    def test_create_info(self):
        """Test creating COCO info."""
        info = COCOInfo(
            description='My Dataset',
            url='https://example.com',
            version='1.0',
            year=2024,
            contributor='Test User',
            date_created='2024-01-01',
        )
        assert info.description == 'My Dataset'
        assert info.year == 2024

    def test_default_values(self):
        """Test default info values."""
        info = COCOInfo()
        assert info.description == ''
        assert info.url == ''
        assert info.year is None


class TestCOCOLicense:
    """Tests for COCOLicense model."""

    def test_create_license(self):
        """Test creating a COCO license."""
        license = COCOLicense(id=1, name='MIT License', url='https://opensource.org/licenses/MIT')
        assert license.id == 1
        assert license.name == 'MIT License'


class TestCOCOImage:
    """Tests for COCOImage model."""

    def test_create_image(self):
        """Test creating a COCO image."""
        img = COCOImage(
            id=1,
            file_name='image001.jpg',
            width=640,
            height=480,
        )
        assert img.id == 1
        assert img.file_name == 'image001.jpg'
        assert img.width == 640
        assert img.height == 480

    def test_image_with_optional_fields(self):
        """Test image with optional fields."""
        img = COCOImage(
            id=2,
            file_name='image002.jpg',
            width=1920,
            height=1080,
            date_captured='2024-01-01 12:00:00',
            license=1,
            coco_url='http://images.cocodataset.org/val2017/000000002.jpg',
        )
        assert img.date_captured == '2024-01-01 12:00:00'
        assert img.license == 1
        assert img.coco_url is not None


class TestCOCOCategory:
    """Tests for COCOCategory model."""

    def test_create_category(self):
        """Test creating a COCO category."""
        cat = COCOCategory(id=1, name='person', supercategory='human')
        assert cat.id == 1
        assert cat.name == 'person'
        assert cat.supercategory == 'human'

    def test_default_supercategory(self):
        """Test default supercategory value."""
        cat = COCOCategory(id=2, name='car')
        assert cat.supercategory == ''


class TestCOCOAnnotation:
    """Tests for COCOAnnotation model."""

    def test_create_annotation(self):
        """Test creating a COCO annotation."""
        ann = COCOAnnotation(
            id=1,
            image_id=1,
            category_id=1,
            bbox=[100.0, 150.0, 50.0, 80.0],
            area=4000.0,
        )
        assert ann.id == 1
        assert ann.image_id == 1
        assert ann.category_id == 1
        assert len(ann.bbox) == 4

    def test_annotation_with_segmentation(self):
        """Test annotation with segmentation."""
        ann = COCOAnnotation(
            id=2,
            image_id=1,
            category_id=1,
            bbox=[100.0, 100.0, 50.0, 50.0],
            segmentation=[[100.0, 100.0, 150.0, 100.0, 150.0, 150.0, 100.0, 150.0]],
            area=2500.0,
        )
        assert ann.segmentation is not None
        assert len(ann.segmentation) == 1

    def test_iscrowd_default(self):
        """Test iscrowd default value."""
        ann = COCOAnnotation(
            id=3,
            image_id=1,
            category_id=1,
            bbox=[10, 20, 30, 40],
            area=1200,
        )
        assert ann.iscrowd == 0

    def test_bbox_validation(self):
        """Test bbox length validation."""
        with pytest.raises(ValueError):
            COCOAnnotation(
                id=4,
                image_id=1,
                category_id=1,
                bbox=[10, 20, 30],  # Invalid: only 3 values
                area=600,
            )


class TestCOCODataset:
    """Tests for COCODataset model."""

    def test_create_empty_dataset(self):
        """Test creating an empty COCO dataset."""
        dataset = COCODataset()
        assert isinstance(dataset.info, COCOInfo)
        assert dataset.licenses == []
        assert dataset.images == []
        assert dataset.annotations == []
        assert dataset.categories == []

    def test_create_dataset_with_data(self):
        """Test creating a dataset with data."""
        dataset = COCODataset(
            info=COCOInfo(description='Test Dataset'),
            categories=[COCOCategory(id=1, name='person')],
            images=[COCOImage(id=1, file_name='img.jpg', width=640, height=480)],
            annotations=[
                COCOAnnotation(
                    id=1,
                    image_id=1,
                    category_id=1,
                    bbox=[100, 100, 50, 50],
                    area=2500,
                )
            ],
        )
        assert len(dataset.categories) == 1
        assert len(dataset.images) == 1
        assert len(dataset.annotations) == 1

    def test_to_json(self):
        """Test serializing dataset to JSON."""
        dataset = COCODataset(
            categories=[COCOCategory(id=1, name='car')],
            images=[COCOImage(id=1, file_name='test.jpg', width=640, height=480)],
            annotations=[COCOAnnotation(id=1, image_id=1, category_id=1, bbox=[10, 20, 30, 40], area=1200)],
        )
        json_str = dataset.to_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert 'categories' in data
        assert 'images' in data
        assert 'annotations' in data

    def test_from_json(self):
        """Test deserializing dataset from JSON."""
        json_data = {
            'info': {'description': 'Test'},
            'licenses': [],
            'images': [{'id': 1, 'file_name': 'test.jpg', 'width': 640, 'height': 480}],
            'annotations': [{'id': 1, 'image_id': 1, 'category_id': 1, 'bbox': [10, 20, 30, 40], 'area': 1200}],
            'categories': [{'id': 1, 'name': 'person', 'supercategory': ''}],
        }
        json_str = json.dumps(json_data)
        dataset = COCODataset.from_json(json_str)

        assert len(dataset.images) == 1
        assert len(dataset.annotations) == 1
        assert dataset.images[0].file_name == 'test.jpg'

    def test_to_dict(self):
        """Test converting dataset to dictionary."""
        dataset = COCODataset(
            categories=[COCOCategory(id=1, name='person')],
        )
        data = dataset.to_dict()
        assert isinstance(data, dict)
        assert 'categories' in data
        assert len(data['categories']) == 1

    def test_from_dict(self):
        """Test creating dataset from dictionary."""
        data = {
            'info': {},
            'licenses': [],
            'images': [],
            'annotations': [],
            'categories': [{'id': 1, 'name': 'car', 'supercategory': 'vehicle'}],
        }
        dataset = COCODataset.from_dict(data)
        assert len(dataset.categories) == 1
        assert dataset.categories[0].name == 'car'

    def test_get_annotations_by_image_id(self):
        """Test getting annotations for a specific image."""
        dataset = COCODataset(
            images=[
                COCOImage(id=1, file_name='img1.jpg', width=640, height=480),
                COCOImage(id=2, file_name='img2.jpg', width=640, height=480),
            ],
            annotations=[
                COCOAnnotation(id=1, image_id=1, category_id=1, bbox=[10, 20, 30, 40], area=1200),
                COCOAnnotation(id=2, image_id=1, category_id=1, bbox=[50, 60, 70, 80], area=5600),
                COCOAnnotation(id=3, image_id=2, category_id=1, bbox=[90, 100, 110, 120], area=13200),
            ],
            categories=[COCOCategory(id=1, name='person')],
        )

        anns_img1 = dataset.get_annotations_by_image_id(1)
        assert len(anns_img1) == 2

        anns_img2 = dataset.get_annotations_by_image_id(2)
        assert len(anns_img2) == 1

    def test_get_category_by_id(self):
        """Test getting category by ID."""
        dataset = COCODataset(
            categories=[
                COCOCategory(id=1, name='person'),
                COCOCategory(id=2, name='car'),
            ]
        )

        cat = dataset.get_category_by_id(1)
        assert cat is not None
        assert cat.name == 'person'

        cat_none = dataset.get_category_by_id(999)
        assert cat_none is None

    def test_get_image_by_id(self):
        """Test getting image by ID."""
        dataset = COCODataset(
            images=[
                COCOImage(id=1, file_name='img1.jpg', width=640, height=480),
                COCOImage(id=2, file_name='img2.jpg', width=1920, height=1080),
            ]
        )

        img = dataset.get_image_by_id(1)
        assert img is not None
        assert img.file_name == 'img1.jpg'

        img_none = dataset.get_image_by_id(999)
        assert img_none is None
