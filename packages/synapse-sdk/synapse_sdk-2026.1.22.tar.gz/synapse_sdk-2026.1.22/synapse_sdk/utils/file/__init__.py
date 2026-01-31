"""File utilities module."""

from .archive import (
    ArchiveFilter,
    ProgressCallback,
    create_archive,
    create_archive_from_git,
    extract_archive,
    get_archive_size,
    list_archive_contents,
)
from .checksum import (
    HashAlgorithm,
    calculate_checksum,
    calculate_checksum_from_bytes,
    calculate_checksum_from_file_object,
    verify_checksum,
)
from .download import (
    adownload_file,
    afiles_url_to_path,
    afiles_url_to_path_from_objs,
    download_file,
    files_url_to_path,
    files_url_to_path_from_objs,
)
from .io import decode_base64_data, get_dict_from_file, get_temp_path, is_base64_data
from .requirements import read_requirements
from .upload import (
    FileProcessingError,
    FilesDict,
    FileTuple,
    FileUploadError,
    FileValidationError,
    RequestsFile,
    close_file_handles,
    process_files_for_upload,
)

__all__ = [
    # I/O
    'get_temp_path',
    'get_dict_from_file',
    # Base64
    'is_base64_data',
    'decode_base64_data',
    # Download (sync)
    'download_file',
    'files_url_to_path',
    'files_url_to_path_from_objs',
    # Download (async)
    'adownload_file',
    'afiles_url_to_path',
    'afiles_url_to_path_from_objs',
    # Requirements
    'read_requirements',
    # Checksum
    'HashAlgorithm',
    'calculate_checksum',
    'calculate_checksum_from_bytes',
    'calculate_checksum_from_file_object',
    'verify_checksum',
    # Archive
    'ProgressCallback',
    'ArchiveFilter',
    'create_archive',
    'create_archive_from_git',
    'extract_archive',
    'list_archive_contents',
    'get_archive_size',
    # Upload
    'FileTuple',
    'RequestsFile',
    'FilesDict',
    'FileUploadError',
    'FileValidationError',
    'FileProcessingError',
    'process_files_for_upload',
    'close_file_handles',
]
