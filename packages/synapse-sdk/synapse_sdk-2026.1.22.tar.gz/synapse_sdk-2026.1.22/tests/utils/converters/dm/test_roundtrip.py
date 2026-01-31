"""
Roundtrip Conversion Tests

TDD: Tests written before implementation

Verifies that V1 → V2 → V1 and V2 → V1 → V2 conversions preserve data.
"""

import pytest

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2ToV1Roundtrip:
    """V1 to V2 to V1 roundtrip tests (US5)"""

    def test_bounding_box_coordinates_preserved(self, v1_bounding_box_sample):
        """Bounding box coordinates are preserved after roundtrip"""
        original_data = v1_bounding_box_sample['annotationsData']['image_1'][0]['coordinate']

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_bounding_box_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_data = v1_result['annotationsData']['image_1'][0]['coordinate']

        assert result_data['x'] == original_data['x']
        assert result_data['y'] == original_data['y']
        assert result_data['width'] == original_data['width']
        assert result_data['height'] == original_data['height']

    def test_bounding_box_rotation_preserved(self, v1_bounding_box_sample):
        """Bounding box rotation is preserved after roundtrip"""
        original_data = v1_bounding_box_sample['annotationsData']['image_1'][0]['coordinate']

        if 'rotation' not in original_data:
            pytest.skip("Sample doesn't have rotation")

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_bounding_box_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_data = v1_result['annotationsData']['image_1'][0]['coordinate']

        assert result_data.get('rotation') == original_data['rotation']

    def test_bounding_box_classification_preserved(self, v1_bounding_box_sample):
        """Bounding box classification is preserved after roundtrip"""
        original_ann = v1_bounding_box_sample['annotations']['image_1'][0]
        original_class = original_ann['classification']['class']

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_bounding_box_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_ann = v1_result['annotations']['image_1'][0]

        assert result_ann['classification']['class'] == original_class

    def test_bounding_box_id_preserved(self, v1_bounding_box_sample):
        """Bounding box ID is preserved after roundtrip"""
        original_id = v1_bounding_box_sample['annotations']['image_1'][0]['id']

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_bounding_box_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_id = v1_result['annotations']['image_1'][0]['id']

        assert result_id == original_id

    def test_polygon_all_points_preserved(self, v1_polygon_sample):
        """All polygon points are preserved after roundtrip"""
        original_coord = v1_polygon_sample['annotationsData']['image_1'][0]['coordinate']

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_polygon_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_coord = v1_result['annotationsData']['image_1'][0]['coordinate']

        # point count matches
        assert len(result_coord) == len(original_coord)

        # All points x, y coordinates match
        for i, (result_pt, original_pt) in enumerate(zip(result_coord, original_coord)):
            assert result_pt['x'] == original_pt['x'], f'Point {i} x coordinate mismatch'
            assert result_pt['y'] == original_pt['y'], f'Point {i} y coordinate mismatch'

    def test_polygon_classification_preserved(self, v1_polygon_sample):
        """Polygon classification is preserved after roundtrip"""
        original_class = v1_polygon_sample['annotations']['image_1'][0]['classification']['class']

        # V1 → V2 → V1
        v2_result = convert_v1_to_v2(v1_polygon_sample)
        v1_result = convert_v2_to_v1(v2_result)

        result_class = v1_result['annotations']['image_1'][0]['classification']['class']

        assert result_class == original_class


class TestV2ToV1ToV2Roundtrip:
    """V2 to V1 to V2 roundtrip tests (US5)"""

    def test_bounding_box_data_preserved(self, v2_bounding_box_sample):
        """Bounding box data is preserved after roundtrip"""
        original_data = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['data']

        # V2 → V1 → V2
        v1_result = convert_v2_to_v1(v2_bounding_box_sample)
        v2_result = convert_v1_to_v2(v1_result)

        result_data = v2_result['annotation_data']['images'][0]['bounding_box'][0]['data']

        assert result_data == original_data

    def test_bounding_box_classification_preserved(self, v2_bounding_box_sample):
        """Bounding box classification is preserved after roundtrip"""
        original_class = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['classification']

        # V2 → V1 → V2
        v1_result = convert_v2_to_v1(v2_bounding_box_sample)
        v2_result = convert_v1_to_v2(v1_result)

        result_class = v2_result['annotation_data']['images'][0]['bounding_box'][0]['classification']

        assert result_class == original_class

    def test_bounding_box_id_preserved(self, v2_bounding_box_sample):
        """Bounding box ID is preserved after roundtrip"""
        original_id = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['id']

        # V2 → V1 → V2
        v1_result = convert_v2_to_v1(v2_bounding_box_sample)
        v2_result = convert_v1_to_v2(v1_result)

        result_id = v2_result['annotation_data']['images'][0]['bounding_box'][0]['id']

        assert result_id == original_id

    def test_polygon_data_preserved(self, v2_polygon_sample):
        """Polygon data is preserved after roundtrip"""
        original_data = v2_polygon_sample['annotation_data']['images'][0]['polygon'][0]['data']

        # V2 → V1 → V2
        v1_result = convert_v2_to_v1(v2_polygon_sample)
        v2_result = convert_v1_to_v2(v1_result)

        result_data = v2_result['annotation_data']['images'][0]['polygon'][0]['data']

        # All point coordinates match
        assert len(result_data) == len(original_data)
        for i, (result_pt, original_pt) in enumerate(zip(result_data, original_data)):
            assert result_pt == original_pt, f'Point {i} mismatch'

    def test_polygon_classification_preserved(self, v2_polygon_sample):
        """Polygon classification is preserved after roundtrip"""
        original_class = v2_polygon_sample['annotation_data']['images'][0]['polygon'][0]['classification']

        # V2 → V1 → V2
        v1_result = convert_v2_to_v1(v2_polygon_sample)
        v2_result = convert_v1_to_v2(v1_result)

        result_class = v2_result['annotation_data']['images'][0]['polygon'][0]['classification']

        assert result_class == original_class
