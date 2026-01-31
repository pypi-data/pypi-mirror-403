---
id: types
title: Custom Types
sidebar_position: 5
---

# Custom Types

Custom types and Pydantic fields used throughout the SDK.

## FileField

Custom Pydantic field for handling file URLs with automatic download.

```python
from synapse_sdk.enums import FileField
from pydantic import BaseModel

class MyParams(BaseModel):
    input_file: FileField  # Automatically downloads files

def process(params: MyParams):
    file_path = params.input_file  # Local file path
    # Process the file...
```

### Features

- Automatic file download from URLs
- URL-based caching to prevent redundant downloads
- Validates successful download from URL

## Usage Examples

```python
# In plugin parameters
class ProcessParams(BaseModel):
    data_file: FileField
    config_file: FileField | None = None  # Optional file

# The FileField automatically:
# 1. Downloads the file from URL
# 2. Caches files using URL hash
# 3. Returns local file path
```

## Type Validation

Custom validators for ensuring type safety across the SDK.