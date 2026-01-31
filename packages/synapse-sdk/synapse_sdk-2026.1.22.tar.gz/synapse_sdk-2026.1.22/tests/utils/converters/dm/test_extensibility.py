"""
Extensibility Tests

TDD: Tests written before implementation

Verifies that ToolProcessor protocol and processor registration patterns work correctly.
"""

from typing import Any

import pytest

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1
from synapse_sdk.utils.converters.dm.from_v1 import DMV1ToV2Converter


class MockCustomProcessor:
    """Custom processor for testing"""

    tool_name = 'custom_tool'

    def to_v2(self, v1_annotation: dict[str, Any], v1_data: dict[str, Any]) -> dict[str, Any]:
        return {
            'id': v1_annotation.get('id', ''),
            'classification': v1_annotation.get('classification', {}).get('class', ''),
            'attrs': [],
            'data': v1_data.get('coordinate', {}),
            'custom_field': 'from_mock',
        }

    def to_v1(self, v2_annotation: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        return (
            {
                'id': v2_annotation.get('id', ''),
                'tool': self.tool_name,
                'classification': {'class': v2_annotation.get('classification', '')},
            },
            {
                'id': v2_annotation.get('id', ''),
                'coordinate': v2_annotation.get('data', {}),
            },
        )


class TestToolProcessorRegistry:
    """US6: ToolProcessor protocol tests"""

    def test_builtin_processors_registered(self):
        """Built-in processors are registered automatically"""
        converter = DMV1ToV2Converter()

        assert converter.get_processor('bounding_box') is not None
        assert converter.get_processor('polygon') is not None

    def test_unknown_tool_returns_none(self):
        """Unregistered tools return None"""
        converter = DMV1ToV2Converter()

        assert converter.get_processor('unknown_tool') is None

    def test_custom_processor_can_be_registered(self):
        """Custom processors can be registered"""
        converter = DMV1ToV2Converter()
        custom_processor = MockCustomProcessor()

        converter.register_processor(custom_processor)

        assert converter.get_processor('custom_tool') is custom_processor

    def test_custom_processor_used_in_conversion(self):
        """Registered custom processors are used in conversion"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'custom_1',
                        'tool': 'custom_tool',
                        'classification': {'class': 'test_class'},
                    }
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'custom_1',
                        'coordinate': {'custom_x': 10, 'custom_y': 20},
                    }
                ]
            },
        }

        converter = DMV1ToV2Converter()
        converter.register_processor(MockCustomProcessor())

        result = converter.convert(v1_data)

        # verify custom processor result
        custom_ann = result['annotation_data']['images'][0]['custom_tool'][0]
        assert custom_ann['custom_field'] == 'from_mock'
        assert custom_ann['data'] == {'custom_x': 10, 'custom_y': 20}


class TestUnsupportedToolHandling:
    """Unsupported tool handling tests"""

    def test_unsupported_tool_raises_error_in_v1_to_v2(self):
        """ValueError is raised for unsupported tools during V1 to V2 conversion"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'tool': 'unsupported_tool',  # unsupported tool
                        'classification': {'class': 'unknown'},
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'ann_1',
                        'coordinate': {'unsupported': 'data'},
                    },
                ]
            },
        }

        with pytest.raises(ValueError, match="Unsupported tool: 'unsupported_tool'"):
            convert_v1_to_v2(v1_data)

    def test_unsupported_tool_skipped_in_v2_to_v1(self):
        """Unsupported tools are skipped during V2 to V1 conversion"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'bounding_box': [
                            {
                                'id': 'ann_1',
                                'classification': 'person',
                                'data': [0, 0, 100, 100],
                                'attrs': [],
                            }
                        ],
                        'unsupported_tool': [
                            {
                                'id': 'ann_2',
                                'classification': 'unknown',
                                'data': {'unsupported': 'data'},
                                'attrs': [],
                            }
                        ],
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        # only bounding_box is converted
        ann_ids = [ann['id'] for ann in result['annotations']['image_1']]
        assert 'ann_1' in ann_ids
        assert 'ann_2' not in ann_ids


class TestMultipleToolConversion:
    """Mixed tool data conversion tests"""

    def test_mixed_tools_v1_to_v2(self):
        """V1 to V2: Conversion with both bounding_box and polygon"""
        v1_data = {
            'annotations': {
                'image_1': [
                    {
                        'id': 'bbox_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'person'},
                    },
                    {
                        'id': 'poly_1',
                        'tool': 'polygon',
                        'classification': {'class': 'road'},
                    },
                ]
            },
            'annotationsData': {
                'image_1': [
                    {
                        'id': 'bbox_1',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    },
                    {
                        'id': 'poly_1',
                        'coordinate': [
                            {'x': 0, 'y': 0, 'id': 'p1'},
                            {'x': 100, 'y': 0, 'id': 'p2'},
                            {'x': 50, 'y': 100, 'id': 'p3'},
                        ],
                    },
                ]
            },
        }

        result = convert_v1_to_v2(v1_data)

        # both tools are converted
        images = result['annotation_data']['images'][0]
        assert 'bounding_box' in images
        assert 'polygon' in images
        assert len(images['bounding_box']) == 1
        assert len(images['polygon']) == 1

    def test_mixed_tools_v2_to_v1(self):
        """V2 to V1: Conversion with both bounding_box and polygon"""
        v2_data = {
            'annotation_data': {
                'images': [
                    {
                        'bounding_box': [
                            {
                                'id': 'bbox_1',
                                'classification': 'person',
                                'data': [0, 0, 100, 100],
                                'attrs': [],
                            }
                        ],
                        'polygon': [
                            {
                                'id': 'poly_1',
                                'classification': 'road',
                                'data': [[0, 0], [100, 0], [50, 100]],
                                'attrs': [],
                            }
                        ],
                    }
                ]
            }
        }

        result = convert_v2_to_v1(v2_data)

        # both tools are converted
        assert len(result['annotations']['image_1']) == 2
        assert len(result['annotationsData']['image_1']) == 2

        # verify each tool
        tools = {ann['tool'] for ann in result['annotations']['image_1']}
        assert 'bounding_box' in tools
        assert 'polygon' in tools
