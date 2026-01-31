"""
Bounding Box Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2BoundingBox:
    """V1 → V2 Bounding Box Conversion Tests (US1)"""

    def test_basic_conversion_returns_split_result(self, v1_bounding_box_sample):
        """US1 Scenario 1: Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_bounding_box_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_v2_structure_contains_required_fields(self, v1_bounding_box_sample):
        """US1 Scenario 2: annotation_data contains id, classification, attrs, data"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_data = result['annotation_data']

        # classification map exists
        assert 'classification' in annotation_data
        assert 'bounding_box' in annotation_data['classification']

        # images array exists
        assert 'images' in annotation_data
        assert len(annotation_data['images']) > 0

        # Verify bounding box annotation
        bbox_list = annotation_data['images'][0].get('bounding_box', [])
        assert len(bbox_list) > 0

        bbox = bbox_list[0]
        assert 'id' in bbox
        assert 'classification' in bbox
        assert 'attrs' in bbox
        assert 'data' in bbox

        # data is in [x, y, width, height] format
        assert len(bbox['data']) == 4

    def test_annotation_meta_preserves_v1_structure(self, v1_bounding_box_sample):
        """US1 Scenario 3: annotation_meta preserves V1 top-level structure"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_meta = result['annotation_meta']

        # Verify V1 top-level structure keys
        assert 'annotations' in annotation_meta
        assert 'annotationsData' in annotation_meta
        assert 'extra' in annotation_meta
        assert 'relations' in annotation_meta
        assert 'annotationGroups' in annotation_meta

    def test_rotation_preserved_in_attrs(self, v1_bounding_box_sample):
        """US1 Scenario 4: rotation info is preserved in attrs as radian value"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['images'][0]['bounding_box'][0]
        attrs = bbox.get('attrs', [])

        # Find rotation attribute
        rotation_attr = next((a for a in attrs if a['name'] == 'rotation'), None)

        # If original has rotation, attrs should have it too
        original_coord = v1_bounding_box_sample['annotationsData']['image_1'][0]['coordinate']
        if 'rotation' in original_coord:
            assert rotation_attr is not None
            assert rotation_attr['value'] == original_coord['rotation']

    def test_meta_fields_preserved_in_annotation_meta(self, v1_bounding_box_sample):
        """US1 Scenario 5: isValid, isDrawCompleted, label and other meta fields are preserved in annotation_meta"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_meta = result['annotation_meta']

        original_ann = v1_bounding_box_sample['annotations']['image_1'][0]
        meta_ann = annotation_meta['annotations']['image_1'][0]

        # Verify meta fields are preserved
        assert meta_ann.get('isValid') == original_ann.get('isValid')
        assert meta_ann.get('isLocked') == original_ann.get('isLocked')
        assert meta_ann.get('isVisible') == original_ann.get('isVisible')
        assert meta_ann.get('label') == original_ann.get('label')

    def test_coordinate_values_correct(self, v1_bounding_box_sample):
        """Coordinate values are correctly converted"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['images'][0]['bounding_box'][0]
        original_coord = v1_bounding_box_sample['annotationsData']['image_1'][0]['coordinate']

        # data[0,1,2,3] == coordinate.{x, y, width, height}
        assert bbox['data'][0] == original_coord['x']
        assert bbox['data'][1] == original_coord['y']
        assert bbox['data'][2] == original_coord['width']
        assert bbox['data'][3] == original_coord['height']

    def test_id_preserved(self, v1_bounding_box_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['images'][0]['bounding_box'][0]
        original_id = v1_bounding_box_sample['annotations']['image_1'][0]['id']

        assert bbox['id'] == original_id

    def test_classification_extracted_correctly(self, v1_bounding_box_sample):
        """classification.class is extracted to V2 classification"""
        result = convert_v1_to_v2(v1_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['images'][0]['bounding_box'][0]
        original_class = v1_bounding_box_sample['annotations']['image_1'][0]['classification']['class']

        assert bbox['classification'] == original_class


class TestV2ToV1BoundingBox:
    """V2 → V1 Bounding Box Conversion Tests (US2)"""

    def test_complete_conversion_with_meta(self, v2_bounding_box_sample):
        """US2 Scenario 1: Complete V1 conversion with annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']
        assert 'image_1' in result['annotationsData']

    def test_partial_conversion_without_meta(self, v2_bounding_box_sample):
        """US2 Scenario 2: Conversion with only annotation_data uses default values"""
        # Pass only annotation_data
        annotation_data_only = {'annotation_data': v2_bounding_box_sample['annotation_data']}
        result = convert_v2_to_v1(annotation_data_only)

        assert 'annotations' in result
        assert 'annotationsData' in result

        # Verify default values
        ann = result['annotations']['image_1'][0]
        assert ann.get('isLocked') is False
        assert ann.get('isVisible') is True
        assert ann.get('isValid') is False

    def test_data_array_to_coordinate_object(self, v2_bounding_box_sample):
        """US2 Scenario 3: data[x, y, width, height] → coordinate object"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        coord = result['annotationsData']['image_1'][0]['coordinate']
        original_data = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['data']

        assert coord['x'] == original_data[0]
        assert coord['y'] == original_data[1]
        assert coord['width'] == original_data[2]
        assert coord['height'] == original_data[3]

    def test_meta_fields_restored_from_annotation_meta(self, v2_bounding_box_sample):
        """US2 Scenario 4: Meta info restored from annotation_meta"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        ann = result['annotations']['image_1'][0]
        original_meta = v2_bounding_box_sample['annotation_meta']['annotations']['image_1'][0]

        assert ann.get('isValid') == original_meta.get('isValid')
        assert ann.get('isLocked') == original_meta.get('isLocked')

    def test_rotation_restored_from_attrs(self, v2_bounding_box_sample):
        """rotation from attrs is restored to coordinate.rotation"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        coord = result['annotationsData']['image_1'][0]['coordinate']

        # Check rotation from original attrs
        original_attrs = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0].get('attrs', [])
        rotation_attr = next((a for a in original_attrs if a['name'] == 'rotation'), None)

        if rotation_attr:
            assert 'rotation' in coord
            assert coord['rotation'] == rotation_attr['value']

    def test_classification_restored(self, v2_bounding_box_sample):
        """V2 classification is restored to V1 classification.class"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        ann = result['annotations']['image_1'][0]
        original_class = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['classification']

        assert ann['classification']['class'] == original_class

    def test_tool_field_set(self, v2_bounding_box_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'bounding_box'

    def test_id_preserved(self, v2_bounding_box_sample):
        """Annotation ID is preserved"""
        result = convert_v2_to_v1(v2_bounding_box_sample)

        ann = result['annotations']['image_1'][0]
        original_id = v2_bounding_box_sample['annotation_data']['images'][0]['bounding_box'][0]['id']

        assert ann['id'] == original_id
