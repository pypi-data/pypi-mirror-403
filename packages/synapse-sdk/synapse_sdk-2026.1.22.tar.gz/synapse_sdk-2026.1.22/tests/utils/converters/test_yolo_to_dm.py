import os
from unittest.mock import patch


def test_convert_categorized_dataset(yolo_to_dm_converter, categorized_yolo_dataset_path):
    """Test conversion of a categorized YOLO dataset."""
    converter = yolo_to_dm_converter(str(categorized_yolo_dataset_path), is_categorized=True)
    result = converter.convert()

    assert 'train' in result, 'Train split should be present in the result.'
    assert len(result['train']) > 0, 'Train split should not be empty.'
    jpg_files = [item[1] for item in result['train'].values()]
    filenames = [os.path.basename(file) for file in jpg_files]
    assert '13782.jpg' in filenames, 'Corresponding image file should be present in the result.'


def test_convert_non_categorized_dataset(yolo_to_dm_converter, not_categorized_yolo_dataset_path):
    """Test conversion of a non-categorized YOLO dataset."""
    converter = yolo_to_dm_converter(str(not_categorized_yolo_dataset_path), is_categorized=False)
    result = converter.convert()

    assert len(result) > 0, 'Result should not be empty for non-categorized dataset.'

    jpg_files = [item[1] for item in result.values()]
    filenames = [os.path.basename(file) for file in jpg_files]
    assert '25332.jpg' in filenames, 'Corresponding image file should be present in the result.'


def test_dataset_save_to_folder(yolo_to_dm_converter, not_categorized_yolo_dataset_path, tmp_path):
    """Test saving converted dataset to folder."""
    temp_output_dir = tmp_path / 'test_output'
    converter = yolo_to_dm_converter(str(not_categorized_yolo_dataset_path), is_categorized=False)
    converter.convert()

    with patch('shutil.copy') as mock_copy:
        converter.save_to_folder(str(temp_output_dir))

        # Verify copy was called for images
        mock_copy.assert_called()

        # Verify JSON files were written
        json_dir = temp_output_dir / 'json'
        assert json_dir.exists()
        json_files = list(json_dir.glob('*.json'))
        assert len(json_files) > 0, 'JSON files should be written to output directory'
