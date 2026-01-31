"""
Performance Tests

Purpose: Verify that a single conversion completes within 100ms (spec.md TR-006)
"""

import time

import pytest

from synapse_sdk.utils.converters.dm import convert_v1_to_v2, convert_v2_to_v1


class TestPerformance:
    """Performance tests"""

    @pytest.fixture
    def large_v1_data(self):
        """Generate large V1 data (100 annotations)"""
        annotations = []
        annotations_data = []

        for i in range(100):
            ann_id = f'ann_{i}'
            if i % 2 == 0:
                # bounding box
                annotations.append({
                    'id': ann_id,
                    'tool': 'bounding_box',
                    'isLocked': False,
                    'isVisible': True,
                    'classification': {'class': f'class_{i % 10}'},
                    'label': [f'class_{i % 10}'],
                })
                annotations_data.append({
                    'id': ann_id,
                    'coordinate': {
                        'x': i * 10,
                        'y': i * 5,
                        'width': 100 + i,
                        'height': 50 + i,
                    },
                })
            else:
                # polygon
                annotations.append({
                    'id': ann_id,
                    'tool': 'polygon',
                    'isLocked': False,
                    'isVisible': True,
                    'classification': {'class': f'class_{i % 10}'},
                    'label': [f'class_{i % 10}'],
                })
                # 20-point polygon
                coordinates = [{'x': j * 10 + i, 'y': j * 5 + i, 'id': f'p{j}'} for j in range(20)]
                annotations_data.append({
                    'id': ann_id,
                    'coordinate': coordinates,
                })

        return {
            'annotations': {'image_1': annotations},
            'annotationsData': {'image_1': annotations_data},
        }

    @pytest.fixture
    def large_v2_data(self, large_v1_data):
        """Generate large V2 data"""
        return convert_v1_to_v2(large_v1_data)

    def test_v1_to_v2_performance_small(self, v1_bounding_box_sample):
        """V1 to V2 conversion performance (small data)"""
        start = time.perf_counter()

        for _ in range(100):
            convert_v1_to_v2(v1_bounding_box_sample)

        elapsed = time.perf_counter() - start
        avg_time_ms = (elapsed / 100) * 1000

        assert avg_time_ms < 100, f'Average conversion time {avg_time_ms:.2f}ms exceeds 100ms'
        print(f'\nV1 to V2 (small data) average: {avg_time_ms:.3f}ms')

    def test_v2_to_v1_performance_small(self, v2_bounding_box_sample):
        """V2 to V1 conversion performance (small data)"""
        start = time.perf_counter()

        for _ in range(100):
            convert_v2_to_v1(v2_bounding_box_sample)

        elapsed = time.perf_counter() - start
        avg_time_ms = (elapsed / 100) * 1000

        assert avg_time_ms < 100, f'Average conversion time {avg_time_ms:.2f}ms exceeds 100ms'
        print(f'\nV2 to V1 (small data) average: {avg_time_ms:.3f}ms')

    def test_v1_to_v2_performance_large(self, large_v1_data):
        """V1 to V2 conversion performance (large data: 100 annotations)"""
        start = time.perf_counter()

        result = convert_v1_to_v2(large_v1_data)

        elapsed_ms = (time.perf_counter() - start) * 1000

        # 100 annotations within 100ms
        assert elapsed_ms < 100, f'Conversion time {elapsed_ms:.2f}ms exceeds 100ms'
        print(f'\nV1 to V2 (100 annotations): {elapsed_ms:.3f}ms')

        # verify result
        images = result['annotation_data']['images'][0]
        total_anns = len(images.get('bounding_box', [])) + len(images.get('polygon', []))
        assert total_anns == 100

    def test_v2_to_v1_performance_large(self, large_v2_data):
        """V2 to V1 conversion performance (large data: 100 annotations)"""
        start = time.perf_counter()

        result = convert_v2_to_v1(large_v2_data)

        elapsed_ms = (time.perf_counter() - start) * 1000

        # 100 annotations within 100ms
        assert elapsed_ms < 100, f'Conversion time {elapsed_ms:.2f}ms exceeds 100ms'
        print(f'\nV2 to V1 (100 annotations): {elapsed_ms:.3f}ms')

        # verify result
        total_anns = len(result['annotations']['image_1'])
        assert total_anns == 100

    def test_roundtrip_performance(self, large_v1_data):
        """Roundtrip conversion performance (V1 to V2 to V1)"""
        start = time.perf_counter()

        v2_result = convert_v1_to_v2(large_v1_data)
        _ = convert_v2_to_v1(v2_result)

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Roundtrip within 200ms (100ms each)
        assert elapsed_ms < 200, f'Roundtrip time {elapsed_ms:.2f}ms exceeds 200ms'
        print(f'\nRoundtrip (100 annotations): {elapsed_ms:.3f}ms')
