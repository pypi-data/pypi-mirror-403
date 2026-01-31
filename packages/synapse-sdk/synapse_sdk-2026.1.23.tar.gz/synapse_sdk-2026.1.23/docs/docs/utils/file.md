---
id: file
title: File Utilities
sidebar_position: 1
---

# File Utilities

File operations and handling utilities for common tasks.

## Module Overview

The file utilities are organized into specialized modules:

| Module | Purpose |
|--------|---------|
| `synapse_sdk.utils.file.archive` | ZIP archive creation and extraction |
| `synapse_sdk.utils.file.checksum` | File hash calculations and verification |
| `synapse_sdk.utils.file.download` | File downloading with async support |
| `synapse_sdk.utils.file.io` | JSON/YAML file operations |
| `synapse_sdk.utils.file.requirements` | Python requirements parsing |

All functions are accessible from the main module:

```python
from synapse_sdk.utils.file import (
    create_archive,
    calculate_checksum,
    download_file,
    get_dict_from_file,
)
```

---

## Archive Operations

Create and extract ZIP archives with filtering and progress tracking.

### create_archive

Create a ZIP archive from a directory.

```python filename="examples/archive.py"
from synapse_sdk.utils.file import create_archive
from pathlib import Path

# Basic usage
archive_path = create_archive(
    source_path=Path("./my_plugin"),
    archive_path=Path("./my_plugin.zip")
)
```

### create_archive_from_git

Create an archive respecting `.gitignore` rules.

```python filename="examples/archive_git.py"
from synapse_sdk.utils.file import create_archive_from_git
from pathlib import Path

# Archive only git-tracked files
archive_path = create_archive_from_git(
    source_path=Path("./my_project"),
    archive_path=Path("./release.zip")
)
```

### extract_archive

Extract a ZIP archive.

```python filename="examples/extract.py"
from synapse_sdk.utils.file import extract_archive
from pathlib import Path

extract_archive(
    archive_path=Path("./archive.zip"),
    output_path=Path("./extracted")
)
```

### Progress Callback

Monitor archive progress with a callback function:

```python filename="examples/progress.py"
from synapse_sdk.utils.file import create_archive
from pathlib import Path

def on_progress(current: int, total: int) -> None:
    percent = (current / total) * 100
    print(f"Progress: {percent:.1f}% ({current}/{total} files)")

create_archive(
    source_path=Path("./data"),
    archive_path=Path("./data.zip"),
    progress_callback=on_progress
)
```

---

## Checksum Functions

Calculate and verify file hashes using various algorithms.

### calculate_checksum

Calculate checksum for a file.

```python filename="examples/checksum.py"
from synapse_sdk.utils.file import calculate_checksum
from pathlib import Path

# Default: MD5
checksum = calculate_checksum(Path("./file.bin"))

# Specify algorithm (use string literals)
sha256_checksum = calculate_checksum(
    Path("./file.bin"),
    algorithm='sha256'
)
```

### Supported Algorithms

`HashAlgorithm` is a `Literal` type that can be imported for type hints:

```python
from synapse_sdk.utils.file import HashAlgorithm

def hash_file(path: str, algo: HashAlgorithm = 'sha256') -> str:
    return calculate_checksum(path, algorithm=algo)
```

| Algorithm | Use Case |
|-----------|----------|
| `'md5'` | Default, legacy compatibility, fast |
| `'sha1'` | Git compatibility |
| `'sha256'` | Secure |
| `'sha512'` | Maximum security |

> **Note**: Pass algorithm values as string literals (e.g., `algorithm='sha256'`). The `HashAlgorithm` type provides IDE autocompletion and type checking.

### verify_checksum

Verify a file against an expected checksum.

```python filename="examples/verify.py"
from synapse_sdk.utils.file import verify_checksum
from pathlib import Path

is_valid = verify_checksum(
    file_path=Path("./download.zip"),
    expected="a1b2c3d4e5f6..."
)

if not is_valid:
    raise ValueError("Checksum mismatch - file may be corrupted")
```

