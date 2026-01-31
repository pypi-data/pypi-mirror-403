"""
Answer Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Answer:
    """V1 to V2 answer conversion tests"""

    def test_basic_conversion_returns_split_result(self, v1_answer_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_answer_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_output_to_data(self, v1_answer_sample):
        """output → data.output conversion"""
        result = convert_v1_to_v2(v1_answer_sample)
        annotation_data = result['annotation_data']

        answer_list = annotation_data['prompts'][0].get('answer', [])
        assert len(answer_list) > 0

        answer = answer_list[0]
        data = answer.get('data', {})

        assert 'output' in data

    def test_output_values_correct(self, v1_answer_sample):
        """output value is converted accurately"""
        result = convert_v1_to_v2(v1_answer_sample)
        annotation_data = result['annotation_data']

        original_output = v1_answer_sample['annotationsData']['prompt_1'][0]['output']
        answer = annotation_data['prompts'][0]['answer'][0]
        result_output = answer['data']['output']

        assert result_output == original_output

    def test_extra_fields_preserved(self, v1_answer_sample):
        """model, displayName, generatedBy, promptAnnotationId are preserved"""
        result = convert_v1_to_v2(v1_answer_sample)
        annotation_data = result['annotation_data']

        original_data = v1_answer_sample['annotationsData']['prompt_1'][0]
        answer = annotation_data['prompts'][0]['answer'][0]
        data = answer['data']

        assert data['model'] == original_data['model']
        assert data['displayName'] == original_data['displayName']
        assert data['generatedBy'] == original_data['generatedBy']
        assert data['promptAnnotationId'] == original_data['promptAnnotationId']

    def test_id_preserved(self, v1_answer_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_answer_sample)
        annotation_data = result['annotation_data']

        answer = annotation_data['prompts'][0]['answer'][0]
        original_id = v1_answer_sample['annotations']['prompt_1'][0]['id']

        assert answer['id'] == original_id


class TestV2ToV1Answer:
    """V2 to V1 answer conversion tests"""

    def test_complete_conversion_with_meta(self, v2_answer_sample):
        """Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_answer_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'prompt_1' in result['annotations']

        data = result['annotationsData']['prompt_1'][0]
        assert 'output' in data

    def test_data_to_output_values_correct(self, v2_answer_sample):
        """data.output is accurately converted to output"""
        result = convert_v2_to_v1(v2_answer_sample)

        original_output = v2_answer_sample['annotation_data']['prompts'][0]['answer'][0]['data']['output']
        result_data = result['annotationsData']['prompt_1'][0]

        assert result_data['output'] == original_output

    def test_tool_field_set(self, v2_answer_sample):
        """tool field is set in V1 annotationsData"""
        result = convert_v2_to_v1(v2_answer_sample)

        data = result['annotationsData']['prompt_1'][0]
        assert data['tool'] == 'answer'


class TestRoundtripAnswer:
    """Answer roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_output(self, v1_answer_sample):
        """output is preserved in V1→V2→V1 conversion"""
        v2_result = convert_v1_to_v2(v1_answer_sample)
        v1_result = convert_v2_to_v1(v2_result)

        original_output = v1_answer_sample['annotationsData']['prompt_1'][0]['output']
        result_output = v1_result['annotationsData']['prompt_1'][0]['output']

        assert result_output == original_output

    def test_v2_to_v1_to_v2_preserves_data(self, v2_answer_sample):
        """data is preserved in V2→V1→V2 conversion"""
        v1_result = convert_v2_to_v1(v2_answer_sample)
        v2_result = convert_v1_to_v2(v1_result)

        original_data = v2_answer_sample['annotation_data']['prompts'][0]['answer'][0]['data']
        result_data = v2_result['annotation_data']['prompts'][0]['answer'][0]['data']

        assert result_data['output'] == original_data['output']
        assert result_data['model'] == original_data['model']
        assert result_data['promptAnnotationId'] == original_data['promptAnnotationId']
