"""Tests for synapse_sdk.utils.file.io - base64 functions."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from synapse_sdk.utils.file.io import decode_base64_data, is_base64_data

# -----------------------------------------------------------------------------
# Test Data
# -----------------------------------------------------------------------------

# 1x1 transparent PNG
PNG_BASE64 = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
PNG_DATA_URI = f'data:image/png;base64,{PNG_BASE64}'

# 1x1 red JPEG (minimal)
JPEG_BASE64 = (
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a'
    'HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy'
    'MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEB'
    'AxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAn/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAA'
    'AAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBEQACEQA/ALUABp//2Q=='
)
JPEG_DATA_URI = f'data:image/jpeg;base64,{JPEG_BASE64}'

# Simple text file as base64
TEXT_CONTENT = 'Hello, World!'
TEXT_BASE64 = base64.b64encode(TEXT_CONTENT.encode()).decode()
TEXT_DATA_URI = f'data:text/plain;base64,{TEXT_BASE64}'


# -----------------------------------------------------------------------------
# Tests: is_base64_data
# -----------------------------------------------------------------------------


class TestIsBase64Data:
    """Tests for is_base64_data function."""

    def test_returns_true_for_png_data_uri(self) -> None:
        """Should return True for valid PNG data URI."""
        assert is_base64_data(PNG_DATA_URI) is True

    def test_returns_true_for_jpeg_data_uri(self) -> None:
        """Should return True for valid JPEG data URI."""
        assert is_base64_data(JPEG_DATA_URI) is True

    def test_returns_true_for_text_data_uri(self) -> None:
        """Should return True for valid text data URI."""
        assert is_base64_data(TEXT_DATA_URI) is True

    def test_returns_false_for_http_url(self) -> None:
        """Should return False for HTTP URL."""
        assert is_base64_data('http://example.com/image.png') is False

    def test_returns_false_for_https_url(self) -> None:
        """Should return False for HTTPS URL."""
        assert is_base64_data('https://example.com/image.png') is False

    def test_returns_false_for_file_path(self) -> None:
        """Should return False for file path."""
        assert is_base64_data('/path/to/file.png') is False

    def test_returns_false_for_empty_string(self) -> None:
        """Should return False for empty string."""
        assert is_base64_data('') is False

    def test_returns_false_for_none(self) -> None:
        """Should return False for None (type check)."""
        assert is_base64_data(None) is False  # type: ignore[arg-type]

    def test_returns_false_for_non_string(self) -> None:
        """Should return False for non-string types."""
        assert is_base64_data(12345) is False  # type: ignore[arg-type]
        assert is_base64_data(['data:']) is False  # type: ignore[arg-type]

    def test_returns_true_for_minimal_data_uri(self) -> None:
        """Should return True for minimal data URI prefix."""
        assert is_base64_data('data:,') is True


# -----------------------------------------------------------------------------
# Tests: decode_base64_data
# -----------------------------------------------------------------------------


class TestDecodeBase64Data:
    """Tests for decode_base64_data function."""

    def test_decode_png_data_uri(self, tmp_path: Path) -> None:
        """Should decode PNG data URI and save as .png file."""
        result = decode_base64_data(PNG_DATA_URI, tmp_path)

        assert result.exists()
        assert result.suffix == '.png'
        assert result.read_bytes() == base64.b64decode(PNG_BASE64)

    def test_decode_jpeg_data_uri(self, tmp_path: Path) -> None:
        """Should decode JPEG data URI and save as .jpeg/.jpg file."""
        result = decode_base64_data(JPEG_DATA_URI, tmp_path)

        assert result.exists()
        # mimetypes.guess_extension for image/jpeg can return .jpeg or .jpg
        assert result.suffix in ('.jpeg', '.jpg')
        assert result.read_bytes() == base64.b64decode(JPEG_BASE64)

    def test_decode_text_data_uri(self, tmp_path: Path) -> None:
        """Should decode text data URI and save as .txt file."""
        result = decode_base64_data(TEXT_DATA_URI, tmp_path)

        assert result.exists()
        assert result.suffix == '.txt'
        assert result.read_text() == TEXT_CONTENT

    def test_uses_md5_hash_as_default_filename(self, tmp_path: Path) -> None:
        """Should use MD5 hash of content as filename when name not provided."""
        import hashlib

        result = decode_base64_data(PNG_DATA_URI, tmp_path)

        content = base64.b64decode(PNG_BASE64)
        expected_hash = hashlib.md5(content).hexdigest()

        assert result.stem == expected_hash

    def test_uses_custom_filename(self, tmp_path: Path) -> None:
        """Should use custom filename when provided."""
        result = decode_base64_data(PNG_DATA_URI, tmp_path, name='my_image')

        assert result.stem == 'my_image'
        assert result.suffix == '.png'

    def test_raises_for_invalid_data_uri(self, tmp_path: Path) -> None:
        """Should raise ValueError for invalid data URI."""
        with pytest.raises(ValueError, match='Invalid data URI format'):
            decode_base64_data('https://example.com/image.png', tmp_path)

    def test_raises_for_malformed_data_uri(self, tmp_path: Path) -> None:
        """Should raise ValueError for malformed data URI (no comma)."""
        with pytest.raises(ValueError, match='Invalid data URI format'):
            decode_base64_data('data:image/png;base64', tmp_path)

    def test_handles_data_uri_without_base64_marker(self, tmp_path: Path) -> None:
        """Should handle data URI without explicit base64 marker in header."""
        # Some data URIs might just be data:mime,content
        simple_uri = f'data:text/plain;base64,{TEXT_BASE64}'
        result = decode_base64_data(simple_uri, tmp_path)

        assert result.exists()
        assert result.read_text() == TEXT_CONTENT

    def test_handles_unknown_mime_type(self, tmp_path: Path) -> None:
        """Should handle unknown MIME type (no extension)."""
        unknown_uri = f'data:application/x-unknown;base64,{TEXT_BASE64}'
        result = decode_base64_data(unknown_uri, tmp_path)

        assert result.exists()
        # Unknown mime type may result in no extension or a generic one
        assert result.read_bytes() == TEXT_CONTENT.encode()

    def test_accepts_string_path(self, tmp_path: Path) -> None:
        """Should accept string path as well as Path object."""
        result = decode_base64_data(PNG_DATA_URI, str(tmp_path))

        assert result.exists()
        assert result.suffix == '.png'

    def test_pdf_data_uri(self, tmp_path: Path) -> None:
        """Should decode PDF data URI correctly."""
        # Minimal PDF content (not a valid PDF, just for testing)
        pdf_content = b'%PDF-1.4 test'
        pdf_base64 = base64.b64encode(pdf_content).decode()
        pdf_uri = f'data:application/pdf;base64,{pdf_base64}'

        result = decode_base64_data(pdf_uri, tmp_path)

        assert result.exists()
        assert result.suffix == '.pdf'
        assert result.read_bytes() == pdf_content
