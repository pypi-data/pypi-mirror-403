"""Tests for DatasetAction class and its key methods."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from synapse_sdk.plugins.actions.dataset.action import DatasetAction

# -----------------------------------------------------------------------------
# Test _build_dm_json
# -----------------------------------------------------------------------------


class TestBuildDmJson:
    """Tests for DatasetAction._build_dm_json method."""

    def test_build_dm_json_from_annotation_json(self, sample_annotation_json):
        """Parse annotation JSON with annotations/annotationsData structure."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, sample_annotation_json)

        # Should have classification from annotations
        assert 'classification' in result
        assert 'images' in result
        assert len(result['images']) == 1

        # Check bounding box was extracted
        img_ann = result['images'][0]
        assert 'bounding_box' in img_ann
        assert len(img_ann['bounding_box']) == 1

        bbox = img_ann['bounding_box'][0]
        assert bbox['classification'] == 'WO-04'
        assert bbox['x'] == 382
        assert bbox['y'] == 410
        assert bbox['width'] == 399
        assert bbox['height'] == 381

    def test_build_dm_json_fallback_to_event_data(self):
        """Fallback when no annotation_json provided - use event['data']['annotations']."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        event = {
            'id': 1,
            'files': {},
            'data': {
                'annotations': {
                    'image': [
                        {
                            'id': 'ann_1',
                            'tool': 'bounding_box',
                            'classification': {'class': 'car'},
                        }
                    ]
                }
            },
        }

        result = action._build_dm_json(event, annotation_json=None)

        assert 'images' in result
        img_ann = result['images'][0]
        # Should have an annotation (though without coordinate data since it's not in annotationsData)
        assert 'bounding_box' in img_ann
        assert len(img_ann['bounding_box']) == 1
        assert img_ann['bounding_box'][0]['classification'] == 'car'

    def test_build_dm_json_bounding_box_coordinates(self, sample_annotation_json):
        """Verify correct x, y, width, height extraction from coordinate field."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, sample_annotation_json)

        bbox = result['images'][0]['bounding_box'][0]
        assert bbox['x'] == 382
        assert bbox['y'] == 410
        assert bbox['width'] == 399
        assert bbox['height'] == 381

    def test_build_dm_json_polygon_points(self, sample_annotation_json):
        """Polygon points extraction from coordinate.points."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, sample_annotation_json)

        img_ann = result['images'][0]
        assert 'polygon' in img_ann
        assert len(img_ann['polygon']) == 1

        poly = img_ann['polygon'][0]
        assert poly['classification'] == 'crack'
        assert poly['points'] == [[100, 100], [200, 100], [200, 200], [100, 200]]

    def test_build_dm_json_nested_classification(self):
        """Classification extracted from nested {"class": "car"} structure."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        annotation_json = {
            'annotations': {
                'image': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': {'class': 'car'},
                    }
                ]
            },
            'annotationsData': {
                'image': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'coordinate': {'x': 0, 'y': 0, 'width': 100, 'height': 100},
                    }
                ]
            },
        }

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, annotation_json)

        bbox = result['images'][0]['bounding_box'][0]
        assert bbox['classification'] == 'car'

    def test_build_dm_json_flat_classification(self):
        """Classification from string value (flat format)."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        annotation_json = {
            'annotations': {
                'image': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'classification': 'vehicle',  # Flat string
                    }
                ]
            },
            'annotationsData': {
                'image': [
                    {
                        'id': 'ann_1',
                        'tool': 'bounding_box',
                        'coordinate': {'x': 10, 'y': 20, 'width': 50, 'height': 60},
                    }
                ]
            },
        }

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, annotation_json)

        bbox = result['images'][0]['bounding_box'][0]
        assert bbox['classification'] == 'vehicle'

    def test_build_dm_json_empty_annotations(self):
        """Handle empty annotations gracefully."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        annotation_json = {
            'annotations': {'image': []},
            'annotationsData': {'image': []},
        }

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, annotation_json)

        assert 'images' in result
        assert len(result['images']) == 1
        img_ann = result['images'][0]
        assert img_ann['bounding_box'] == []
        assert img_ann['polygon'] == []

    def test_build_dm_json_missing_annotation_data_lookup(self):
        """Handle missing annotationsData for an annotation ID."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        annotation_json = {
            'annotations': {
                'image': [
                    {
                        'id': 'ann_missing',  # No matching entry in annotationsData
                        'tool': 'bounding_box',
                        'classification': {'class': 'box'},
                    }
                ]
            },
            'annotationsData': {
                'image': []  # Empty - no matching data
            },
        }

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, annotation_json)

        # Should still create annotation but without coordinate data
        bbox = result['images'][0]['bounding_box'][0]
        assert bbox['classification'] == 'box'
        # No x, y, width, height since coordinate data wasn't found
        assert 'x' not in bbox or bbox.get('x') == 0

    def test_build_dm_json_multiple_tool_types(self):
        """Handle multiple annotation tool types in single JSON."""
        action = MagicMock(spec=DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

        annotation_json = {
            'annotations': {
                'image': [
                    {
                        'id': 'ann_bbox',
                        'tool': 'bounding_box',
                        'classification': {'class': 'car'},
                    },
                    {
                        'id': 'ann_poly',
                        'tool': 'polygon',
                        'classification': {'class': 'road'},
                    },
                    {
                        'id': 'ann_kp',
                        'tool': 'keypoint',
                        'classification': {'class': 'person'},
                    },
                ]
            },
            'annotationsData': {
                'image': [
                    {
                        'id': 'ann_bbox',
                        'tool': 'bounding_box',
                        'coordinate': {'x': 0, 'y': 0, 'width': 50, 'height': 50},
                    },
                    {
                        'id': 'ann_poly',
                        'tool': 'polygon',
                        'coordinate': {'points': [[0, 0], [10, 0], [10, 10], [0, 10]]},
                    },
                    {
                        'id': 'ann_kp',
                        'tool': 'keypoint',
                        'coordinate': {'points': [[5, 5]]},
                    },
                ]
            },
        }

        event = {'id': 1, 'files': {}, 'data': {}}
        result = action._build_dm_json(event, annotation_json)

        img_ann = result['images'][0]
        assert len(img_ann['bounding_box']) == 1
        assert len(img_ann['polygon']) == 1
        assert len(img_ann['keypoint']) == 1


# -----------------------------------------------------------------------------
# Test _download_split
# -----------------------------------------------------------------------------


class TestDownloadSplit:
    """Tests for DatasetAction._download_split method."""

    def test_download_split_no_versions(self, mock_backend_client, tmp_path):
        """Returns 0 when no versions found for dataset."""
        mock_backend_client.list_ground_truth_versions.return_value = {'results': []}

        action = MagicMock(spec=DatasetAction)
        action._download_split = DatasetAction._download_split.__get__(action, DatasetAction)
        action.client = mock_backend_client
        action.set_progress = MagicMock()
        action.log = MagicMock()

        result = action._download_split(
            dataset=123,
            output_dir=tmp_path,
            filters={},
        )

        assert result == 0
        action.log.assert_called_with('no_versions_found', {'dataset': 123})

    def test_download_split_empty_events(self, mock_backend_client, tmp_path):
        """Handle empty event generator gracefully."""
        mock_backend_client.list_ground_truth_versions.return_value = {'results': [{'id': 1}]}
        mock_backend_client.list_ground_truths.return_value = (iter([]), 0)

        action = MagicMock(spec=DatasetAction)
        action._download_split = DatasetAction._download_split.__get__(action, DatasetAction)
        action.client = mock_backend_client
        action.set_progress = MagicMock()
        action.log = MagicMock()

        result = action._download_split(
            dataset=123,
            output_dir=tmp_path,
            filters={},
        )

        assert result == 0

    def test_download_split_creates_directories(self, mock_backend_client, tmp_path):
        """Verify json/ and original_files/ directories are created."""
        mock_backend_client.list_ground_truth_versions.return_value = {'results': []}

        action = MagicMock(spec=DatasetAction)
        action._download_split = DatasetAction._download_split.__get__(action, DatasetAction)
        action.client = mock_backend_client
        action.set_progress = MagicMock()
        action.log = MagicMock()

        output_dir = tmp_path / 'test_split'
        action._download_split(
            dataset=123,
            output_dir=output_dir,
            filters={},
        )

        assert (output_dir / 'json').exists()
        assert (output_dir / 'original_files').exists()

    def test_download_split_success(self, mock_backend_client, tmp_path):
        """Full download flow with mocked client - downloads and processes events."""
        # Create test image file
        image_path = tmp_path / 'source' / 'test_image.jpg'
        image_path.parent.mkdir(parents=True)
        image_path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        # Create test annotation JSON
        ann_path = tmp_path / 'source' / 'annotation.json'
        ann_path.write_text(
            json.dumps({
                'annotations': {
                    'image': [
                        {
                            'id': 'ann_1',
                            'tool': 'bounding_box',
                            'classification': {'class': 'car'},
                        }
                    ]
                },
                'annotationsData': {
                    'image': [
                        {
                            'id': 'ann_1',
                            'coordinate': {'x': 10, 'y': 20, 'width': 100, 'height': 50},
                        }
                    ]
                },
            })
        )

        # Setup mock responses
        mock_backend_client.list_ground_truth_versions.return_value = {'results': [{'id': 1}]}

        events = [
            {
                'id': 100,
                'files': {
                    'image_1': {
                        'path': str(image_path),
                        'file_type': 'image',
                        'is_primary': True,
                    },
                    'data_meta_1': {
                        'path': str(ann_path),
                        'file_type': 'data',
                    },
                },
                'data': {},
            }
        ]
        # Override side_effect to return our events
        mock_backend_client.list_ground_truths.side_effect = None
        mock_backend_client.list_ground_truths.return_value = (iter(events), 1)

        # Create real action (we need the actual implementation)
        action = MagicMock(spec=DatasetAction)
        action._download_split = DatasetAction._download_split.__get__(action, DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)
        action.client = mock_backend_client
        action.set_progress = MagicMock()
        action.log = MagicMock()

        output_dir = tmp_path / 'output'
        result = action._download_split(
            dataset=123,
            output_dir=output_dir,
            filters={},
            max_workers=1,
        )

        assert result == 1

        # Check output files were created
        assert (output_dir / 'original_files' / 'test_image.jpg').exists()
        assert (output_dir / 'json' / 'test_image.json').exists()

        # Verify JSON content
        json_content = json.loads((output_dir / 'json' / 'test_image.json').read_text())
        assert 'images' in json_content
        assert len(json_content['images'][0]['bounding_box']) == 1

    def test_download_split_tracks_image_count(self, mock_backend_client, tmp_path):
        """Verify images_found/images_not_found are tracked correctly."""
        # Create event with valid image
        image_path = tmp_path / 'source' / 'found.jpg'
        image_path.parent.mkdir(parents=True)
        image_path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)

        mock_backend_client.list_ground_truth_versions.return_value = {'results': [{'id': 1}]}

        events = [
            # Event with valid image
            {
                'id': 1,
                'files': {
                    'image_1': {
                        'path': str(image_path),
                        'file_type': 'image',
                        'is_primary': True,
                    },
                },
                'data': {},
            },
            # Event without image file
            {
                'id': 2,
                'files': {},
                'data': {},
            },
        ]
        # Override side_effect to return our events
        mock_backend_client.list_ground_truths.side_effect = None
        mock_backend_client.list_ground_truths.return_value = (iter(events), 2)

        action = MagicMock(spec=DatasetAction)
        action._download_split = DatasetAction._download_split.__get__(action, DatasetAction)
        action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)
        action.client = mock_backend_client
        action.set_progress = MagicMock()
        action.log = MagicMock()

        output_dir = tmp_path / 'output'
        result = action._download_split(
            dataset=123,
            output_dir=output_dir,
            filters={},
            max_workers=1,
        )

        assert result == 2

        # Check download_stats was logged
        log_calls = [call[0] for call in action.log.call_args_list]
        assert any('download_stats' in str(call) for call in log_calls)
