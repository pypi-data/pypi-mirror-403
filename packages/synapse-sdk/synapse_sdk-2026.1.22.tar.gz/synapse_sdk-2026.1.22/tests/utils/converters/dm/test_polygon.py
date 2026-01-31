"""
Polygon Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Polygon:
    """V1 → V2 Polygon Conversion Tests (US3)"""

    def test_basic_conversion_returns_split_result(self, v1_polygon_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_polygon_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_coordinate_array_to_nested_array(self, v1_polygon_sample):
        """US3 Scenario 1: coordinate [{x, y, id}] → data [[x, y]]"""
        result = convert_v1_to_v2(v1_polygon_sample)
        annotation_data = result['annotation_data']

        # Verify polygon array
        polygon_list = annotation_data['images'][0].get('polygon', [])
        assert len(polygon_list) > 0

        polygon = polygon_list[0]
        data = polygon.get('data', [])

        # Verify each point is in [x, y] format
        assert len(data) >= 3  # Polygon has at least 3 points
        for point in data:
            assert isinstance(point, list)
            assert len(point) == 2

    def test_all_points_converted_in_order(self, v1_polygon_sample):
        """US3 Scenario 2: All points are converted in order"""
        result = convert_v1_to_v2(v1_polygon_sample)
        annotation_data = result['annotation_data']

        original_coord = v1_polygon_sample['annotationsData']['image_1'][0]['coordinate']
        polygon = annotation_data['images'][0]['polygon'][0]
        data = polygon['data']

        # Point count matches
        assert len(data) == len(original_coord)

        # Coordinates match in order
        for i, (v2_point, v1_point) in enumerate(zip(data, original_coord)):
            assert v2_point[0] == v1_point['x'], f'Point {i} x coordinate mismatch'
            assert v2_point[1] == v1_point['y'], f'Point {i} y coordinate mismatch'

    def test_meta_preserved_in_annotation_meta(self, v1_polygon_sample):
        """Meta info is preserved in annotation_meta"""
        result = convert_v1_to_v2(v1_polygon_sample)
        annotation_meta = result['annotation_meta']

        original_ann = v1_polygon_sample['annotations']['image_1'][0]
        meta_ann = annotation_meta['annotations']['image_1'][0]

        assert meta_ann.get('id') == original_ann.get('id')
        assert meta_ann.get('tool') == 'polygon'

    def test_id_preserved(self, v1_polygon_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_polygon_sample)
        annotation_data = result['annotation_data']

        polygon = annotation_data['images'][0]['polygon'][0]
        original_id = v1_polygon_sample['annotations']['image_1'][0]['id']

        assert polygon['id'] == original_id

    def test_classification_extracted_correctly(self, v1_polygon_sample):
        """classification.class is extracted to V2 classification"""
        result = convert_v1_to_v2(v1_polygon_sample)
        annotation_data = result['annotation_data']

        polygon = annotation_data['images'][0]['polygon'][0]
        original_class = v1_polygon_sample['annotations']['image_1'][0]['classification']['class']

        assert polygon['classification'] == original_class


class TestV2ToV1Polygon:
    """V2 → V1 Polygon Conversion Tests (US4)"""

    def test_complete_conversion_with_meta(self, v2_polygon_sample):
        """US4 Scenario 1: Complete V1 conversion with annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_polygon_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']

        # verify coordinate is in [{x, y, id}] format
        coord = result['annotationsData']['image_1'][0]['coordinate']
        assert isinstance(coord, list)
        assert len(coord) >= 3

        for point in coord:
            assert 'x' in point
            assert 'y' in point
            assert 'id' in point

    def test_partial_conversion_generates_ids(self, v2_polygon_sample):
        """US4 Scenario 2: Conversion with only annotation_data generates unique id for each point"""
        annotation_data_only = {'annotation_data': v2_polygon_sample['annotation_data']}
        result = convert_v2_to_v1(annotation_data_only)

        coord = result['annotationsData']['image_1'][0]['coordinate']

        # Verify each point has an id generated
        ids = set()
        for point in coord:
            assert 'id' in point
            assert point['id']  # Not empty string
            ids.add(point['id'])

        # Verify all ids are unique
        assert len(ids) == len(coord)

    def test_complex_polygon_all_points_preserved(self, v2_polygon_sample):
        """US4 Scenario 3: All points of complex polygon are converted with exact order and coordinate values"""
        result = convert_v2_to_v1(v2_polygon_sample)

        original_data = v2_polygon_sample['annotation_data']['images'][0]['polygon'][0]['data']
        coord = result['annotationsData']['image_1'][0]['coordinate']

        # Point count matches
        assert len(coord) == len(original_data)

        # Coordinates match in order
        for i, (v1_point, v2_point) in enumerate(zip(coord, original_data)):
            assert v1_point['x'] == v2_point[0], f'Point {i} x coordinate mismatch'
            assert v1_point['y'] == v2_point[1], f'Point {i} y coordinate mismatch'

    def test_tool_field_set(self, v2_polygon_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_polygon_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'polygon'

    def test_classification_restored(self, v2_polygon_sample):
        """V2 classification is restored to V1 classification.class"""
        result = convert_v2_to_v1(v2_polygon_sample)

        ann = result['annotations']['image_1'][0]
        original_class = v2_polygon_sample['annotation_data']['images'][0]['polygon'][0]['classification']

        assert ann['classification']['class'] == original_class

    def test_attrs_restored_to_classification(self, v2_polygon_sample):
        """V2 attrs are restored to V1 classification"""
        result = convert_v2_to_v1(v2_polygon_sample)

        ann = result['annotations']['image_1'][0]
        original_attrs = v2_polygon_sample['annotation_data']['images'][0]['polygon'][0].get('attrs', [])

        # Verify each attr is restored to classification
        for attr in original_attrs:
            name = attr['name']
            value = attr['value']
            # Only check non-internal attributes (not starting with _)
            if not name.startswith('_'):
                assert ann['classification'].get(name) == value
