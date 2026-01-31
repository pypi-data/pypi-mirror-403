"""Tests for MLClientMixin list_ground_truths and list_ground_truth_versions methods."""

from __future__ import annotations

import pytest
import responses

from synapse_sdk.clients.backend.ml import MLClientMixin

# -----------------------------------------------------------------------------
# Test Client Implementation
# -----------------------------------------------------------------------------


class MockMLClient(MLClientMixin):
    """Mock client that implements MLClientMixin for testing."""

    def __init__(self, base_url: str = 'https://api.example.com'):
        self.base_url = base_url
        self._list_calls = []
        self._get_calls = []

    def _list(
        self,
        endpoint: str,
        params: dict | None = None,
        url_conversion: dict | None = None,
        list_all: bool = False,
        timeout: tuple | None = None,
    ) -> dict | tuple:
        """Mock _list method."""
        self._list_calls.append({
            'endpoint': endpoint,
            'params': params,
            'url_conversion': url_conversion,
            'list_all': list_all,
            'timeout': timeout,
        })

        if list_all:
            return (iter([{'id': 1}, {'id': 2}]), 2)
        return {
            'count': 2,
            'next': None,
            'results': [{'id': 1}, {'id': 2}],
        }

    def _get(
        self,
        endpoint: str,
        params: dict | None = None,
    ) -> dict:
        """Mock _get method."""
        self._get_calls.append({
            'endpoint': endpoint,
            'params': params,
        })
        return {
            'count': 1,
            'results': [{'id': 1, 'name': 'v1.0'}],
        }


# -----------------------------------------------------------------------------
# Test list_ground_truths
# -----------------------------------------------------------------------------


class TestListGroundTruths:
    """Tests for MLClientMixin.list_ground_truths method."""

    @pytest.fixture
    def client(self):
        """Create mock client."""
        return MockMLClient()

    def test_list_ground_truths_returns_paginated(self, client):
        """Default pagination response (list_all=False)."""
        result = client.list_ground_truths()

        assert isinstance(result, dict)
        assert 'count' in result
        assert 'results' in result
        assert result['count'] == 2
        assert len(result['results']) == 2

    def test_list_ground_truths_list_all(self, client):
        """Returns (generator, count) tuple when list_all=True."""
        result = client.list_ground_truths(list_all=True)

        assert isinstance(result, tuple)
        assert len(result) == 2

        generator, count = result
        assert count == 2

        # Consume generator
        items = list(generator)
        assert len(items) == 2

    def test_list_ground_truths_with_filters(self, client):
        """Passes params correctly to _list."""
        params = {
            'ground_truth_dataset': 123,
            'is_archived': False,
        }
        client.list_ground_truths(params=params)

        assert len(client._list_calls) == 1
        call = client._list_calls[0]
        assert call['params']['ground_truth_dataset'] == 123
        assert call['params']['is_archived'] is False

    def test_list_ground_truths_url_conversion(self, client):
        """Default url_conversion for files is set."""
        client.list_ground_truths()

        assert len(client._list_calls) == 1
        call = client._list_calls[0]
        assert call['url_conversion'] == {
            'files_fields': ['files'],
            'is_list': True,
        }

    def test_list_ground_truths_custom_url_conversion(self, client):
        """Custom url_conversion overrides default."""
        custom_conversion = {'files_fields': ['custom_field'], 'is_list': False}
        client.list_ground_truths(url_conversion=custom_conversion)

        call = client._list_calls[0]
        assert call['url_conversion'] == custom_conversion

    def test_list_ground_truths_endpoint(self, client):
        """Calls correct endpoint."""
        client.list_ground_truths()

        call = client._list_calls[0]
        assert call['endpoint'] == 'ground_truths/'

    def test_list_ground_truths_default_page_size(self, client):
        """Default page_size is 100."""
        client.list_ground_truths()

        call = client._list_calls[0]
        assert call['params']['page_size'] == 100

    def test_list_ground_truths_custom_page_size(self, client):
        """Custom page_size is used."""
        client.list_ground_truths(page_size=50)

        call = client._list_calls[0]
        assert call['params']['page_size'] == 50

    def test_list_ground_truths_timeout(self, client):
        """Timeout is passed to _list."""
        client.list_ground_truths(timeout=120)

        call = client._list_calls[0]
        assert call['timeout'] == (5, 120)


# -----------------------------------------------------------------------------
# Test list_ground_truth_versions
# -----------------------------------------------------------------------------


class TestListGroundTruthVersions:
    """Tests for MLClientMixin.list_ground_truth_versions method."""

    @pytest.fixture
    def client(self):
        """Create mock client."""
        return MockMLClient()

    def test_list_ground_truth_versions(self, client):
        """Returns version list."""
        result = client.list_ground_truth_versions()

        assert isinstance(result, dict)
        assert 'results' in result
        assert len(result['results']) == 1
        assert result['results'][0]['name'] == 'v1.0'

    def test_list_ground_truth_versions_with_filters(self, client):
        """Filter by dataset ID and other params."""
        params = {
            'ground_truth_dataset': 209,
            'is_archived': False,
        }
        client.list_ground_truth_versions(params=params)

        assert len(client._get_calls) == 1
        call = client._get_calls[0]
        assert call['params'] == params

    def test_list_ground_truth_versions_endpoint(self, client):
        """Calls correct endpoint."""
        client.list_ground_truth_versions()

        call = client._get_calls[0]
        assert call['endpoint'] == 'ground_truth_dataset_versions/'

    def test_list_ground_truth_versions_no_params(self, client):
        """Works without params."""
        client.list_ground_truth_versions(params=None)

        assert len(client._get_calls) == 1
        call = client._get_calls[0]
        assert call['params'] is None


# -----------------------------------------------------------------------------
# Integration-style tests with responses mock
# -----------------------------------------------------------------------------


class TestMLClientMixinIntegration:
    """Integration tests using responses mock."""

    @pytest.fixture
    def real_client(self):
        """Create a more realistic client setup."""
        from synapse_sdk.clients.backend import BackendClient

        # BackendClient includes MLClientMixin
        return BackendClient(
            base_url='https://api.test.com',
            access_token='test-access-token',
        )

    @responses.activate
    def test_list_ground_truths_real_client(self, real_client):
        """Test with actual BackendClient implementation."""
        responses.add(
            responses.GET,
            'https://api.test.com/ground_truths/',
            json={
                'count': 1,
                'next': None,
                'results': [
                    {
                        'id': 100,
                        'files': {
                            'image_1': {
                                'path': '/tmp/image.jpg',
                                'url': 'https://storage.example.com/image.jpg',
                            }
                        },
                    }
                ],
            },
            status=200,
        )

        result = real_client.list_ground_truths(params={'ground_truth_dataset': 1})

        assert result['count'] == 1
        assert len(result['results']) == 1
        assert result['results'][0]['id'] == 100

    @responses.activate
    def test_list_ground_truth_versions_real_client(self, real_client):
        """Test list_ground_truth_versions with actual BackendClient."""
        responses.add(
            responses.GET,
            'https://api.test.com/ground_truth_dataset_versions/',
            json={
                'count': 2,
                'results': [
                    {'id': 1, 'name': 'v1.0', 'is_archived': False},
                    {'id': 2, 'name': 'v2.0', 'is_archived': False},
                ],
            },
            status=200,
        )

        result = real_client.list_ground_truth_versions(params={'ground_truth_dataset': 209})

        assert result['count'] == 2
        assert len(result['results']) == 2
        assert result['results'][0]['name'] == 'v1.0'
