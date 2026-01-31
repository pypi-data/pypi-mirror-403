"""
Legacy Converter Comparison Tests

Purpose: Verify that the new converter results are equivalent to the legacy converter

Note: dm_legacy returns only annotation_data, while the new converter returns annotation_data + annotation_meta.
Only the annotation_data portion is compared.
"""

import pytest

from synapse_sdk.utils.converters.dm import convert_v1_to_v2


class TestLegacyComparison:
    """Legacy converter and new converter comparison tests"""

    @pytest.fixture
    def sample_v1_bounding_box(self):
        """Bounding box V1 sample data"""
        return {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'isLocked': False,
                        'isVisible': True,
                        'isValid': True,
                        'classification': {'class': 'person'},
                        'label': ['person'],
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 100, 'y': 200, 'width': 150, 'height': 100},
                    }
                ]
            },
        }

    @pytest.fixture
    def sample_v1_polygon(self):
        """Polygon V1 sample data"""
        return {
            'annotations': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'tool': 'polygon',
                        'isLocked': False,
                        'isVisible': True,
                        'classification': {'class': 'road'},
                        'label': ['road'],
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'coordinate': [
                            {'x': 0, 'y': 0, 'id': 'p1'},
                            {'x': 100, 'y': 0, 'id': 'p2'},
                            {'x': 50, 'y': 100, 'id': 'p3'},
                        ],
                    }
                ]
            },
        }

    def test_bounding_box_annotation_data_structure(self, sample_v1_bounding_box):
        """Bounding box: annotation_data structure is compatible with legacy"""
        result = convert_v1_to_v2(sample_v1_bounding_box)
        annotation_data = result['annotation_data']

        # legacy format: classification, images array
        assert 'classification' in annotation_data
        assert 'images' in annotation_data

        # classification map structure
        assert 'bounding_box' in annotation_data['classification']
        assert 'person' in annotation_data['classification']['bounding_box']

        # images array structure
        assert len(annotation_data['images']) == 1
        assert 'bounding_box' in annotation_data['images'][0]

    def test_bounding_box_data_format(self, sample_v1_bounding_box):
        """Bounding box: data array format is identical to legacy"""
        result = convert_v1_to_v2(sample_v1_bounding_box)
        bbox = result['annotation_data']['images'][0]['bounding_box'][0]

        # legacy format: [x, y, width, height]
        assert bbox['data'] == [100, 200, 150, 100]
        assert bbox['id'] == 'ann_1'
        assert bbox['classification'] == 'person'
        assert isinstance(bbox['attrs'], list)

    def test_polygon_annotation_data_structure(self, sample_v1_polygon):
        """Polygon: annotation_data structure is compatible with legacy"""
        result = convert_v1_to_v2(sample_v1_polygon)
        annotation_data = result['annotation_data']

        assert 'classification' in annotation_data
        assert 'images' in annotation_data
        assert 'polygon' in annotation_data['classification']

    def test_polygon_data_format(self, sample_v1_polygon):
        """Polygon: data array format is identical to legacy"""
        result = convert_v1_to_v2(sample_v1_polygon)
        polygon = result['annotation_data']['images'][0]['polygon'][0]

        # legacy format: [[x, y], [x, y], ...]
        assert polygon['data'] == [[0, 0], [100, 0], [50, 100]]
        assert polygon['id'] == 'poly_1'
        assert polygon['classification'] == 'road'
        assert isinstance(polygon['attrs'], list)

    def test_mixed_tools_annotation_data(self, sample_v1_bounding_box, sample_v1_polygon):
        """Mixed tools: annotation_data structure is compatible with legacy"""
        mixed_v1 = {
            'annotations': {
                'image_1': [
                    sample_v1_bounding_box['annotations']['image_1'][0],
                    sample_v1_polygon['annotations']['image_1'][0],
                ]
            },
            'annotationsData': {
                'image_1': [
                    sample_v1_bounding_box['annotationsData']['image_1'][0],
                    sample_v1_polygon['annotationsData']['image_1'][0],
                ]
            },
        }

        result = convert_v1_to_v2(mixed_v1)
        annotation_data = result['annotation_data']

        # both tools included in classification
        assert 'bounding_box' in annotation_data['classification']
        assert 'polygon' in annotation_data['classification']

        # both tools included in images array
        images = annotation_data['images'][0]
        assert 'bounding_box' in images
        assert 'polygon' in images


class TestLegacyDirectComparison:
    """Direct comparison with legacy converter (when legacy code is available)"""

    @pytest.fixture
    def sample_v1_data(self):
        """V1 sample data for testing"""
        return {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'isLocked': False,
                        'isVisible': True,
                        'classification': {'class': 'person'},
                        'label': ['person'],
                    },
                    {
                        'id': 'ann_2',
                        'tool': 'polygon',
                        'isLocked': False,
                        'isVisible': True,
                        'classification': {'class': 'road'},
                        'label': ['road'],
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 10, 'y': 20, 'width': 100, 'height': 50},
                    },
                    {
                        'id': 'ann_2',
                        'coordinate': [
                            {'x': 0, 'y': 0, 'id': 'p1'},
                            {'x': 100, 'y': 0, 'id': 'p2'},
                            {'x': 50, 'y': 100, 'id': 'p3'},
                        ],
                    },
                ]
            },
        }

    def test_compare_with_legacy_converter(self, sample_v1_data):
        """Compare results with legacy converter"""
        try:
            from synapse_sdk.utils.converters.dm_legacy.from_v1 import DMV1ToV2Converter as LegacyConverter

            # run legacy converter
            legacy_converter = LegacyConverter(old_dm_data=sample_v1_data)
            legacy_result = legacy_converter.convert()

            # run new converter
            new_result = convert_v1_to_v2(sample_v1_data)
            annotation_data = new_result['annotation_data']

            # compare classification maps
            assert set(legacy_result['classification'].keys()) == set(annotation_data['classification'].keys())

            for tool in legacy_result['classification']:
                assert set(legacy_result['classification'][tool]) == set(annotation_data['classification'][tool])

            # compare images array structure
            assert len(legacy_result.get('images', [])) == len(annotation_data.get('images', []))

            if legacy_result.get('images') and annotation_data.get('images'):
                legacy_image = legacy_result['images'][0]
                new_image = annotation_data['images'][0]

                # compare annotation count per tool
                for tool in legacy_image:
                    if tool in new_image:
                        assert len(legacy_image[tool]) == len(new_image[tool])

                        # compare key fields of each annotation
                        for legacy_ann, new_ann in zip(legacy_image[tool], new_image[tool]):
                            assert legacy_ann['id'] == new_ann['id']
                            assert legacy_ann['classification'] == new_ann['classification']
                            assert legacy_ann['data'] == new_ann['data']

        except ImportError:
            pytest.skip('Legacy converter not available')
