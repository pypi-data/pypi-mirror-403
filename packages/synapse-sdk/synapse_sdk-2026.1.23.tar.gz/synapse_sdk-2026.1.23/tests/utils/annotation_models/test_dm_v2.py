"""Tests for DataMaker V2 models."""

from __future__ import annotations

import pytest

from synapse_sdk.utils.annotation_models.dm import (
    DMAttribute,
    DMv2BoundingBox,
    DMv2Dataset,
    DMv2Group,
    DMv2ImageItem,
    DMv2Keypoint,
    DMv2Polygon,
    DMv2Relation,
)


class TestDMv2BoundingBox:
    """Tests for DMv2BoundingBox model."""

    def test_create_bbox(self):
        """Test creating a bounding box."""
        bbox = DMv2BoundingBox(
            id='bbox_001',
            classification='person',
            data=(100.0, 150.0, 50.0, 80.0),
        )
        assert bbox.id == 'bbox_001'
        assert bbox.classification == 'person'
        assert bbox.data == (100.0, 150.0, 50.0, 80.0)
        assert bbox.attrs == []

    def test_bbox_with_attributes(self):
        """Test bounding box with attributes."""
        bbox = DMv2BoundingBox(
            id='bbox_002',
            classification='car',
            data=(200.0, 300.0, 100.0, 80.0),
            attrs=[DMAttribute(name='color', value='red')],
        )
        assert len(bbox.attrs) == 1
        assert bbox.attrs[0].name == 'color'
        assert bbox.attrs[0].value == 'red'

    def test_invalid_id_pattern(self):
        """Test that invalid ID patterns are rejected."""
        with pytest.raises(ValueError):
            DMv2BoundingBox(
                id='invalid id with spaces',
                classification='person',
                data=(0, 0, 10, 10),
            )


class TestDMv2Polygon:
    """Tests for DMv2Polygon model."""

    def test_create_polygon(self):
        """Test creating a polygon."""
        polygon = DMv2Polygon(
            id='poly_001',
            classification='building',
            data=[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
        )
        assert polygon.id == 'poly_001'
        assert polygon.classification == 'building'
        assert len(polygon.data) == 4


class TestDMv2Keypoint:
    """Tests for DMv2Keypoint model."""

    def test_create_keypoint(self):
        """Test creating a keypoint."""
        kpt = DMv2Keypoint(
            id='kpt_001',
            classification='nose',
            data=(150.0, 200.0),
        )
        assert kpt.id == 'kpt_001'
        assert kpt.classification == 'nose'
        assert kpt.data == (150.0, 200.0)


class TestDMv2Relation:
    """Tests for DMv2Relation model."""

    def test_create_relation(self):
        """Test creating a relation."""
        rel = DMv2Relation(
            id='rel_001',
            classification='connected_to',
            data=('bbox_001', 'bbox_002'),
        )
        assert rel.id == 'rel_001'
        assert rel.classification == 'connected_to'
        assert rel.data == ('bbox_001', 'bbox_002')


class TestDMv2Group:
    """Tests for DMv2Group model."""

    def test_create_group(self):
        """Test creating a group."""
        group = DMv2Group(
            id='group_001',
            classification='vehicle_parts',
            data=['bbox_001', 'bbox_002', 'bbox_003'],
        )
        assert group.id == 'group_001'
        assert group.classification == 'vehicle_parts'
        assert len(group.data) == 3


class TestDMv2ImageItem:
    """Tests for DMv2ImageItem model."""

    def test_create_empty_image_item(self):
        """Test creating an empty image item."""
        item = DMv2ImageItem()
        assert item.bounding_box == []
        assert item.polygon == []
        assert item.polyline == []
        assert item.keypoint == []
        assert item.relation == []
        assert item.group == []

    def test_create_image_item_with_annotations(self):
        """Test creating an image item with annotations."""
        bbox = DMv2BoundingBox(id='b1', classification='person', data=(10, 20, 30, 40))
        kpt = DMv2Keypoint(id='k1', classification='nose', data=(25, 30))

        item = DMv2ImageItem(bounding_box=[bbox], keypoint=[kpt])
        assert len(item.bounding_box) == 1
        assert len(item.keypoint) == 1
        assert item.bounding_box[0].id == 'b1'
        assert item.keypoint[0].id == 'k1'


class TestDMv2Dataset:
    """Tests for DMv2Dataset model."""

    def test_create_empty_dataset(self):
        """Test creating an empty dataset."""
        dataset = DMv2Dataset()
        assert dataset.classification == {}
        assert dataset.images == []

    def test_create_dataset_with_classification(self):
        """Test creating a dataset with classification."""
        dataset = DMv2Dataset(
            classification={
                'bounding_box': ['person', 'car', 'bicycle'],
                'polygon': ['building', 'tree'],
            }
        )
        assert 'bounding_box' in dataset.classification
        assert len(dataset.classification['bounding_box']) == 3

    def test_get_class_names(self):
        """Test getting class names for a specific tool."""
        dataset = DMv2Dataset(
            classification={
                'bounding_box': ['person', 'car'],
                'polygon': ['building'],
            }
        )
        bbox_classes = dataset.get_class_names('bounding_box')
        assert bbox_classes == ['person', 'car']

        polygon_classes = dataset.get_class_names('polygon')
        assert polygon_classes == ['building']

        # Non-existent tool
        other_classes = dataset.get_class_names('nonexistent')
        assert other_classes == []

    def test_get_all_class_names(self):
        """Test getting all unique class names."""
        dataset = DMv2Dataset(
            classification={
                'bounding_box': ['person', 'car', 'bicycle'],
                'polygon': ['building', 'person'],  # 'person' appears twice
            }
        )
        all_classes = dataset.get_all_class_names()
        assert all_classes == ['bicycle', 'building', 'car', 'person']  # Sorted and unique

    def test_dataset_serialization(self):
        """Test dataset serialization."""
        bbox = DMv2BoundingBox(id='b1', classification='person', data=(10, 20, 30, 40))
        item = DMv2ImageItem(bounding_box=[bbox])
        dataset = DMv2Dataset(classification={'bounding_box': ['person']}, images=[item])

        data = dataset.model_dump()
        assert 'classification' in data
        assert 'images' in data
        assert len(data['images']) == 1

    def test_dataset_deserialization(self):
        """Test dataset deserialization."""
        data = {
            'classification': {'bounding_box': ['person', 'car']},
            'images': [
                {
                    'bounding_box': [
                        {
                            'id': 'b1',
                            'classification': 'person',
                            'data': [10.0, 20.0, 30.0, 40.0],
                            'attrs': [],
                        }
                    ],
                    'polygon': [],
                    'polyline': [],
                    'keypoint': [],
                    'relation': [],
                    'group': [],
                }
            ],
        }
        dataset = DMv2Dataset.model_validate(data)
        assert len(dataset.images) == 1
        assert len(dataset.images[0].bounding_box) == 1
        assert dataset.images[0].bounding_box[0].id == 'b1'
