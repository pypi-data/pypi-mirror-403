"""Fixtures for dataset action tests."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, PropertyMock

import pytest


@pytest.fixture
def mock_backend_client():
    """Mock BackendClient with list_ground_truths, list_ground_truth_versions methods."""
    client = MagicMock()

    # Default version response
    client.list_ground_truth_versions.return_value = {'results': [{'id': 1, 'name': 'v1.0'}]}

    # Default ground truths response (paginated)
    def default_list_ground_truths(params=None, list_all=False, **kwargs):
        if list_all:
            return (iter([]), 0)
        return {'count': 0, 'results': [], 'next': None}

    client.list_ground_truths.side_effect = default_list_ground_truths

    return client


@pytest.fixture
def sample_annotation_json():
    """Sample annotation JSON content from data_meta_* file."""
    return {
        'annotations': {
            'image': [
                {
                    'id': 'ann_123',
                    'tool': 'bounding_box',
                    'classification': {'class': 'WO-04'},
                    'isValid': True,
                },
                {
                    'id': 'ann_456',
                    'tool': 'polygon',
                    'classification': {'class': 'crack'},
                    'isValid': True,
                },
            ]
        },
        'annotationsData': {
            'image': [
                {
                    'id': 'ann_123',
                    'tool': 'bounding_box',
                    'coordinate': {'x': 382, 'y': 410, 'width': 399, 'height': 381},
                },
                {
                    'id': 'ann_456',
                    'tool': 'polygon',
                    'coordinate': {'points': [[100, 100], [200, 100], [200, 200], [100, 200]]},
                },
            ]
        },
    }


@pytest.fixture
def sample_ground_truth_event(tmp_path):
    """Sample event with files dict."""
    # Create actual files on disk
    image_path = tmp_path / 'image.jpg'
    image_path.write_bytes(b'\xff\xd8\xff\xe0' + b'\x00' * 100)  # Minimal JPEG header

    annotation_path = tmp_path / 'annotation.json'
    annotation_path.write_text(
        json.dumps({
            'annotations': {'image': []},
            'annotationsData': {'image': []},
        })
    )

    return {
        'id': 34673,
        'files': {
            'image_1': {
                'path': str(image_path),
                'file_type': 'image',
                'is_primary': True,
            },
            'data_meta_1': {
                'path': str(annotation_path),
                'file_type': 'data',
            },
        },
        'data': {},
    }


@pytest.fixture
def temp_dataset_dir(tmp_path):
    """Temporary directory structure for dataset."""
    json_dir = tmp_path / 'json'
    files_dir = tmp_path / 'original_files'
    json_dir.mkdir()
    files_dir.mkdir()
    return tmp_path


@pytest.fixture
def mock_dataset_action(mock_backend_client):
    """Create a mock DatasetAction for testing."""
    from synapse_sdk.plugins.actions.dataset.action import DatasetAction

    action = MagicMock(spec=DatasetAction)
    action._build_dm_json = DatasetAction._build_dm_json.__get__(action, DatasetAction)

    # Mock client property
    type(action).client = PropertyMock(return_value=mock_backend_client)

    return action
