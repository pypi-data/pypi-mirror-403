"""
Keypoint Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Keypoint:
    """V1 → V2 Keypoint Conversion Tests (US8)"""

    def test_basic_conversion_returns_split_result(self, v1_keypoint_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_keypoint_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_coordinate_object_to_array(self, v1_keypoint_sample):
        """US8 Scenario 1: coordinate {x, y} → data [x, y]"""
        result = convert_v1_to_v2(v1_keypoint_sample)
        annotation_data = result['annotation_data']

        # Verify keypoint array
        keypoint_list = annotation_data['images'][0].get('keypoint', [])
        assert len(keypoint_list) > 0

        keypoint = keypoint_list[0]
        data = keypoint.get('data', [])

        # Verify data is in [x, y] format
        assert isinstance(data, list)
        assert len(data) == 2

    def test_coordinate_values_correct(self, v1_keypoint_sample):
        """US8 Scenario 2: Coordinate values are correctly converted"""
        result = convert_v1_to_v2(v1_keypoint_sample)
        annotation_data = result['annotation_data']

        original_coord = v1_keypoint_sample['annotationsData']['image_1'][0]['coordinate']
        keypoint = annotation_data['images'][0]['keypoint'][0]
        data = keypoint['data']

        # Coordinates match
        assert data[0] == original_coord['x']
        assert data[1] == original_coord['y']

    def test_meta_preserved_in_annotation_meta(self, v1_keypoint_sample):
        """Meta info is preserved in annotation_meta"""
        result = convert_v1_to_v2(v1_keypoint_sample)
        annotation_meta = result['annotation_meta']

        original_ann = v1_keypoint_sample['annotations']['image_1'][0]
        meta_ann = annotation_meta['annotations']['image_1'][0]

        assert meta_ann.get('id') == original_ann.get('id')
        assert meta_ann.get('tool') == 'keypoint'

    def test_id_preserved(self, v1_keypoint_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_keypoint_sample)
        annotation_data = result['annotation_data']

        keypoint = annotation_data['images'][0]['keypoint'][0]
        original_id = v1_keypoint_sample['annotations']['image_1'][0]['id']

        assert keypoint['id'] == original_id

    def test_classification_extracted_correctly(self, v1_keypoint_sample):
        """classification.class is extracted to V2 classification"""
        result = convert_v1_to_v2(v1_keypoint_sample)
        annotation_data = result['annotation_data']

        keypoint = annotation_data['images'][0]['keypoint'][0]
        original_class = v1_keypoint_sample['annotations']['image_1'][0]['classification']['class']

        assert keypoint['classification'] == original_class


class TestV2ToV1Keypoint:
    """V2 → V1 Keypoint Conversion Tests (US8)"""

    def test_complete_conversion_with_meta(self, v2_keypoint_sample):
        """US8 Scenario 2: Complete V1 conversion with annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_keypoint_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']

        # Verify coordinate is in {x, y} format
        coord = result['annotationsData']['image_1'][0]['coordinate']
        assert isinstance(coord, dict)
        assert 'x' in coord
        assert 'y' in coord

    def test_partial_conversion_works(self, v2_keypoint_sample):
        """Conversion is possible with only annotation_data"""
        annotation_data_only = {'annotation_data': v2_keypoint_sample['annotation_data']}
        result = convert_v2_to_v1(annotation_data_only)

        coord = result['annotationsData']['image_1'][0]['coordinate']

        # Coordinate is generated
        assert 'x' in coord
        assert 'y' in coord

    def test_coordinate_values_correct(self, v2_keypoint_sample):
        """US8 Scenario 3: Coordinate values are correctly converted"""
        result = convert_v2_to_v1(v2_keypoint_sample)

        original_data = v2_keypoint_sample['annotation_data']['images'][0]['keypoint'][0]['data']
        coord = result['annotationsData']['image_1'][0]['coordinate']

        # Coordinates match
        assert coord['x'] == original_data[0]
        assert coord['y'] == original_data[1]

    def test_tool_field_set(self, v2_keypoint_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_keypoint_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'keypoint'

    def test_classification_restored(self, v2_keypoint_sample):
        """V2 classification is restored to V1 classification.class"""
        result = convert_v2_to_v1(v2_keypoint_sample)

        ann = result['annotations']['image_1'][0]
        original_class = v2_keypoint_sample['annotation_data']['images'][0]['keypoint'][0]['classification']

        assert ann['classification']['class'] == original_class

    def test_attrs_restored_to_classification(self, v2_keypoint_sample):
        """V2 attrs are restored to V1 classification"""
        result = convert_v2_to_v1(v2_keypoint_sample)

        ann = result['annotations']['image_1'][0]
        original_attrs = v2_keypoint_sample['annotation_data']['images'][0]['keypoint'][0].get('attrs', [])

        # Verify each attr is restored to classification
        for attr in original_attrs:
            name = attr['name']
            value = attr['value']
            # Only check non-internal attributes (not starting with _)
            if not name.startswith('_'):
                assert ann['classification'].get(name) == value


class TestRoundtripKeypoint:
    """Keypoint Roundtrip Conversion Tests"""

    def test_v1_to_v2_to_v1_preserves_coordinates(self, v1_keypoint_sample):
        """Coordinates are preserved in V1→V2→V1 conversion"""
        # V1 → V2
        v2_result = convert_v1_to_v2(v1_keypoint_sample)

        # V2 → V1
        v1_result = convert_v2_to_v1(v2_result)

        # Compare original and result
        original_coord = v1_keypoint_sample['annotationsData']['image_1'][0]['coordinate']
        result_coord = v1_result['annotationsData']['image_1'][0]['coordinate']

        assert result_coord['x'] == original_coord['x']
        assert result_coord['y'] == original_coord['y']

    def test_v2_to_v1_to_v2_preserves_data(self, v2_keypoint_sample):
        """Data is preserved in V2→V1→V2 conversion"""
        # V2 → V1
        v1_result = convert_v2_to_v1(v2_keypoint_sample)

        # V1 → V2
        v2_result = convert_v1_to_v2(v1_result)

        # Compare original and result
        original_data = v2_keypoint_sample['annotation_data']['images'][0]['keypoint'][0]['data']
        result_data = v2_result['annotation_data']['images'][0]['keypoint'][0]['data']

        assert result_data[0] == original_data[0]  # x
        assert result_data[1] == original_data[1]  # y
