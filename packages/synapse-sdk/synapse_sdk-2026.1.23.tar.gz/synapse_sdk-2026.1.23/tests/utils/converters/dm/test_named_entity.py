"""
Named Entity Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2NamedEntity:
    """V1 to V2 named entity conversion tests (US11)"""

    def test_basic_conversion_returns_split_result(self, v1_named_entity_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_named_entity_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_ranges_and_content_to_data(self, v1_named_entity_sample):
        """US11 scenario 1: ranges, content → data conversion"""
        result = convert_v1_to_v2(v1_named_entity_sample)
        annotation_data = result['annotation_data']

        # check named_entity array (texts media type)
        ne_list = annotation_data['texts'][0].get('named_entity', [])
        assert len(ne_list) > 0

        ne = ne_list[0]
        data = ne.get('data', {})

        # data contains ranges, content
        assert 'ranges' in data
        assert 'content' in data

    def test_data_values_correct(self, v1_named_entity_sample):
        """US11 scenario 2: ranges and content values are converted accurately"""
        result = convert_v1_to_v2(v1_named_entity_sample)
        annotation_data = result['annotation_data']

        original_data = v1_named_entity_sample['annotationsData']['text_1'][0]
        ne = annotation_data['texts'][0]['named_entity'][0]
        data = ne['data']

        # values match
        assert data['ranges'] == original_data['ranges']
        assert data['content'] == original_data['content']

    def test_id_preserved(self, v1_named_entity_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_named_entity_sample)
        annotation_data = result['annotation_data']

        ne = annotation_data['texts'][0]['named_entity'][0]
        original_id = v1_named_entity_sample['annotations']['text_1'][0]['id']

        assert ne['id'] == original_id

    def test_classification_extracted_correctly(self, v1_named_entity_sample):
        """classification.class is extracted as V2 classification"""
        result = convert_v1_to_v2(v1_named_entity_sample)
        annotation_data = result['annotation_data']

        ne = annotation_data['texts'][0]['named_entity'][0]
        original_class = v1_named_entity_sample['annotations']['text_1'][0]['classification']['class']

        assert ne['classification'] == original_class


class TestV2ToV1NamedEntity:
    """V2 to V1 named entity conversion tests (US11)"""

    def test_complete_conversion_with_meta(self, v2_named_entity_sample):
        """US11 scenario 2: Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_named_entity_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'text_1' in result['annotations']

        # check if ranges, content exist
        data = result['annotationsData']['text_1'][0]
        assert 'ranges' in data
        assert 'content' in data

    def test_data_to_ranges_content_values_correct(self, v2_named_entity_sample):
        """US11 scenario 3: data is converted accurately to ranges and content"""
        result = convert_v2_to_v1(v2_named_entity_sample)

        original_data = v2_named_entity_sample['annotation_data']['texts'][0]['named_entity'][0]['data']
        result_data = result['annotationsData']['text_1'][0]

        # values match
        assert result_data['ranges'] == original_data['ranges']
        assert result_data['content'] == original_data['content']

    def test_tool_field_set(self, v2_named_entity_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_named_entity_sample)

        ann = result['annotations']['text_1'][0]
        assert ann['tool'] == 'named_entity'

    def test_classification_restored(self, v2_named_entity_sample):
        """V2 classification is restored to V1 classification.class"""
        result = convert_v2_to_v1(v2_named_entity_sample)

        ann = result['annotations']['text_1'][0]
        original_class = v2_named_entity_sample['annotation_data']['texts'][0]['named_entity'][0]['classification']

        assert ann['classification']['class'] == original_class


class TestRoundtripNamedEntity:
    """Named entity roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_data(self, v1_named_entity_sample):
        """ranges and content are preserved in V1→V2→V1 conversion"""
        # V1 → V2
        v2_result = convert_v1_to_v2(v1_named_entity_sample)

        # V2 → V1
        v1_result = convert_v2_to_v1(v2_result)

        # compare original and result
        original_data = v1_named_entity_sample['annotationsData']['text_1'][0]
        result_data = v1_result['annotationsData']['text_1'][0]

        assert result_data['ranges'] == original_data['ranges']
        assert result_data['content'] == original_data['content']

    def test_v2_to_v1_to_v2_preserves_data(self, v2_named_entity_sample):
        """data is preserved in V2→V1→V2 conversion"""
        # V2 → V1
        v1_result = convert_v2_to_v1(v2_named_entity_sample)

        # V1 → V2
        v2_result = convert_v1_to_v2(v1_result)

        # compare original and result
        original_data = v2_named_entity_sample['annotation_data']['texts'][0]['named_entity'][0]['data']
        result_data = v2_result['annotation_data']['texts'][0]['named_entity'][0]['data']

        assert result_data['ranges'] == original_data['ranges']
        assert result_data['content'] == original_data['content']
