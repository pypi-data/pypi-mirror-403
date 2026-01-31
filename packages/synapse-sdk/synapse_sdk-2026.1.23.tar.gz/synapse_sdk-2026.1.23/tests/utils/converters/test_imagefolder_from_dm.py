"""Tests for FromDMToImageFolderConverter."""

from pathlib import Path
from unittest.mock import patch

from synapse_sdk.utils.annotation_models.dm import DMVersion


class TestDMToImageFolderConverter:
    """Test cases for FromDMToImageFolderConverter class."""

    def test_converter_initialization(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
    ):
        """Test basic initialization of the ImageFolder converter."""
        converter = imagefolder_from_dm_converter_class(str(classification_not_categorized_dataset_path))

        assert converter.root_dir == classification_not_categorized_dataset_path
        assert converter.is_categorized is False
        assert converter.class_names == []
        assert converter.class_map is None
        assert converter.dm_version == DMVersion.V2

    def test_converter_initialization_with_dm_v1(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
    ):
        """Test initialization with DM v1."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_not_categorized_dataset_path),
            dm_version=DMVersion.V1,
        )

        assert converter.dm_version == DMVersion.V1

    def test_get_all_classes_categorized(
        self,
        imagefolder_from_dm_converter_class,
        classification_categorized_dataset_path,
    ):
        """Test collecting all unique class names from categorized dataset."""
        train_dir = classification_categorized_dataset_path / 'train'
        valid_dir = classification_categorized_dataset_path / 'valid'
        test_dir = classification_categorized_dataset_path / 'test'

        classes = imagefolder_from_dm_converter_class.get_all_classes(
            [train_dir, valid_dir, test_dir],
            dm_version=DMVersion.V2,
        )

        # Should find: bird, cat, dog (sorted alphabetically)
        assert classes == ['bird', 'cat', 'dog']
        assert len(classes) == 3

    def test_get_all_classes_not_categorized(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
    ):
        """Test collecting all unique class names from non-categorized dataset."""
        classes = imagefolder_from_dm_converter_class.get_all_classes(
            [classification_not_categorized_dataset_path],
            dm_version=DMVersion.V2,
        )

        # Should find: cat, dog (sorted alphabetically)
        assert classes == ['cat', 'dog']
        assert len(classes) == 2

    def test_get_classification_from_dm_json_v2(
        self,
        imagefolder_from_dm_converter_class,
    ):
        """Test extracting classification from DM v2 JSON."""
        converter = imagefolder_from_dm_converter_class('/dummy/path', dm_version=DMVersion.V2)

        dm_json = {'images': [{'classification': [{'classification': 'cat'}]}]}

        classification = converter._get_classification_from_dm_json(dm_json)
        assert classification == 'cat'

    def test_get_classification_from_dm_json_v2_no_classification(
        self,
        imagefolder_from_dm_converter_class,
    ):
        """Test extracting classification when none exists."""
        converter = imagefolder_from_dm_converter_class('/dummy/path', dm_version=DMVersion.V2)

        dm_json = {'images': [{'bounding_box': []}]}

        classification = converter._get_classification_from_dm_json(dm_json)
        assert classification is None

    def test_get_classification_from_dm_json_v1(
        self,
        imagefolder_from_dm_converter_class,
    ):
        """Test extracting classification from DM v1 JSON."""
        converter = imagefolder_from_dm_converter_class('/dummy/path', dm_version=DMVersion.V1)

        dm_json = {'annotations': {'asset_123': [{'classification': {'class': 'dog'}}]}}

        classification = converter._get_classification_from_dm_json(dm_json)
        assert classification == 'dog'

    def test_convert_categorized_dataset(
        self,
        imagefolder_from_dm_converter_class,
        classification_categorized_dataset_path,
    ):
        """Test conversion of a categorized dataset."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_categorized_dataset_path),
            is_categorized=True,
            dm_version=DMVersion.V2,
        )

        result = converter.convert()

        # Should have train, valid, test splits
        assert 'train' in result
        assert 'valid' in result
        assert 'test' in result

        # Check train split has 3 entries (img1.jpg=cat, img2.jpg=dog, img3.jpg=cat)
        assert len(result['train']) == 3
        assert result['train'][0]['classification'] in ['cat', 'dog']

        # Check valid split has 1 entry
        assert len(result['valid']) == 1
        assert result['valid'][0]['classification'] == 'dog'

        # Check test split has 1 entry
        assert len(result['test']) == 1
        assert result['test'][0]['classification'] == 'bird'

        # Check class names are sorted
        assert converter.class_names == ['bird', 'cat', 'dog']

    def test_convert_not_categorized_dataset(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
    ):
        """Test conversion of a non-categorized dataset."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_not_categorized_dataset_path),
            is_categorized=False,
            dm_version=DMVersion.V2,
        )

        result = converter.convert()

        # Should return a list (not a dict)
        assert isinstance(result, list)
        assert len(result) == 2

        # Check classifications
        classifications = {entry['classification'] for entry in result}
        assert classifications == {'cat', 'dog'}

        # Check class names are sorted
        assert converter.class_names == ['cat', 'dog']

    def test_save_to_folder_categorized(
        self,
        imagefolder_from_dm_converter_class,
        classification_categorized_dataset_path,
        temp_output_dir,
    ):
        """Test saving converted ImageFolder data to folder (categorized)."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_categorized_dataset_path),
            is_categorized=True,
            dm_version=DMVersion.V2,
        )
        converter.convert()

        with patch('shutil.copy') as mock_copy:
            converter.save_to_folder(temp_output_dir)

            # Verify shutil.copy was called for images
            assert mock_copy.call_count > 0

            # Verify directory structure was created
            output_path = Path(temp_output_dir)

            # Check split directories exist
            assert (output_path / 'train').exists()
            assert (output_path / 'valid').exists()
            assert (output_path / 'test').exists()

            # Check class directories exist in each split
            assert (output_path / 'train' / 'bird').exists()
            assert (output_path / 'train' / 'cat').exists()
            assert (output_path / 'train' / 'dog').exists()

            # Verify classes.txt was written
            classes_file = output_path / 'classes.txt'
            assert classes_file.exists()
            classes_content = classes_file.read_text()
            assert 'bird\n' in classes_content
            assert 'cat\n' in classes_content
            assert 'dog\n' in classes_content

    def test_save_to_folder_not_categorized(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
        temp_output_dir,
    ):
        """Test saving converted ImageFolder data to folder (non-categorized)."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_not_categorized_dataset_path),
            is_categorized=False,
            dm_version=DMVersion.V2,
        )
        converter.convert()

        with patch('shutil.copy') as mock_copy:
            converter.save_to_folder(temp_output_dir)

            # Verify shutil.copy was called for images
            assert mock_copy.call_count > 0

            # Verify directory structure was created
            output_path = Path(temp_output_dir)

            # Check class directories exist at root level
            assert (output_path / 'cat').exists()
            assert (output_path / 'dog').exists()

            # Verify classes.txt was written
            classes_file = output_path / 'classes.txt'
            assert classes_file.exists()
            classes_content = classes_file.read_text()
            assert 'cat\n' in classes_content
            assert 'dog\n' in classes_content

    def test_get_config_path(
        self,
        imagefolder_from_dm_converter_class,
        temp_output_dir,
    ):
        """Test get_config_path returns classes.txt path."""
        converter = imagefolder_from_dm_converter_class('/dummy/path')
        output_path = Path(temp_output_dir)

        # Create classes.txt
        classes_file = output_path / 'classes.txt'
        classes_file.write_text('cat\ndog\n')

        config_path = converter.get_config_path(output_path)
        assert config_path == classes_file
        assert config_path.exists()

    def test_get_config_path_not_exists(
        self,
        imagefolder_from_dm_converter_class,
        temp_output_dir,
    ):
        """Test get_config_path returns None when classes.txt doesn't exist."""
        converter = imagefolder_from_dm_converter_class('/dummy/path')
        output_path = Path(temp_output_dir)

        config_path = converter.get_config_path(output_path)
        assert config_path is None

    def test_class_map_generation(
        self,
        imagefolder_from_dm_converter_class,
        classification_not_categorized_dataset_path,
    ):
        """Test that class_map is correctly generated."""
        converter = imagefolder_from_dm_converter_class(
            str(classification_not_categorized_dataset_path),
            dm_version=DMVersion.V2,
        )
        converter.convert()

        # Class map should map class names to indices (sorted alphabetically)
        assert converter.class_map == {'cat': 0, 'dog': 1}

    def test_convert_without_images(
        self,
        imagefolder_from_dm_converter_class,
        temp_output_dir,
    ):
        """Test conversion when JSON files exist but images don't."""
        # Create a temporary dataset with JSON but no images
        json_dir = Path(temp_output_dir) / 'json'
        json_dir.mkdir()

        # Create original_files directory but leave it empty
        original_files_dir = Path(temp_output_dir) / 'original_files'
        original_files_dir.mkdir()

        json_file = json_dir / 'test.json'
        json_file.write_text("""{
            "images": [
                {
                    "classification": [
                        {"classification": "cat"}
                    ]
                }
            ]
        }""")

        converter = imagefolder_from_dm_converter_class(
            str(temp_output_dir),
            is_categorized=False,
            dm_version=DMVersion.V2,
        )

        result = converter.convert()

        # Should have no entries since images are missing
        assert len(result) == 0

    def test_target_format(
        self,
        imagefolder_from_dm_converter_class,
    ):
        """Test that target_format is set correctly."""
        from synapse_sdk.utils.converters.base import DatasetFormat

        converter = imagefolder_from_dm_converter_class('/dummy/path')
        assert converter.target_format == DatasetFormat.IMAGEFOLDER
