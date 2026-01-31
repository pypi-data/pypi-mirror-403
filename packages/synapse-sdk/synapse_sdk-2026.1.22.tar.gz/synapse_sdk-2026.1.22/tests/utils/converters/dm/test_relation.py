"""
Relation Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Relation:
    """V1 to V2 relation conversion tests"""

    def test_basic_conversion_returns_split_result(self, v1_relation_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_relation_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_annotation_ids_to_data(self, v1_relation_sample):
        """annotationId, targetAnnotationId → data [from_id, to_id] conversion"""
        result = convert_v1_to_v2(v1_relation_sample)
        annotation_data = result['annotation_data']

        rel_list = annotation_data['images'][0].get('relation', [])
        assert len(rel_list) > 0

        rel = rel_list[0]
        data = rel.get('data', [])

        assert isinstance(data, list)
        assert len(data) == 2

    def test_data_values_correct(self, v1_relation_sample):
        """annotationId, targetAnnotationId values are converted accurately"""
        result = convert_v1_to_v2(v1_relation_sample)
        annotation_data = result['annotation_data']

        original_data = v1_relation_sample['annotationsData']['image_1'][0]
        rel = annotation_data['images'][0]['relation'][0]
        data = rel['data']

        assert data[0] == original_data['annotationId']
        assert data[1] == original_data['targetAnnotationId']

    def test_id_preserved(self, v1_relation_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_relation_sample)
        annotation_data = result['annotation_data']

        rel = annotation_data['images'][0]['relation'][0]
        original_id = v1_relation_sample['annotations']['image_1'][0]['id']

        assert rel['id'] == original_id


class TestV2ToV1Relation:
    """V2 to V1 relation conversion tests"""

    def test_complete_conversion_with_meta(self, v2_relation_sample):
        """Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_relation_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']

        data = result['annotationsData']['image_1'][0]
        assert 'annotationId' in data
        assert 'targetAnnotationId' in data

    def test_data_to_annotation_ids_values_correct(self, v2_relation_sample):
        """data is accurately converted to annotationId, targetAnnotationId"""
        result = convert_v2_to_v1(v2_relation_sample)

        original_data = v2_relation_sample['annotation_data']['images'][0]['relation'][0]['data']
        result_data = result['annotationsData']['image_1'][0]

        assert result_data['annotationId'] == original_data[0]
        assert result_data['targetAnnotationId'] == original_data[1]

    def test_tool_field_set(self, v2_relation_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_relation_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'relation'


class TestRoundtripRelation:
    """Relation roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_annotation_ids(self, v1_relation_sample):
        """annotationId and targetAnnotationId are preserved in V1→V2→V1 conversion"""
        v2_result = convert_v1_to_v2(v1_relation_sample)
        v1_result = convert_v2_to_v1(v2_result)

        original_data = v1_relation_sample['annotationsData']['image_1'][0]
        result_data = v1_result['annotationsData']['image_1'][0]

        assert result_data['annotationId'] == original_data['annotationId']
        assert result_data['targetAnnotationId'] == original_data['targetAnnotationId']

    def test_v2_to_v1_to_v2_preserves_data(self, v2_relation_sample):
        """data is preserved in V2→V1→V2 conversion"""
        v1_result = convert_v2_to_v1(v2_relation_sample)
        v2_result = convert_v1_to_v2(v1_result)

        original_data = v2_relation_sample['annotation_data']['images'][0]['relation'][0]['data']
        result_data = v2_result['annotation_data']['images'][0]['relation'][0]['data']

        assert result_data[0] == original_data[0]
        assert result_data[1] == original_data[1]