### calculate_checksum_from_file_object

Calculate checksum from file-like objects.

```python filename="examples/checksum_stream.py"
from synapse_sdk.utils.file import calculate_checksum_from_file_object
from io import BytesIO

data = BytesIO(b"Hello, world!")
checksum = calculate_checksum_from_file_object(data)
```

> **Good to know**: Checksum functions read in chunks (1MB by default) for memory efficiency with large files.

---

## Download Functions

Download files from URLs with both synchronous and asynchronous support.

### download_file

Synchronous file download. The filename is automatically derived from the URL (or generated from URL hash).

```python filename="examples/download.py"
from synapse_sdk.utils.file import download_file
from pathlib import Path

# Download to directory (filename derived from URL)
local_path = download_file(
    url="https://example.com/file.zip",
    path_download=Path("./downloads")
)

# With custom filename
local_path = download_file(
    url="https://example.com/file.zip",
    path_download=Path("./downloads"),
    name="my_file"  # Results in my_file.zip
)
```

### adownload_file

Asynchronous file download.

```python filename="examples/async_download.py"
import asyncio
from synapse_sdk.utils.file import adownload_file
from pathlib import Path

async def main():
    path = await adownload_file(
        url="https://example.com/file.zip",
        path_download=Path("./downloads")
    )
    print(f"Downloaded to: {path}")

asyncio.run(main())
```

### Batch Downloads

Convert file URLs to local paths by downloading them. The function modifies the dictionary in-place.

```python filename="examples/batch_download.py"
from synapse_sdk.utils.file import files_url_to_path

# Simple URL values - replaced with local Paths
files = {
    'image1': 'https://example.com/file1.jpg',
    'image2': 'https://example.com/file2.jpg',
}
files_url_to_path(files)  # In-place modification
# files['image1'] is now a local Path object

# Dict values with 'url' key - 'url' is replaced with 'path'
files = {
    'video': {'url': 'https://example.com/vid.mp4', 'size': 1024},
}
files_url_to_path(files)
# files['video'] is now {'path': Path(...), 'size': 1024}
```

For async batch downloads, use `afiles_url_to_path`:

```python filename="examples/async_batch_download.py"
import asyncio
from synapse_sdk.utils.file import afiles_url_to_path

async def main():
    files = {
        'image1': 'https://example.com/file1.jpg',
        'image2': 'https://example.com/file2.jpg',
    }
    await afiles_url_to_path(files)
    print(files)  # URLs replaced with local Paths

asyncio.run(main())
```

---

## I/O Functions

Read and write structured data files.

### get_dict_from_file

Load a dictionary from JSON or YAML files.

```python filename="examples/io.py"
from synapse_sdk.utils.file import get_dict_from_file

# JSON file
config = get_dict_from_file("/path/to/config.json")

# YAML file
settings = get_dict_from_file("/path/to/settings.yaml")
```

### get_temp_path

Get a temporary directory path for SDK operations.

```python filename="examples/temp.py"
from synapse_sdk.utils.file import get_temp_path

# Get base temp directory: /tmp/datamaker
temp_dir = get_temp_path()

# Get subdirectory path: /tmp/datamaker/media
media_dir = get_temp_path("media")
```

---

## Requirements Parsing

Parse Python requirements files.

### read_requirements

Parse a requirements.txt file into a list. Returns `None` if the file doesn't exist or contains no valid requirements.

```python filename="examples/requirements.py"
from synapse_sdk.utils.file import read_requirements

requirements = read_requirements("./requirements.txt")

if requirements:
    print(requirements)
    # ['numpy>=1.20.0', 'pandas>=1.3.0', 'requests>=2.25.0']
else:
    print("No requirements found or file doesn't exist")
```

---

## See Also

- [Storage Providers](./storage.md) - Cloud storage operations
- [Network Utilities](./network.md) - Network streaming utilities
