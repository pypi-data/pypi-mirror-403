"""COCO dataset models.

Models for COCO dataset structure including info, licenses, and the main dataset container.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from synapse_sdk.utils.annotation_models.coco.annotation import COCOAnnotation
from synapse_sdk.utils.annotation_models.coco.category import COCOCategory
from synapse_sdk.utils.annotation_models.coco.image import COCOImage


class COCOInfo(BaseModel):
    """COCO dataset metadata.

    Contains general information about the dataset.

    Attributes:
        description: Dataset description.
        url: Dataset URL.
        version: Dataset version.
        year: Dataset year.
        contributor: Dataset contributor(s).
        date_created: Date when dataset was created.
    """

    description: str = ''
    url: str = ''
    version: str = ''
    year: int | None = None
    contributor: str = ''
    date_created: str = ''


class COCOLicense(BaseModel):
    """COCO license information.

    Represents a license that can be associated with images.

    Attributes:
        id: Unique license ID.
        name: License name.
        url: License URL.
    """

    id: int
    name: str = ''
    url: str = ''


class COCODataset(BaseModel):
    """COCO dataset container.

    Main container for COCO format dataset with all components.

    Attributes:
        info: Dataset metadata.
        licenses: List of licenses.
        images: List of images.
        annotations: List of annotations.
        categories: List of categories.

    Example:
        >>> dataset = COCODataset(
        ...     info=COCOInfo(description='My dataset'),
        ...     categories=[COCOCategory(id=1, name='person')],
        ...     images=[COCOImage(id=1, file_name='img.jpg', width=640, height=480)],
        ...     annotations=[COCOAnnotation(id=1, image_id=1, category_id=1, bbox=[10, 20, 30, 40], area=1200)],
        ... )
        >>> json_str = dataset.to_json()
        >>> loaded = COCODataset.from_json(json_str)
    """

    info: COCOInfo = Field(default_factory=COCOInfo)
    licenses: list[COCOLicense] = Field(default_factory=list)
    images: list[COCOImage] = Field(default_factory=list)
    annotations: list[COCOAnnotation] = Field(default_factory=list)
    categories: list[COCOCategory] = Field(default_factory=list)

    def to_json(self, indent: int | None = None) -> str:
        """Serialize to JSON string.

        Args:
            indent: Optional indentation for pretty printing.

        Returns:
            JSON string representation.
        """
        return self.model_dump_json(indent=indent)

    def to_file(self, file_path: Path | str, indent: int | None = 2) -> None:
        """Save to JSON file.

        Args:
            file_path: Path to output JSON file.
            indent: Optional indentation for pretty printing.
        """
        Path(file_path).write_text(self.to_json(indent=indent))

    @classmethod
    def from_json(cls, json_str: str) -> COCODataset:
        """Deserialize from JSON string.

        Args:
            json_str: JSON string representation.

        Returns:
            COCODataset instance.
        """
        return cls.model_validate_json(json_str)

    @classmethod
    def from_file(cls, file_path: Path | str) -> COCODataset:
        """Load from JSON file.

        Args:
            file_path: Path to JSON file.

        Returns:
            COCODataset instance.
        """
        return cls.from_json(Path(file_path).read_text())

    @classmethod
    def from_dict(cls, data: dict) -> COCODataset:
        """Create from dictionary.

        Args:
            data: Dictionary with COCO format data.

        Returns:
            COCODataset instance.
        """
        return cls.model_validate(data)

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return self.model_dump()

    def get_annotations_by_image_id(self, image_id: int) -> list[COCOAnnotation]:
        """Get all annotations for a specific image.

        Args:
            image_id: Image ID to filter annotations.

        Returns:
            List of annotations for the specified image.
        """
        return [ann for ann in self.annotations if ann.image_id == image_id]

    def get_category_by_id(self, category_id: int) -> COCOCategory | None:
        """Get category by ID.

        Args:
            category_id: Category ID to find.

        Returns:
            COCOCategory if found, None otherwise.
        """
        for cat in self.categories:
            if cat.id == category_id:
                return cat
        return None

    def get_image_by_id(self, image_id: int) -> COCOImage | None:
        """Get image by ID.

        Args:
            image_id: Image ID to find.

        Returns:
            COCOImage if found, None otherwise.
        """
        for img in self.images:
            if img.id == image_id:
                return img
        return None


__all__ = [
    'COCODataset',
    'COCOInfo',
    'COCOLicense',
]
