"""
Segmentation Conversion Tests (Image/Video)

TDD: Tests written before implementation
"""

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2ImageSegmentation:
    """V1 to V2 image segmentation conversion tests (US9)"""

    def test_basic_conversion_returns_split_result(self, v1_image_segmentation_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_image_segmentation_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_pixel_indices_to_data(self, v1_image_segmentation_sample):
        """US9 scenario 1: pixel_indices → data conversion"""
        result = convert_v1_to_v2(v1_image_segmentation_sample)
        annotation_data = result['annotation_data']

        # check segmentation array
        seg_list = annotation_data['images'][0].get('segmentation', [])
        assert len(seg_list) > 0

        seg = seg_list[0]
        data = seg.get('data', [])

        # check if data is array
        assert isinstance(data, list)
        assert len(data) > 0

    def test_pixel_indices_values_correct(self, v1_image_segmentation_sample):
        """US9 scenario 2: pixel_indices values are converted accurately"""
        result = convert_v1_to_v2(v1_image_segmentation_sample)
        annotation_data = result['annotation_data']

        original_pixels = v1_image_segmentation_sample['annotationsData']['image_1'][0]['pixel_indices']
        seg = annotation_data['images'][0]['segmentation'][0]
        data = seg['data']

        # values match
        assert data == original_pixels

    def test_id_preserved(self, v1_image_segmentation_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_image_segmentation_sample)
        annotation_data = result['annotation_data']

        seg = annotation_data['images'][0]['segmentation'][0]
        original_id = v1_image_segmentation_sample['annotations']['image_1'][0]['id']

        assert seg['id'] == original_id

    def test_classification_extracted_correctly(self, v1_image_segmentation_sample):
        """classification.class is extracted as V2 classification"""
        result = convert_v1_to_v2(v1_image_segmentation_sample)
        annotation_data = result['annotation_data']

        seg = annotation_data['images'][0]['segmentation'][0]
        original_class = v1_image_segmentation_sample['annotations']['image_1'][0]['classification']['class']

        assert seg['classification'] == original_class


class TestV2ToV1ImageSegmentation:
    """V2 to V1 image segmentation conversion tests (US9)"""

    def test_complete_conversion_with_meta(self, v2_image_segmentation_sample):
        """US9 scenario 2: Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_image_segmentation_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'image_1' in result['annotations']

        # check if pixel_indices is array
        pixel_indices = result['annotationsData']['image_1'][0]['pixel_indices']
        assert isinstance(pixel_indices, list)

    def test_data_to_pixel_indices_values_correct(self, v2_image_segmentation_sample):
        """US9 scenario 3: data values are converted accurately to pixel_indices"""
        result = convert_v2_to_v1(v2_image_segmentation_sample)

        original_data = v2_image_segmentation_sample['annotation_data']['images'][0]['segmentation'][0]['data']
        pixel_indices = result['annotationsData']['image_1'][0]['pixel_indices']

        # values match
        assert pixel_indices == original_data

    def test_tool_field_set(self, v2_image_segmentation_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_image_segmentation_sample)

        ann = result['annotations']['image_1'][0]
        assert ann['tool'] == 'segmentation'


class TestV1ToV2VideoSegmentation:
    """V1 to V2 video segmentation conversion tests (US10)"""

    def test_basic_conversion_returns_split_result(self, v1_video_segmentation_sample):
        """Conversion result is split into annotation_data and annotation_meta"""
        result = convert_v1_to_v2(v1_video_segmentation_sample)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result

    def test_section_to_data(self, v1_video_segmentation_sample):
        """US10 scenario 1: section → data conversion"""
        result = convert_v1_to_v2(v1_video_segmentation_sample)
        annotation_data = result['annotation_data']

        # check segmentation array (videos media type)
        seg_list = annotation_data['videos'][0].get('segmentation', [])
        assert len(seg_list) > 0

        seg = seg_list[0]
        data = seg.get('data', {})

        # data contains startFrame, endFrame
        assert 'startFrame' in data
        assert 'endFrame' in data

    def test_section_values_correct(self, v1_video_segmentation_sample):
        """US10 scenario 2: section values are converted accurately"""
        result = convert_v1_to_v2(v1_video_segmentation_sample)
        annotation_data = result['annotation_data']

        original_section = v1_video_segmentation_sample['annotationsData']['video_1'][0]['section']
        seg = annotation_data['videos'][0]['segmentation'][0]
        data = seg['data']

        # values match
        assert data['startFrame'] == original_section['startFrame']
        assert data['endFrame'] == original_section['endFrame']

    def test_id_preserved(self, v1_video_segmentation_sample):
        """Annotation ID is preserved"""
        result = convert_v1_to_v2(v1_video_segmentation_sample)
        annotation_data = result['annotation_data']

        seg = annotation_data['videos'][0]['segmentation'][0]
        original_id = v1_video_segmentation_sample['annotations']['video_1'][0]['id']

        assert seg['id'] == original_id


class TestV2ToV1VideoSegmentation:
    """V2 to V1 video segmentation conversion tests (US10)"""

    def test_complete_conversion_with_meta(self, v2_video_segmentation_sample):
        """US10 scenario 2: Complete V1 conversion from annotation_data + annotation_meta"""
        result = convert_v2_to_v1(v2_video_segmentation_sample)

        assert 'annotations' in result
        assert 'annotationsData' in result
        assert 'video_1' in result['annotations']

        # verify section is in {startFrame, endFrame} format
        section = result['annotationsData']['video_1'][0]['section']
        assert isinstance(section, dict)
        assert 'startFrame' in section
        assert 'endFrame' in section

    def test_data_to_section_values_correct(self, v2_video_segmentation_sample):
        """US10 scenario 3: data values are converted accurately to section"""
        result = convert_v2_to_v1(v2_video_segmentation_sample)

        original_data = v2_video_segmentation_sample['annotation_data']['videos'][0]['segmentation'][0]['data']
        section = result['annotationsData']['video_1'][0]['section']

        # values match
        assert section['startFrame'] == original_data['startFrame']
        assert section['endFrame'] == original_data['endFrame']

    def test_tool_field_set(self, v2_video_segmentation_sample):
        """tool field is set in V1 annotation"""
        result = convert_v2_to_v1(v2_video_segmentation_sample)

        ann = result['annotations']['video_1'][0]
        assert ann['tool'] == 'segmentation'


class TestRoundtripSegmentation:
    """Segmentation roundtrip conversion tests"""

    def test_image_v1_to_v2_to_v1_preserves_pixel_indices(self, v1_image_segmentation_sample):
        """pixel_indices is preserved in V1→V2→V1 conversion"""
        # V1 → V2
        v2_result = convert_v1_to_v2(v1_image_segmentation_sample)

        # V2 → V1
        v1_result = convert_v2_to_v1(v2_result)

        # compare original and result
        original_pixels = v1_image_segmentation_sample['annotationsData']['image_1'][0]['pixel_indices']
        result_pixels = v1_result['annotationsData']['image_1'][0]['pixel_indices']

        assert result_pixels == original_pixels

    def test_video_v1_to_v2_to_v1_preserves_section(self, v1_video_segmentation_sample):
        """section is preserved in V1→V2→V1 conversion"""
        # V1 → V2
        v2_result = convert_v1_to_v2(v1_video_segmentation_sample)

        # V2 → V1
        v1_result = convert_v2_to_v1(v2_result)

        # compare original and result
        original_section = v1_video_segmentation_sample['annotationsData']['video_1'][0]['section']
        result_section = v1_result['annotationsData']['video_1'][0]['section']

        assert result_section['startFrame'] == original_section['startFrame']
        assert result_section['endFrame'] == original_section['endFrame']

    def test_image_v2_to_v1_to_v2_preserves_data(self, v2_image_segmentation_sample):
        """data is preserved in V2→V1→V2 conversion"""
        # V2 → V1
        v1_result = convert_v2_to_v1(v2_image_segmentation_sample)

        # V1 → V2
        v2_result = convert_v1_to_v2(v1_result)

        # compare original and result
        original_data = v2_image_segmentation_sample['annotation_data']['images'][0]['segmentation'][0]['data']
        result_data = v2_result['annotation_data']['images'][0]['segmentation'][0]['data']

        assert result_data == original_data

    def test_video_v2_to_v1_to_v2_preserves_data(self, v2_video_segmentation_sample):
        """data is preserved in V2→V1→V2 conversion"""
        # V2 → V1
        v1_result = convert_v2_to_v1(v2_video_segmentation_sample)

        # V1 → V2
        v2_result = convert_v1_to_v2(v1_result)

        # compare original and result
        original_data = v2_video_segmentation_sample['annotation_data']['videos'][0]['segmentation'][0]['data']
        result_data = v2_result['annotation_data']['videos'][0]['segmentation'][0]['data']

        assert result_data['startFrame'] == original_data['startFrame']
        assert result_data['endFrame'] == original_data['endFrame']
