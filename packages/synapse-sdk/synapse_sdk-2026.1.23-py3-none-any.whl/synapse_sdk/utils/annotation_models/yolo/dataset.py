"""YOLO dataset and image models.

Models for representing YOLO dataset structure with images and annotations.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from synapse_sdk.utils.annotation_models.yolo.annotation import YOLOAnnotation
from synapse_sdk.utils.annotation_models.yolo.config import YOLODatasetConfig


class YOLOImage(BaseModel):
    """YOLO image with its label file content.

    Represents a single image and its annotations.

    Attributes:
        image_path: Path to the image file.
        annotations: List of YOLO annotations.
    """

    image_path: Path
    annotations: list[YOLOAnnotation] = Field(default_factory=list)

    def to_label_content(self) -> str:
        """Convert annotations to label file content.

        Returns:
            Newline-separated YOLO annotation lines.
        """
        return '\n'.join(ann.to_line() for ann in self.annotations)

    @classmethod
    def from_label_file(cls, image_path: Path, label_path: Path) -> YOLOImage:
        """Load from image and label file pair.

        Args:
            image_path: Path to image file.
            label_path: Path to corresponding label file.

        Returns:
            YOLOImage instance.
        """
        annotations = []
        if label_path.exists():
            for line in label_path.read_text().strip().splitlines():
                if line.strip():
                    annotations.append(YOLOAnnotation.from_line(line))
        return cls(image_path=image_path, annotations=annotations)


class YOLODataset(BaseModel):
    """Full YOLO dataset structure.

    Contains configuration and images for all splits.

    Attributes:
        config: Dataset configuration (dataset.yaml content).
        train_images: Training images with annotations.
        val_images: Validation images with annotations.
        test_images: Test images with annotations (optional).
    """

    config: YOLODatasetConfig
    train_images: list[YOLOImage] = Field(default_factory=list)
    val_images: list[YOLOImage] = Field(default_factory=list)
    test_images: list[YOLOImage] = Field(default_factory=list)


__all__ = [
    'YOLODataset',
    'YOLOImage',
]
