"""
Classification Conversion Tests

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2Classification:
    """V1 to V2 classification conversion tests"""

    def test_basic_conversion_returns_split_result(self, v1_classification_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_classification_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_classification_to_attrs(self, v1_classification_sample):
        """classification properties are converted to attrs"""
        result = convert_v1_to_v2(v1_classification_sample)
        annotation_data = result['annotation_data']

        cls_list = annotation_data['images'][0].get('classification', [])
        assert len(cls_list) > 0

        cls = cls_list[0]
        assert 'attrs' in cls
        assert 'data' in cls
        assert cls['data'] == {}  # empty object

    def test_classification_class_extracted(self, v1_classification_sample):
        """classification.class is extracted as V2 classification"""
        result = convert_v1_to_v2(v1_classification_sample)
        annotation_data = result['annotation_data']

        cls = annotation_data['images'][0]['classification'][0]
        original_class = v1_classification_sample['annotations']['image_1'][0]['classification']['class']

        assert cls['classification'] == original_class

    def test_other_props_to_attrs(self, v1_classification_sample):
        """other classification properties are converted to attrs"""
        result = convert_v1_to_v2(v1_classification_sample)
        annotation_data = result['annotation_data']

        cls = annotation_data['images'][0]['classification'][0]
        attrs = cls['attrs']

        # weather, time_of_day should be in attrs
        attr_names = {attr['name'] for attr in attrs}
        assert 'weather' in attr_names
        assert 'time_of_day' in attr_names

    def test_id_preserved(self, v1_classification_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_classification_sample)
        annotation_data = result['annotation_data']

        cls = annotation_data['images'][0]['classification'][0]
        original_id = v1_classification_sample['annotations']['image_1'][0]['id']

        assert cls['id'] == original_id


class TestV2ToV1Classification:
    """V2 to V1 classification conversion tests"""

    def test_complete_conversion_with_meta(self, v2_classification_sample):
        """Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_classification_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']

    def test_attrs_to_classification(self, v2_classification_sample):
        """attrs are restored to classification"""
        result = convert_v2_to_v1(v2_classification_sample)

        ann = result['annotations']['image_1'][0]
        original_attrs = v2_classification_sample['annotation_data']['images'][0]['classification'][0]['attrs']

        for attr in original_attrs:
            name = attr['name']
            value = attr['value']
            if not name.startswith('_'):
                assert ann['classification'].get(name) == value

    def test_tool_field_set(self, v2_classification_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_classification_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'classification'

    def test_annotationsData_has_only_id(self, v2_classification_sample):
        """annotationsData contains only id"""
        result = convert_v2_to_v1(v2_classification_sample)

        data = result['annotationsData']['image_1'][0]
        assert 'id' in data


class TestRoundtripClassification:
    """Classification roundtrip conversion tests"""

    def test_v1_to_v2_to_v1_preserves_classification(self, v1_classification_sample):
        """classification is preserved in V1→V2→V1 conversion"""
        v2_result = convert_v1_to_v2(v1_classification_sample)
        v1_result = convert_v2_to_v1(v2_result)

        original_cls = v1_classification_sample['annotations']['image_1'][0]['classification']
        result_cls = v1_result['annotations']['image_1'][0]['classification']

        assert result_cls['class'] == original_cls['class']
        assert result_cls.get('weather') == original_cls.get('weather')

    def test_v2_to_v1_to_v2_preserves_attrs(self, v2_classification_sample):
        """attrs is preserved in V2→V1→V2 conversion"""
        v1_result = convert_v2_to_v1(v2_classification_sample)
        v2_result = convert_v1_to_v2(v1_result)

        original_cls = v2_classification_sample['annotation_data']['images'][0]['classification'][0]
        result_cls = v2_result['annotation_data']['images'][0]['classification'][0]

        assert result_cls['classification'] == original_cls['classification']
