"""
3D Bounding Box Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV23DBoundingBox:
    """V1 → V2 3D Bounding Box Conversion Tests (US12)"""

    def test_basic_conversion_returns_split_result(self, v1_3d_bounding_box_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_psr_to_data(self, v1_3d_bounding_box_sample):
        """US12 Scenario 1: psr → data conversion"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)
        annotation_data = result['annotation_data']

        # Verify 3d_bounding_box array (pcds media type)
        bbox_list = annotation_data['pcds'][0].get('3d_bounding_box', [])
        assert len(bbox_list) > 0

        bbox = bbox_list[0]
        data = bbox.get('data', {})

        # data contains position, scale, rotation
        assert 'position' in data
        assert 'scale' in data
        assert 'rotation' in data

    def test_psr_values_correct(self, v1_3d_bounding_box_sample):
        """US12 Scenario 2: PSR values are correctly converted"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)
        annotation_data = result['annotation_data']

        original_psr = v1_3d_bounding_box_sample['annotationsData']['pcd_1'][0]['psr']
        bbox = annotation_data['pcds'][0]['3d_bounding_box'][0]
        data = bbox['data']

        # position matches
        assert data['position']['x'] == original_psr['position']['x']
        assert data['position']['y'] == original_psr['position']['y']
        assert data['position']['z'] == original_psr['position']['z']

        # scale matches
        assert data['scale']['x'] == original_psr['scale']['x']
        assert data['scale']['y'] == original_psr['scale']['y']
        assert data['scale']['z'] == original_psr['scale']['z']

        # rotation matches
        assert data['rotation']['x'] == original_psr['rotation']['x']
        assert data['rotation']['y'] == original_psr['rotation']['y']
        assert data['rotation']['z'] == original_psr['rotation']['z']

    def test_meta_preserved_in_annotation_meta(self, v1_3d_bounding_box_sample):
        """Meta info is preserved in annotation_meta"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)
        annotation_meta = result['annotation_meta']

        original_ann = v1_3d_bounding_box_sample['annotations']['pcd_1'][0]
        meta_ann = annotation_meta['annotations']['pcd_1'][0]

        assert meta_ann.get('id') == original_ann.get('id')
        assert meta_ann.get('tool') == '3d_bounding_box'

    def test_id_preserved(self, v1_3d_bounding_box_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['pcds'][0]['3d_bounding_box'][0]
        original_id = v1_3d_bounding_box_sample['annotations']['pcd_1'][0]['id']

        assert bbox['id'] == original_id

    def test_classification_extracted_correctly(self, v1_3d_bounding_box_sample):
        """classification.class is extracted to V2 classification"""
        result = convert_v1_to_v2(v1_3d_bounding_box_sample)
        annotation_data = result['annotation_data']

        bbox = annotation_data['pcds'][0]['3d_bounding_box'][0]
        original_class = v1_3d_bounding_box_sample['annotations']['pcd_1'][0]['classification']['class']

        assert bbox['classification'] == original_class


class TestV2ToV13DBoundingBox:
    """V2 → V1 3D Bounding Box Conversion Tests (US12)"""

    def test_complete_conversion_with_meta(self, v2_3d_bounding_box_sample):
        """US12 Scenario 2: Complete V1 conversion with annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'pcd_1' in result['annotations']

        # Verify psr is in {position, scale, rotation} format
        psr = result['annotationsData']['pcd_1'][0]['psr']
        assert isinstance(psr, dict)
        assert 'position' in psr
        assert 'scale' in psr
        assert 'rotation' in psr

    def test_partial_conversion_works(self, v2_3d_bounding_box_sample):
        """Conversion is possible with only annotation_data"""
        annotation_data_only = {'annotation_data': v2_3d_bounding_box_sample['annotation_data']}
        result = convert_v2_to_v1(annotation_data_only)

        psr = result['annotationsData']['pcd_1'][0]['psr']

        # psr is generated
        assert 'position' in psr
        assert 'scale' in psr
        assert 'rotation' in psr

    def test_psr_values_correct(self, v2_3d_bounding_box_sample):
        """US12 Scenario 3: PSR values are correctly converted"""
        result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        original_data = v2_3d_bounding_box_sample['annotation_data']['pcds'][0]['3d_bounding_box'][0]['data']
        psr = result['annotationsData']['pcd_1'][0]['psr']

        # position matches
        assert psr['position']['x'] == original_data['position']['x']
        assert psr['position']['y'] == original_data['position']['y']
        assert psr['position']['z'] == original_data['position']['z']

        # scale matches
        assert psr['scale']['x'] == original_data['scale']['x']
        assert psr['scale']['y'] == original_data['scale']['y']
        assert psr['scale']['z'] == original_data['scale']['z']

        # rotation matches
        assert psr['rotation']['x'] == original_data['rotation']['x']
        assert psr['rotation']['y'] == original_data['rotation']['y']
        assert psr['rotation']['z'] == original_data['rotation']['z']

    def test_tool_field_set(self, v2_3d_bounding_box_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        ann = result['annotations']['pcd_1'][0]
        assert ann['tool'] == '3d_bounding_box'

    def test_classification_restored(self, v2_3d_bounding_box_sample):
        """V2 classification is restored to V1 classification.class"""
        result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        ann = result['annotations']['pcd_1'][0]
        original_class = v2_3d_bounding_box_sample['annotation_data']['pcds'][0]['3d_bounding_box'][0]['classification']

        assert ann['classification']['class'] == original_class

    def test_attrs_restored_to_classification(self, v2_3d_bounding_box_sample):
        """V2 attrs are restored to V1 classification"""
        result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        ann = result['annotations']['pcd_1'][0]
        original_attrs = v2_3d_bounding_box_sample['annotation_data']['pcds'][0]['3d_bounding_box'][0].get('attrs', [])

        # Verify each attr is restored to classification
        for attr in original_attrs:
            name = attr['name']
            value = attr['value']
            # Only check non-internal attributes (not starting with _)
            if not name.startswith('_'):
                assert ann['classification'].get(name) == value


class TestRoundtrip3DBoundingBox:
    """3D Bounding Box Roundtrip Conversion Tests"""

    def test_v1_to_v2_to_v1_preserves_psr(self, v1_3d_bounding_box_sample):
        """PSR is preserved in V1→V2→V1 conversion"""
        # V1 → V2
        v2_result = convert_v1_to_v2(v1_3d_bounding_box_sample)

        # V2 → V1
        v1_result = convert_v2_to_v1(v2_result)

        # Compare original and result
        original_psr = v1_3d_bounding_box_sample['annotationsData']['pcd_1'][0]['psr']
        result_psr = v1_result['annotationsData']['pcd_1'][0]['psr']

        # position matches
        assert result_psr['position']['x'] == original_psr['position']['x']
        assert result_psr['position']['y'] == original_psr['position']['y']
        assert result_psr['position']['z'] == original_psr['position']['z']

        # scale matches
        assert result_psr['scale']['x'] == original_psr['scale']['x']
        assert result_psr['scale']['y'] == original_psr['scale']['y']
        assert result_psr['scale']['z'] == original_psr['scale']['z']

        # rotation matches
        assert result_psr['rotation']['x'] == original_psr['rotation']['x']
        assert result_psr['rotation']['y'] == original_psr['rotation']['y']
        assert result_psr['rotation']['z'] == original_psr['rotation']['z']

    def test_v2_to_v1_to_v2_preserves_data(self, v2_3d_bounding_box_sample):
        """Data is preserved in V2→V1→V2 conversion"""
        # V2 → V1
        v1_result = convert_v2_to_v1(v2_3d_bounding_box_sample)

        # V1 → V2
        v2_result = convert_v1_to_v2(v1_result)

        # Compare original and result
        original_data = v2_3d_bounding_box_sample['annotation_data']['pcds'][0]['3d_bounding_box'][0]['data']
        result_data = v2_result['annotation_data']['pcds'][0]['3d_bounding_box'][0]['data']

        # position matches
        assert result_data['position']['x'] == original_data['position']['x']
        assert result_data['position']['y'] == original_data['position']['y']
        assert result_data['position']['z'] == original_data['position']['z']

        # scale matches
        assert result_data['scale']['x'] == original_data['scale']['x']
        assert result_data['scale']['y'] == original_data['scale']['y']
        assert result_data['scale']['z'] == original_data['scale']['z']

        # rotation matches
        assert result_data['rotation']['x'] == original_data['rotation']['x']
        assert result_data['rotation']['y'] == original_data['rotation']['y']
        assert result_data['rotation']['z'] == original_data['rotation']['z']
