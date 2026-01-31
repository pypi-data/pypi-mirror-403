"""
Edge Case Tests

TDD: Tests written before implementation

Verifies edge cases such as empty data, missing required fields, invalid formats, etc.
"""

import pytest

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestV1ToV2EdgeCases:
    """V1 to V2 conversion edge cases"""

    def test_missing_annotations_raises_error(self):
        """ValueError is raised when annotations field is missing"""
        v1_data = {'annotationsData': {}}

        with pytest.raises(ValueError, match='annotations'):
            convert_v1_to_v2(v1_data)

    def test_missing_annotations_data_raises_error(self):
        """ValueError is raised when annotationsData field is missing"""
        v1_data = {'annotations': {}}

        with pytest.raises(ValueError, match='annotationsData'):
            convert_v1_to_v2(v1_data)

    def test_empty_annotations_returns_empty_result(self):
        """Empty annotations are converted successfully"""
        v1_data = {'annotations': {}, 'annotationsData': {}}

        result = convert_v1_to_v2(v1_data)

        assert 'annotation_data' in result
        assert 'annotation_meta' in result
        # media type array should not exist
        assert 'images' not in result['annotation_data']

    def test_annotation_without_tool_skipped(self):
        """Annotations without tool field are skipped"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        # no tool field
                        'classification': {'class': 'person'},
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        # no converted annotations should exist
        images = result['annotation_data'].get('images', [])
        if images:
            assert len(images[0]) == 0

    def test_mismatched_ids_handled_gracefully(self):
        """Mismatched IDs between annotations and annotationsData are handled gracefully"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_different',  # different ID
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        # when IDs don't match, converts to empty data
        bbox = result['annotation_data']['images'][0]['bounding_box'][0]
        assert bbox['id'] == 'ann_1'
        # data is default value (0, 0, 0, 0)
        assert bbox['data'] == [0, 0, 0, 0]

    def test_none_classification_handled(self):
        """None classification is handled gracefully"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': None,
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        bbox = result['annotation_data']['images'][0]['bounding_box'][0]
        assert bbox['classification'] == ''


class TestV2ToV1EdgeCases:
    """V2 to V1 conversion edge cases"""

    def test_missing_annotation_data_raises_error(self):
        """ValueError is raised when annotation_data is missing"""
        v2_data = {}

        with pytest.raises(ValueError, match='annotation_data'):
            convert_v2_to_v1(v2_data)

    def test_empty_annotation_data_raises_error(self):
        """ValueError is raised when annotation_data is empty"""
        v2_data = {'annotation_data': None}

        with pytest.raises(ValueError, match='annotation_data'):
            convert_v2_to_v1(v2_data)

    def test_empty_images_returns_empty_result(self):
        """Empty images are converted successfully"""
        v2_data = {'annotation_data': {'images': []}}

        result = convert_v2_to_v1(v2_data)

        assert 'annotations' in result
        assert 'annotationsData' in result

    def test_missing_data_field_uses_defaults(self):
        """Default values are used when data field is missing"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'bounding_box': [
                            {
                                'id': 'ann_1',
                                'classification': 'person',
                                # no data field
                                'attrs': [],
                            }
                        ]
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        coord = result['annotationsData']['image_1'][0]['coordinate']
        assert coord['x'] == 0
        assert coord['y'] == 0
        assert coord['width'] == 0
        assert coord['height'] == 0

    def test_partial_data_array_handled(self):
        """Incomplete data arrays are handled gracefully"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'bounding_box': [
                            {
                                'id': 'ann_1',
                                'classification': 'person',
                                'data': [10, 20],  # missing width, height
                                'attrs': [],
                            }
                        ]
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        coord = result['annotationsData']['image_1'][0]['coordinate']
        assert coord['x'] == 10
        assert coord['y'] == 20
        assert coord['width'] == 0
        assert coord['height'] == 0


class TestPolygonEdgeCases:
    """Polygon edge cases"""

    def test_empty_coordinate_array(self):
        """Empty coordinate arrays are handled gracefully"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'tool': 'polygon',
                        'classification': {'class': 'road'},
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'coordinate': [],  # empty array
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        polygon = result['annotation_data']['images'][0]['polygon'][0]
        assert polygon['data'] == []

    def test_single_point_polygon(self):
        """Single-point polygons are handled gracefully"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'tool': 'polygon',
                        'classification': {'class': 'point'},
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'poly_1',
                        'coordinate': [{'x': 10, 'y': 20, 'id': 'p1'}],
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        polygon = result['annotation_data']['images'][0]['polygon'][0]
        assert polygon['data'] == [[10, 20]]

    def test_v2_polygon_invalid_point_format(self):
        """Invalid point formats in V2 polygons are skipped"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'polygon': [
                            {
                                'id': 'poly_1',
                                'classification': 'road',
                                'data': [
                                    [0, 0],
                                    'invalid',  # invalid format
                                    [100, 100],
                                ],
                                'attrs': [],
                            }
                        ]
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        coord = result['annotationsData']['image_1'][0]['coordinate']
        # only valid points are converted
        assert len(coord) == 2
        assert coord[0]['x'] == 0
        assert coord[1]['x'] == 100


