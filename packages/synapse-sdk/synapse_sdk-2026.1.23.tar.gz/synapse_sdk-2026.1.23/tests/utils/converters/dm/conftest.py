"""
Common fixtures for DM Schema V1/V2 Converter Tests

"""

import json
from pathlib import Path
from typing import Any

import pytest

# Fixtures directory path
FIXTURES_DIR = Path(__file__).parent / 'fixtures'
V1_SAMPLES_DIR = FIXTURES_DIR / 'v1_samples'
V2_SAMPLES_DIR = FIXTURES_DIR / 'v2_samples'


def load_json_fixture(file_path: Path) -> dict[str, Any]:
    """Load JSON fixture file"""
    with open(file_path, encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# V1 Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_bounding_box_sample() -> dict[str, Any]:
    """V1 format bounding box sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_bounding_box.json')


@pytest.fixture
def v1_polygon_sample() -> dict[str, Any]:
    """V1 format polygon sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_polygon.json')


@pytest.fixture
def v1_mixed_sample() -> dict[str, Any]:
    """V1 format mixed tool sample data (bounding box + polygon)"""
    file_path = V1_SAMPLES_DIR / 'image_mixed.json'
    if file_path.exists():
        return load_json_fixture(file_path)
    # If mixed sample doesn't exist, combine bounding box and polygon
    bbox = load_json_fixture(V1_SAMPLES_DIR / 'image_bounding_box.json')
    poly = load_json_fixture(V1_SAMPLES_DIR / 'image_polygon.json')

    # Merge
    mixed = {
        'annotations': {'image_1': bbox['annotations']['image_1'] + poly['annotations']['image_1']},
        'annotationsData': {'image_1': bbox['annotationsData']['image_1'] + poly['annotationsData']['image_1']},
        'extra': {},
        'relations': {},
        'annotationGroups': {},
        'assignmentId': 12345,
    }
    return mixed


# =============================================================================
# V2 Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v2_bounding_box_sample() -> dict[str, Any]:
    """V2 format bounding box sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_bounding_box.json')


@pytest.fixture
def v2_polygon_sample() -> dict[str, Any]:
    """V2 format polygon sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_polygon.json')


# =============================================================================
# Polyline Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_polyline_sample() -> dict[str, Any]:
    """V1 format polyline sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_polyline.json')


@pytest.fixture
def v2_polyline_sample() -> dict[str, Any]:
    """V2 format polyline sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_polyline.json')


# =============================================================================
# Keypoint Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_keypoint_sample() -> dict[str, Any]:
    """V1 format keypoint sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_keypoint.json')


@pytest.fixture
def v2_keypoint_sample() -> dict[str, Any]:
    """V2 format keypoint sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_keypoint.json')


# =============================================================================
# 3D Bounding Box Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_3d_bounding_box_sample() -> dict[str, Any]:
    """V1 format 3D bounding box sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'pcd_3d_bounding_box.json')


@pytest.fixture
def v2_3d_bounding_box_sample() -> dict[str, Any]:
    """V2 format 3D bounding box sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'pcd_3d_bounding_box.json')


# =============================================================================
# Segmentation Sample Data Fixtures (Image/Video)
# =============================================================================


@pytest.fixture
def v1_image_segmentation_sample() -> dict[str, Any]:
    """V1 format image segmentation sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_segmentation.json')


@pytest.fixture
def v2_image_segmentation_sample() -> dict[str, Any]:
    """V2 format image segmentation sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_segmentation.json')


@pytest.fixture
def v1_video_segmentation_sample() -> dict[str, Any]:
    """V1 format video segmentation sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'video_segmentation.json')


@pytest.fixture
def v2_video_segmentation_sample() -> dict[str, Any]:
    """V2 format video segmentation sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'video_segmentation.json')


# =============================================================================
# Named Entity Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_named_entity_sample() -> dict[str, Any]:
    """V1 format named entity sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'text_named_entity.json')


@pytest.fixture
def v2_named_entity_sample() -> dict[str, Any]:
    """V2 format named entity sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'text_named_entity.json')


# =============================================================================
# 3D Segmentation Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_3d_segmentation_sample() -> dict[str, Any]:
    """V1 format 3D segmentation sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'pcd_3d_segmentation.json')


@pytest.fixture
def v2_3d_segmentation_sample() -> dict[str, Any]:
    """V2 format 3D segmentation sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'pcd_3d_segmentation.json')


