"""Tests for YOLO annotation models."""

from __future__ import annotations

from pathlib import Path

import pytest

from synapse_sdk.utils.annotation_models.yolo import (
    YOLOAnnotation,
    YOLODataset,
    YOLODatasetConfig,
    YOLOImage,
)


class TestYOLOAnnotation:
    """Tests for YOLOAnnotation model."""

    def test_create_annotation(self):
        """Test creating a YOLO annotation."""
        ann = YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3)
        assert ann.class_id == 0
        assert ann.cx == 0.5
        assert ann.cy == 0.5
        assert ann.w == 0.2
        assert ann.h == 0.3

    def test_to_line(self):
        """Test converting annotation to YOLO line format."""
        ann = YOLOAnnotation(class_id=1, cx=0.5, cy=0.6, w=0.3, h=0.4)
        line = ann.to_line()
        assert line == '1 0.500000 0.600000 0.300000 0.400000'

    def test_from_line(self):
        """Test parsing annotation from YOLO line."""
        line = '2 0.25 0.75 0.1 0.2'
        ann = YOLOAnnotation.from_line(line)
        assert ann.class_id == 2
        assert ann.cx == 0.25
        assert ann.cy == 0.75
        assert ann.w == 0.1
        assert ann.h == 0.2

    def test_to_absolute(self):
        """Test converting to absolute pixel coordinates."""
        ann = YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.4)
        x, y, w, h = ann.to_absolute(width=1000, height=800)

        # cx=0.5, w=0.2 -> abs_w=200, abs_x=500-100=400
        # cy=0.5, h=0.4 -> abs_h=320, abs_y=400-160=240
        assert x == 400.0
        assert y == 240.0
        assert w == 200.0
        assert h == 320.0

    def test_from_absolute(self):
        """Test creating from absolute pixel coordinates."""
        ann = YOLOAnnotation.from_absolute(
            class_id=1,
            x=100.0,
            y=150.0,
            w=50.0,
            h=80.0,
            img_width=640,
            img_height=480,
        )

        # cx = (100 + 50/2) / 640 = 125 / 640 = 0.1953125
        # cy = (150 + 80/2) / 480 = 190 / 480 = 0.395833...
        # w = 50 / 640 = 0.078125
        # h = 80 / 480 = 0.166666...
        assert ann.class_id == 1
        assert abs(ann.cx - 0.1953125) < 0.0001
        assert abs(ann.cy - 0.395833) < 0.0001
        assert abs(ann.w - 0.078125) < 0.0001
        assert abs(ann.h - 0.166667) < 0.0001

    def test_validation_class_id(self):
        """Test validation of class_id."""
        with pytest.raises(ValueError):
            YOLOAnnotation(class_id=-1, cx=0.5, cy=0.5, w=0.2, h=0.3)

    def test_validation_normalized_coords(self):
        """Test validation of normalized coordinates."""
        with pytest.raises(ValueError):
            YOLOAnnotation(class_id=0, cx=1.5, cy=0.5, w=0.2, h=0.3)  # cx > 1


class TestYOLODatasetConfig:
    """Tests for YOLODatasetConfig model."""

    def test_create_config(self):
        """Test creating a YOLO dataset config."""
        config = YOLODatasetConfig(
            path='/data/mydata',
            train='train/images',
            val='valid/images',
            nc=3,
            names=['person', 'car', 'bicycle'],
        )
        assert config.path == '/data/mydata'
        assert config.nc == 3
        assert len(config.names) == 3

    def test_default_values(self):
        """Test default config values."""
        config = YOLODatasetConfig(nc=2, names=['cat', 'dog'])
        assert config.path == '.'
        assert config.train == 'train/images'
        assert config.val == 'valid/images'
        assert config.test is None

    def test_to_yaml(self):
        """Test converting config to YAML string."""
        config = YOLODatasetConfig(
            path='.',
            train='train/images',
            val='valid/images',
            test='test/images',
            nc=2,
            names=['cat', 'dog'],
        )
        yaml_str = config.to_yaml()

        assert 'path: .' in yaml_str
        assert 'train: train/images' in yaml_str
        assert 'val: valid/images' in yaml_str
        assert 'test: test/images' in yaml_str
        assert 'nc: 2' in yaml_str
        assert "names: ['cat', 'dog']" in yaml_str


class TestYOLOImage:
    """Tests for YOLOImage model."""

    def test_create_image(self):
        """Test creating a YOLO image."""
        img = YOLOImage(
            image_path=Path('/data/image001.jpg'),
            annotations=[YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3)],
        )
        assert img.image_path == Path('/data/image001.jpg')
        assert len(img.annotations) == 1

    def test_to_label_content(self):
        """Test converting annotations to label file content."""
        img = YOLOImage(
            image_path=Path('/data/test.jpg'),
            annotations=[
                YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3),
                YOLOAnnotation(class_id=1, cx=0.3, cy=0.7, w=0.1, h=0.2),
            ],
        )
        content = img.to_label_content()
        lines = content.split('\n')
        assert len(lines) == 2
        assert lines[0].startswith('0 0.500000')
        assert lines[1].startswith('1 0.300000')


class TestYOLODataset:
    """Tests for YOLODataset model."""

    def test_create_dataset(self):
        """Test creating a YOLO dataset."""
        config = YOLODatasetConfig(nc=2, names=['cat', 'dog'])
        dataset = YOLODataset(
            config=config,
            train_images=[],
            val_images=[],
        )
        assert dataset.config.nc == 2
        assert len(dataset.train_images) == 0
        assert len(dataset.val_images) == 0
        assert len(dataset.test_images) == 0

    def test_dataset_serialization(self):
        """Test dataset serialization."""
        config = YOLODatasetConfig(nc=1, names=['person'])
        img = YOLOImage(
            image_path=Path('/data/img.jpg'),
            annotations=[YOLOAnnotation(class_id=0, cx=0.5, cy=0.5, w=0.2, h=0.3)],
        )
        dataset = YOLODataset(config=config, train_images=[img])

        data = dataset.model_dump()
        assert 'config' in data
        assert 'train_images' in data
        assert len(data['train_images']) == 1
