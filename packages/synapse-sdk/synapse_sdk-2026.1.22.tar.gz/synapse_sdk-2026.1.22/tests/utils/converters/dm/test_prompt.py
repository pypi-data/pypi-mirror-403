"""
Prompt Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Prompt:
    """V1 to V2 prompt conversion tests"""

    def test_basic_conversion_returns_split_result(self, v1_prompt_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_prompt_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_input_to_data(self, v1_prompt_sample):
        """input → data.input conversion"""
        result = convert_v1_to_v2(v1_prompt_sample)
        annotation_data = result['annotation_data']

        prompt_list = annotation_data['prompts'][0].get('prompt', [])
        assert len(prompt_list) > 0

        prompt = prompt_list[0]
        data = prompt.get('data', {})

        assert 'input' in data

    def test_input_values_correct(self, v1_prompt_sample):
        """input value is converted accurately"""
        result = convert_v1_to_v2(v1_prompt_sample)
        annotation_data = result['annotation_data']

        original_input = v1_prompt_sample['annotationsData']['prompt_1'][0]['input']
        prompt = annotation_data['prompts'][0]['prompt'][0]
        result_input = prompt['data']['input']

        assert result_input == original_input

    def test_id_preserved(self, v1_prompt_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_prompt_sample)
        annotation_data = result['annotation_data']

        prompt = annotation_data['prompts'][0]['prompt'][0]
        original_id = v1_prompt_sample['annotations']['prompt_1'][0]['id']

        assert prompt['id'] == original_id


class TestV2ToV1Prompt:
    """V2 to V1 prompt conversion tests"""

    def test_complete_conversion_with_meta(self, v2_prompt_sample):
        """Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_prompt_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'prompt_1' in result['annotations']

        data = result['annotationsData']['prompt_1'][0]
        assert 'input' in data

    def test_data_to_input_values_correct(self, v2_prompt_sample):
        """data.input is accurately converted to input"""
        result = convert_v2_to_v1(v2_prompt_sample)

        original_input = v2_prompt_sample['annotation_data']['prompts'][0]['prompt'][0]['data']['input']
        result_data = result['annotationsData']['prompt_1'][0]

        assert result_data['input'] == original_input

    def test_tool_field_set(self, v2_prompt_sample):
        """tool field is set in V1 annotationsData"""
        result = convert_v2_to_v1(v2_prompt_sample)

        data = result['annotationsData']['prompt_1'][0]
        assert data['tool'] == 'prompt'


class TestRoundtripPrompt:
    """Prompt roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_input(self, v1_prompt_sample):
        """input is preserved in V1→V2→V1 conversion"""
        v2_result = convert_v1_to_v2(v1_prompt_sample)
        v1_result = convert_v2_to_v1(v2_result)

        original_input = v1_prompt_sample['annotationsData']['prompt_1'][0]['input']
        result_input = v1_result['annotationsData']['prompt_1'][0]['input']

        assert result_input == original_input

    def test_v2_to_v1_to_v2_preserves_data(self, v2_prompt_sample):
        """data is preserved in V2→V1→V2 conversion"""
        v1_result = convert_v2_to_v1(v2_prompt_sample)
        v2_result = convert_v1_to_v2(v1_result)

        original_data = v2_prompt_sample['annotation_data']['prompts'][0]['prompt'][0]['data']
        result_data = v2_result['annotation_data']['prompts'][0]['prompt'][0]['data']

        assert result_data['input'] == original_data['input']
