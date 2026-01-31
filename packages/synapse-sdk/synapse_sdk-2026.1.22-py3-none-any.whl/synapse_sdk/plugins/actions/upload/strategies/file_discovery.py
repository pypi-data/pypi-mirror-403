"""File discovery strategies for upload operations.

Provides strategies for discovering and organizing files:
    - FlatFileDiscoveryStrategy: Non-recursive file discovery
    - RecursiveFileDiscoveryStrategy: Recursive file discovery
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from synapse_sdk.plugins.actions.upload.strategies.base import FileDiscoveryStrategy

# System directories to exclude from file discovery
EXCLUDED_DIRS = frozenset({
    '@eaDir',  # Synology metadata
    '.@__thumb',  # Synology thumbnails
    '@Recycle',  # Synology recycle
    '#recycle',  # SMB recycle
    '.DS_Store',  # macOS
    'Thumbs.db',  # Windows
    '.synology',  # Synology
    '__pycache__',  # Python cache
    '.git',  # Git
})

# Files to exclude from file discovery
EXCLUDED_FILES = frozenset({
    '.DS_Store',
    'Thumbs.db',
    'desktop.ini',
    '.gitkeep',
})


class FlatFileDiscoveryStrategy(FileDiscoveryStrategy):
    """Flat (non-recursive) file discovery strategy.

    Discovers files only in the immediate directory without
    traversing subdirectories.

    Example:
        >>> strategy = FlatFileDiscoveryStrategy()
        >>> files = strategy.discover(Path("/data/images"), recursive=False)
    """

    def discover(self, path: Path, recursive: bool = False) -> list[Path]:
        """Discover files in the given path.

        Args:
            path: Directory path to search.
            recursive: If True, uses recursive search. Default is False.

        Returns:
            List of discovered file paths.
        """
        if recursive:
            return self._discover_recursive(path)
        return self._discover_flat(path)

    def _discover_flat(self, path: Path) -> list[Path]:
        """Discover files non-recursively."""
        if not path.exists() or not path.is_dir():
            return []

        return [
            file_path for file_path in path.glob('*') if file_path.is_file() and file_path.name not in EXCLUDED_FILES
        ]

    def _discover_recursive(self, path: Path) -> list[Path]:
        """Discover files recursively."""
        if not path.exists() or not path.is_dir():
            return []

        def is_excluded(file_path: Path) -> bool:
            """Check if file path contains excluded directories."""
            return any(excluded in file_path.parts for excluded in EXCLUDED_DIRS)

        return [
            file_path
            for file_path in path.rglob('*')
            if file_path.is_file() and not is_excluded(file_path) and file_path.name not in EXCLUDED_FILES
        ]

    def organize(
        self,
        files: list[Path],
        specs: list[dict[str, Any]],
        metadata: dict[str, dict[str, Any]],
        type_dirs: dict[str, Path] | None = None,
    ) -> list[dict[str, Any]]:
        """Organize files according to specifications.

        Uses stem-based grouping to match files with specifications.

        Args:
            files: List of discovered file paths.
            specs: File specifications from data collection.
            metadata: Metadata dictionary keyed by filename.
            type_dirs: Mapping of spec names to directories.

        Returns:
            List of organized file dictionaries.
        """
        if type_dirs is None:
            type_dirs = self._build_type_dirs(files, specs)

        if not type_dirs:
            return []

        # Build metadata index for faster lookups
        metadata_index = self._build_metadata_index(metadata)

        # Group files by dataset key (stem-based)
        dataset_files = self._group_files_by_stem(files, specs, type_dirs)

        # Create organized files from groups with all required files
        return self._create_organized_files(dataset_files, specs, metadata_index)

    def _build_type_dirs(
        self,
        files: list[Path],
        specs: list[dict[str, Any]],
    ) -> dict[str, Path]:
        """Build type directories mapping from file paths and specs."""
        type_dirs: dict[str, Path] = {}

        for spec in specs:
            spec_name = spec.get('name', '')
            if not spec_name:
                continue

            # Find directory containing spec name in file paths
            for file_path in files:
                if spec_name in file_path.parts:
                    spec_index = file_path.parts.index(spec_name)
                    spec_dir = Path(*file_path.parts[: spec_index + 1])
                    if spec_dir.exists() and spec_dir.is_dir():
                        type_dirs[spec_name] = spec_dir
                        break

        return type_dirs

    def _build_metadata_index(
        self,
        metadata: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Build metadata index for faster lookups."""
        if not metadata:
            return {}

        index: dict[str, dict[str, Any]] = {
            'exact_stem': {},
            'exact_name': {},
            'partial_paths': {},
        }

        for meta_key, meta_value in metadata.items():
            meta_path = Path(meta_key)

            # Index by stem
            stem = meta_path.stem
            if stem:
                index['exact_stem'][stem] = meta_value

            # Index by full name
            name = meta_path.name
            if name:
                index['exact_name'][name] = meta_value

            # Index for partial path matching
            index['partial_paths'][meta_key] = meta_value

        return index

    def _group_files_by_stem(
        self,
        files: list[Path],
        specs: list[dict[str, Any]],
        type_dirs: dict[str, Path],
    ) -> dict[str, dict[str, Path]]:
        """Group files by their stem for data unit creation."""
        dataset_files: dict[str, dict[str, Path]] = {}

        for file_path in files:
            # Find matching spec directory
            matched_spec = self._find_matching_spec(file_path, type_dirs)
            if not matched_spec:
                continue

            spec_name, dir_path, relative_path = matched_spec

            # Create dataset key from relative path and stem
            if relative_path.parent != Path('.'):
                dataset_key = f'{relative_path.parent}_{file_path.stem}'
            else:
                dataset_key = file_path.stem

            # Add to group
            if dataset_key not in dataset_files:
                dataset_files[dataset_key] = {}

            if spec_name not in dataset_files[dataset_key]:
                dataset_files[dataset_key][spec_name] = file_path
            else:
                # Keep the most recent file
                existing = dataset_files[dataset_key][spec_name]
                try:
                    if file_path.stat().st_mtime > existing.stat().st_mtime:
                        dataset_files[dataset_key][spec_name] = file_path
                except (OSError, IOError):
                    pass

        return dataset_files

    def _find_matching_spec(
        self,
        file_path: Path,
        type_dirs: dict[str, Path],
    ) -> tuple[str, Path, Path] | None:
        """Find the matching spec for a file path."""
        matched_specs = []

        for spec_name, dir_path in type_dirs.items():
            try:
                relative_path = file_path.relative_to(dir_path)
                matched_specs.append((spec_name, dir_path, relative_path))
            except ValueError:
                continue

        if not matched_specs:
            return None

        # Return the most specific (deepest) match
        return max(matched_specs, key=lambda x: len(x[1].parts))

    def _create_organized_files(
        self,
        dataset_files: dict[str, dict[str, Path]],
        specs: list[dict[str, Any]],
        metadata_index: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Create organized file entries from grouped files."""
        organized_files = []
        required_specs = [spec['name'] for spec in specs if spec.get('is_required', False)]

        for dataset_key, files_dict in sorted(dataset_files.items()):
            # Check if all required files are present
            has_all_required = all(req in files_dict for req in required_specs)

            if not has_all_required:
                continue

            # Extract file stems and extensions
            file_stems = {}
            file_extensions = {}

            for file_path in files_dict.values():
                stem = file_path.stem
                ext = file_path.suffix.lower()

                if stem:
                    file_stems[stem] = file_stems.get(stem, 0) + 1
                if ext:
                    file_extensions[ext] = file_extensions.get(ext, 0) + 1

            # Use most common stem
            original_stem = max(file_stems, key=file_stems.get) if file_stems else dataset_key
            origin_extension = max(file_extensions, key=file_extensions.get) if file_extensions else ''

            # Build metadata
            meta_data = {
                'origin_file_stem': original_stem,
                'origin_file_extension': origin_extension,
                'created_at': datetime.now().isoformat(),
                'dataset_key': dataset_key,
            }

            # Add matched metadata
            if metadata_index:
                matched = self._find_matching_metadata(original_stem, files_dict, metadata_index)
                if matched:
                    meta_data.update(matched)

            organized_files.append({
                'files': files_dict,
                'meta': meta_data,
            })

        return organized_files

    def _find_matching_metadata(
        self,
        file_stem: str,
        files_dict: dict[str, Path],
        metadata_index: dict[str, Any],
    ) -> dict[str, Any]:
        """Find matching metadata using index lookups."""
        if not metadata_index:
            return {}

        # Strategy 1: Exact stem match
        if file_stem in metadata_index.get('exact_stem', {}):
            return metadata_index['exact_stem'][file_stem]

        # Strategy 2: Exact filename match
        sample_file = next(iter(files_dict.values()), None)
        if sample_file:
            full_filename = f'{file_stem}{sample_file.suffix}'
            if full_filename in metadata_index.get('exact_name', {}):
                return metadata_index['exact_name'][full_filename]

            if sample_file.name in metadata_index.get('exact_name', {}):
                return metadata_index['exact_name'][sample_file.name]

            # Strategy 3: Partial path matching
            file_path_str = str(sample_file)
            file_path_posix = sample_file.as_posix()

            for meta_key, meta_value in metadata_index.get('partial_paths', {}).items():
                if (
                    meta_key in file_path_str
                    or meta_key in file_path_posix
                    or file_path_str in meta_key
                    or file_path_posix in meta_key
                ):
                    return meta_value

        return {}


class RecursiveFileDiscoveryStrategy(FlatFileDiscoveryStrategy):
    """Recursive file discovery strategy.

    Extends FlatFileDiscoveryStrategy with recursive search as default.

    Example:
        >>> strategy = RecursiveFileDiscoveryStrategy()
        >>> files = strategy.discover(Path("/data/images"))  # recursive by default
    """

    def discover(self, path: Path, recursive: bool = True) -> list[Path]:
        """Discover files recursively in the given path.

        Args:
            path: Directory path to search.
            recursive: Whether to search recursively. Default is True.

        Returns:
            List of discovered file paths.
        """
        return super().discover(path, recursive=recursive)


__all__ = [
    'EXCLUDED_DIRS',
    'EXCLUDED_FILES',
    'FlatFileDiscoveryStrategy',
    'RecursiveFileDiscoveryStrategy',
]
