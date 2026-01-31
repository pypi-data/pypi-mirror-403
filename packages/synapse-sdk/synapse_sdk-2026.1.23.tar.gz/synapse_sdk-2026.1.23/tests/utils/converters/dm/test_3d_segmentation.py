"""
3D Segmentation Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV23DSegmentation:
    """V1 to V2 3D segmentation conversion tests"""

    def test_basic_conversion_returns_split_result(self, v1_3d_segmentation_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_3d_segmentation_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_points_to_data(self, v1_3d_segmentation_sample):
        """points → data.points conversion"""
        result = convert_v1_to_v2(v1_3d_segmentation_sample)
        annotation_data = result['annotation_data']

        seg_list = annotation_data['pcds'][0].get('3d_segmentation', [])
        assert len(seg_list) > 0

        seg = seg_list[0]
        data = seg.get('data', {})

        assert 'points' in data
        assert isinstance(data['points'], list)

    def test_points_values_correct(self, v1_3d_segmentation_sample):
        """points values are converted accurately"""
        result = convert_v1_to_v2(v1_3d_segmentation_sample)
        annotation_data = result['annotation_data']

        original_points = v1_3d_segmentation_sample['annotationsData']['pcd_1'][0]['points']
        seg = annotation_data['pcds'][0]['3d_segmentation'][0]
        data = seg['data']

        assert data['points'] == original_points

    def test_id_preserved(self, v1_3d_segmentation_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_3d_segmentation_sample)
        annotation_data = result['annotation_data']

        seg = annotation_data['pcds'][0]['3d_segmentation'][0]
        original_id = v1_3d_segmentation_sample['annotations']['pcd_1'][0]['id']

        assert seg['id'] == original_id


class TestV2ToV13DSegmentation:
    """V2 to V1 3D segmentation conversion tests"""

    def test_complete_conversion_with_meta(self, v2_3d_segmentation_sample):
        """Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_3d_segmentation_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'pcd_1' in result['annotations']

        points = result['annotationsData']['pcd_1'][0]['points']
        assert isinstance(points, list)

    def test_data_to_points_values_correct(self, v2_3d_segmentation_sample):
        """data.points is converted accurately to points"""
        result = convert_v2_to_v1(v2_3d_segmentation_sample)

        original_data = v2_3d_segmentation_sample['annotation_data']['pcds'][0]['3d_segmentation'][0]['data']
        result_points = result['annotationsData']['pcd_1'][0]['points']

        assert result_points == original_data['points']

    def test_tool_field_set(self, v2_3d_segmentation_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_3d_segmentation_sample)

        ann = result['annotations']['pcd_1'][0]
        assert ann['tool'] == '3d_segmentation'


class TestRoundtrip3DSegmentation:
    """3D segmentation roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_points(self, v1_3d_segmentation_sample):
        """points is preserved in V1→V2→V1 conversion"""
        v2_result = convert_v1_to_v2(v1_3d_segmentation_sample)
        v1_result = convert_v2_to_v1(v2_result)

        original_points = v1_3d_segmentation_sample['annotationsData']['pcd_1'][0]['points']
        result_points = v1_result['annotationsData']['pcd_1'][0]['points']

        assert result_points == original_points

    def test_v2_to_v1_to_v2_preserves_data(self, v2_3d_segmentation_sample):
        """data is preserved in V2→V1→V2 conversion"""
        v1_result = convert_v2_to_v1(v2_3d_segmentation_sample)
        v2_result = convert_v1_to_v2(v1_result)

        original_data = v2_3d_segmentation_sample['annotation_data']['pcds'][0]['3d_segmentation'][0]['data']
        result_data = v2_result['annotation_data']['pcds'][0]['3d_segmentation'][0]['data']

        assert result_data['points'] == original_data['points']