class TestMultipleMediaItems:
    """Multiple media items handling tests"""

    def test_multiple_images_converted(self):
        """All images are converted when multiple images exist"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    }
                ],
                'image_2': [
                    {
                        'id': 'ann_2',
                        'tool': 'bounding_box',
                        'classification': {'class': 'car'},
                    }
                ],
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ],
                'image_2': [
                    {
                        'id': 'ann_2',
                        'coordinate': {'x': 50, 'y': 50, 'width': 200, 'height': 200},
                    }
                ],
            },
        }

        result = convert_v1_to_v2(v1_data)

        # both images are converted
        assert len(result['annotation_data']['images']) == 2

    def test_video_media_type_handled(self):
        """Video media type is handled correctly"""
        v1_data = {
            'annotations': {
                'video_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    }
                ]
            },
            'annotationsData': {
                'video_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        # converted to videos array
        assert 'videos' in result['annotation_data']
        assert len(result['annotation_data']['videos']) == 1


class TestUnsupportedMediaTypeAndTool:
    """Unsupported media type and tool tests"""

    def test_unsupported_file_type_raises_error(self):
        """ValueError is raised when creating converter with unsupported file type"""
        from synapse_sdk.utils.converters.dm.from_v1 import DMV1ToV2Converter

        with pytest.raises(ValueError, match='Unsupported file type'):
            DMV1ToV2Converter(file_type='unsupported_type')

    def test_unsupported_file_type_error_message_contains_supported_types(self):
        """Error message contains list of supported types"""
        from synapse_sdk.utils.converters.dm.from_v1 import DMV1ToV2Converter

        with pytest.raises(ValueError) as exc_info:
            DMV1ToV2Converter(file_type='unknown')

        error_msg = str(exc_info.value)
        assert 'image' in error_msg
        assert 'video' in error_msg
        assert 'pcd' in error_msg

    def test_unsupported_tool_raises_error_v1_to_v2(self):
        """V1 to V2: ValueError is raised for unsupported tools"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_unsupported',
                        'tool': 'unknown_tool',  # unsupported tool
                        'classification': {'class': 'unknown'},
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_unsupported',
                        'some_data': 'value',
                    },
                ]
            },
        }

        with pytest.raises(ValueError, match="Unsupported tool: 'unknown_tool'"):
            convert_v1_to_v2(v1_data)

    def test_unsupported_tool_error_message_contains_supported_tools(self):
        """V1 to V2: Error message contains list of supported tools"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'custom_tool',
                        'classification': {'class': 'test'},
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {'id': 'ann_1', 'data': 'value'},
                ]
            },
        }

        with pytest.raises(ValueError) as exc_info:
            convert_v1_to_v2(v1_data)

        error_msg = str(exc_info.value)
        assert 'bounding_box' in error_msg
        assert 'polygon' in error_msg
        assert 'Supported tools:' in error_msg

    def test_unsupported_tool_silently_skipped_v2_to_v1(self):
        """V2 to V1: Unsupported tools are silently skipped"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'bounding_box': [
                            {
                                'id': 'ann_supported',
                                'classification': 'person',
                                'attrs': [],
                                'data': [10, 20, 100, 50],
                            }
                        ],
                        'unknown_tool': [  # unsupported tool
                            {
                                'id': 'ann_unsupported',
                                'classification': 'unknown',
                                'attrs': [],
                                'data': {'some': 'data'},
                            }
                        ],
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        # only bounding_box is converted
        assert len(result['annotations']['image_1']) == 1
        assert result['annotations']['image_1'][0]['tool'] == 'bounding_box'

    def test_all_unsupported_tools_raises_error(self):
        """ValueError is raised when all tools are unsupported"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'unsupported_tool_1',
                        'classification': {'class': 'unknown'},
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {'id': 'ann_1', 'data': 'value1'},
                ]
            },
        }

        with pytest.raises(ValueError, match="Unsupported tool: 'unsupported_tool_1'"):
            convert_v1_to_v2(v1_data)

    def test_mixed_supported_unsupported_tools_raises_error(self):
        """ValueError is raised when mixed with supported and unsupported tools"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {'id': 'bbox_1', 'tool': 'bounding_box', 'classification': {'class': 'a'}},
                    {'id': 'unk_1', 'tool': 'unknown', 'classification': {'class': 'b'}},
                ]
            },
            'annotationsData': {
                'image_1': [
                    {'id': 'bbox_1', 'coordinate': {'x': 0, 'y': 0, 'width': 10, 'height': 10}},
                    {'id': 'unk_1', 'data': 'unknown'},
                ]
            },
        }

        with pytest.raises(ValueError, match="Unsupported tool: 'unknown'"):
            convert_v1_to_v2(v1_data)

    def test_unknown_media_type_prefix_raises_error(self):
        """ValueError is raised for unknown media type prefix"""
        v1_data = {
            'annotations': {
                'custom_1': [  # unknown media type
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    }
                ]
            },
            'annotationsData': {
                'custom_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        with pytest.raises(ValueError, match='Unknown media type'):
            convert_v1_to_v2(v1_data)

    def test_unknown_media_type_error_message_contains_media_id(self):
        """Error message contains the problematic media ID"""
        v1_data = {
            'annotations': {
                'unknown_media_123': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    }
                ]
            },
            'annotationsData': {
                'unknown_media_123': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        with pytest.raises(ValueError) as exc_info:
            convert_v1_to_v2(v1_data)

        error_msg = str(exc_info.value)
        assert 'unknown_media_123' in error_msg
