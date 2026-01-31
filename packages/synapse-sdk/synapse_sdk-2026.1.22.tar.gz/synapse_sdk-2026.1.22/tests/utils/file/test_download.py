"""Tests for synapse_sdk.utils.file.download - base64 support in files_url_to_path."""

from __future__ import annotations

import base64
from pathlib import Path
from unittest.mock import patch

import pytest

from synapse_sdk.utils.file.download import (
    afiles_url_to_path,
    files_url_to_path,
)

# -----------------------------------------------------------------------------
# Test Data
# -----------------------------------------------------------------------------

# 1x1 transparent PNG
PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
PNG_DATA_URI = f'data:image/png;base64,{PNG_BASE64}'

# Simple text as base64
TEXT_CONTENT = 'Hello, World!'
TEXT_BASE64 = base64.b64encode(TEXT_CONTENT.encode()).decode()
TEXT_DATA_URI = f'data:text/plain;base64,{TEXT_BASE64}'

# Mock URL for testing
MOCK_URL = 'https://example.com/image.png'


# -----------------------------------------------------------------------------
# Tests: files_url_to_path with base64
# -----------------------------------------------------------------------------


class TestFilesUrlToPathBase64:
    """Tests for files_url_to_path with base64 data URIs."""

    def test_converts_base64_data_uri_to_path(self, tmp_path: Path) -> None:
        """Should convert base64 data URI to local file path."""
        files: dict = {'image': PNG_DATA_URI}

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            files_url_to_path(files)

        assert isinstance(files['image'], Path)
        assert files['image'].exists()
        assert files['image'].suffix == '.png'
        assert files['image'].read_bytes() == base64.b64decode(PNG_BASE64)

    def test_converts_text_base64_data_uri(self, tmp_path: Path) -> None:
        """Should convert text base64 data URI to local file."""
        files: dict = {'document': TEXT_DATA_URI}

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            files_url_to_path(files)

        assert files['document'].exists()
        assert files['document'].read_text() == TEXT_CONTENT

    def test_handles_mixed_urls_and_base64(self, tmp_path: Path) -> None:
        """Should handle dictionary with both URLs and base64 data URIs."""
        files: dict = {
            'base64_image': PNG_DATA_URI,
            'url_image': MOCK_URL,
        }

        with (
            patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path),
            patch('synapse_sdk.utils.file.download.download_file') as mock_download,
        ):
            # Mock download_file to return a fake path
            mock_download.return_value = tmp_path / 'downloaded.png'
            (tmp_path / 'downloaded.png').touch()

            files_url_to_path(files)

        # base64 should be decoded directly
        assert isinstance(files['base64_image'], Path)
        assert files['base64_image'].read_bytes() == base64.b64decode(PNG_BASE64)

        # URL should call download_file
        mock_download.assert_called_once()

    def test_handles_dict_with_url_key_and_base64(self, tmp_path: Path) -> None:
        """Should handle dict format with 'url' key containing base64."""
        files: dict = {
            'video': {
                'url': PNG_DATA_URI,  # Can also be base64
                'size': 1024,
            }
        }

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            files_url_to_path(files)

        assert 'path' in files['video']
        assert isinstance(files['video']['path'], Path)
        assert files['video']['path'].exists()
        assert files['video']['size'] == 1024
        assert 'url' not in files['video']

    def test_file_field_parameter_with_base64(self, tmp_path: Path) -> None:
        """Should process only specified file_field with base64."""
        files: dict = {
            'image': PNG_DATA_URI,
            'other': 'should_not_be_processed',
        }

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            files_url_to_path(files, file_field='image')

        assert isinstance(files['image'], Path)
        assert files['other'] == 'should_not_be_processed'

    def test_multiple_base64_files(self, tmp_path: Path) -> None:
        """Should handle multiple base64 data URIs."""
        files: dict = {
            'image1': PNG_DATA_URI,
            'image2': TEXT_DATA_URI,
        }

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            files_url_to_path(files)

        assert files['image1'].exists()
        assert files['image2'].exists()
        assert files['image1'].suffix == '.png'
        assert files['image2'].suffix == '.txt'


# -----------------------------------------------------------------------------
# Tests: afiles_url_to_path with base64 (async)
# -----------------------------------------------------------------------------


class TestAfilesUrlToPathBase64:
    """Tests for afiles_url_to_path with base64 data URIs."""

    @pytest.mark.asyncio
    async def test_converts_base64_data_uri_async(self, tmp_path: Path) -> None:
        """Should convert base64 data URI to local file path asynchronously."""
        files: dict = {'image': PNG_DATA_URI}

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            await afiles_url_to_path(files)

        assert isinstance(files['image'], Path)
        assert files['image'].exists()
        assert files['image'].read_bytes() == base64.b64decode(PNG_BASE64)

    @pytest.mark.asyncio
    async def test_handles_mixed_urls_and_base64_async(self, tmp_path: Path) -> None:
        """Should handle mixed URLs and base64 asynchronously."""
        files: dict = {
            'base64_image': PNG_DATA_URI,
            'url_image': MOCK_URL,
        }

        with (
            patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path),
            patch('synapse_sdk.utils.file.download.adownload_file') as mock_adownload,
        ):
            # Mock adownload_file to return a fake path
            async def fake_download(*args, **kwargs):
                path = tmp_path / 'async_downloaded.png'
                path.touch()
                return path

            mock_adownload.side_effect = fake_download

            await afiles_url_to_path(files)

        # base64 should be decoded directly (sync, since CPU-bound)
        assert isinstance(files['base64_image'], Path)
        assert files['base64_image'].read_bytes() == base64.b64decode(PNG_BASE64)

        # URL should call adownload_file
        mock_adownload.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_dict_with_url_key_async(self, tmp_path: Path) -> None:
        """Should handle dict format with 'url' key asynchronously."""
        files: dict = {
            'video': {
                'url': TEXT_DATA_URI,
                'metadata': {'duration': 120},
            }
        }

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            await afiles_url_to_path(files)

        assert 'path' in files['video']
        assert files['video']['path'].exists()
        assert files['video']['path'].read_text() == TEXT_CONTENT
        assert files['video']['metadata'] == {'duration': 120}

    @pytest.mark.asyncio
    async def test_multiple_base64_files_async(self, tmp_path: Path) -> None:
        """Should handle multiple base64 data URIs asynchronously."""
        files: dict = {
            'file1': PNG_DATA_URI,
            'file2': TEXT_DATA_URI,
        }

        with patch('synapse_sdk.utils.file.download.get_temp_path', return_value=tmp_path):
            await afiles_url_to_path(files)

        assert files['file1'].exists()
        assert files['file2'].exists()