# =============================================================================
# Classification Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_classification_sample() -> dict[str, Any]:
    """V1 format classification sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_classification.json')


@pytest.fixture
def v2_classification_sample() -> dict[str, Any]:
    """V2 format classification sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_classification.json')


# =============================================================================
# Relation Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_relation_sample() -> dict[str, Any]:
    """V1 format relation sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'image_relation.json')


@pytest.fixture
def v2_relation_sample() -> dict[str, Any]:
    """V2 format relation sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'image_relation.json')


# =============================================================================
# Prompt Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_prompt_sample() -> dict[str, Any]:
    """V1 format prompt sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'prompt_prompt.json')


@pytest.fixture
def v2_prompt_sample() -> dict[str, Any]:
    """V2 format prompt sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'prompt_prompt.json')


# =============================================================================
# Answer Sample Data Fixtures
# =============================================================================


@pytest.fixture
def v1_answer_sample() -> dict[str, Any]:
    """V1 format answer sample data"""
    return load_json_fixture(V1_SAMPLES_DIR / 'prompt_answer.json')


@pytest.fixture
def v2_answer_sample() -> dict[str, Any]:
    """V2 format answer sample data (annotation_data + annotation_meta)"""
    return load_json_fixture(V2_SAMPLES_DIR / 'prompt_answer.json')


# =============================================================================
# Empty Data Fixtures
# =============================================================================


@pytest.fixture
def v1_empty_sample() -> dict[str, Any]:
    """V1 format empty data"""
    return {
        'annotations': {},
        'annotationsData': {},
        'extra': {},
        'relations': {},
        'annotationGroups': {},
        'assignmentId': None,
    }


@pytest.fixture
def v2_empty_sample() -> dict[str, Any]:
    """V2 format empty data"""
    return {
        'annotation_data': {
            'classification': {},
        },
        'annotation_meta': {
            'annotations': {},
            'annotationsData': {},
            'extra': {},
            'relations': {},
            'annotationGroups': {},
            'assignmentId': None,
        },
    }


# =============================================================================
# Helper Functions
# =============================================================================


def assert_v1_structure(data: dict[str, Any]) -> None:
    """Validate V1 data structure"""
    assert 'annotations' in data, "V1 data requires 'annotations' key"
    assert 'annotationsData' in data, "V1 data requires 'annotationsData' key"


def assert_v2_structure(data: dict[str, Any]) -> None:
    """Validate V2 data structure"""
    assert 'annotation_data' in data, "V2 data requires 'annotation_data' key"
    assert 'annotation_meta' in data, "V2 data requires 'annotation_meta' key"


def assert_coordinates_equal(
    coord1: dict[str, float] | list,
    coord2: dict[str, float] | list,
    tolerance: float = 1e-6,
) -> None:
    """Validate coordinate equality (with floating-point tolerance)"""
    if isinstance(coord1, dict) and isinstance(coord2, dict):
        # Bounding box coordinates
        for key in ['x', 'y', 'width', 'height']:
            assert abs(coord1.get(key, 0) - coord2.get(key, 0)) < tolerance, (
                f"Coordinate '{key}' mismatch: {coord1.get(key)} != {coord2.get(key)}"
            )
        # rotation is optional
        if 'rotation' in coord1 or 'rotation' in coord2:
            assert abs(coord1.get('rotation', 0) - coord2.get('rotation', 0)) < tolerance, (
                f'rotation mismatch: {coord1.get("rotation")} != {coord2.get("rotation")}'
            )
    elif isinstance(coord1, list) and isinstance(coord2, list):
        # Polygon coordinates or V2 data array
        assert len(coord1) == len(coord2), f'Coordinate array length mismatch: {len(coord1)} != {len(coord2)}'
        for i, (c1, c2) in enumerate(zip(coord1, coord2)):
            if isinstance(c1, (int, float)):
                assert abs(c1 - c2) < tolerance, f'Coordinate[{i}] mismatch: {c1} != {c2}'
            elif isinstance(c1, list):
                assert_coordinates_equal(c1, c2, tolerance)
            elif isinstance(c1, dict):
                assert_coordinates_equal(c1, c2, tolerance)
