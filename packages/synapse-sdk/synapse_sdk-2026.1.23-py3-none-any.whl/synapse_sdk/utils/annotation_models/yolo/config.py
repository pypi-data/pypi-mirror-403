"""YOLO dataset configuration model.

Supports standard YOLO dataset.yaml configuration file structure.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class YOLODatasetConfig(BaseModel):
    """YOLO dataset.yaml configuration.

    Standard YOLO dataset configuration file structure.

    Attributes:
        path: Root path to dataset.
        train: Relative path to training images.
        val: Relative path to validation images.
        test: Optional relative path to test images.
        nc: Number of classes.
        names: List of class names.
    """

    path: str = '.'
    train: str = 'train/images'
    val: str = 'valid/images'
    test: str | None = None
    nc: int
    names: list[str]

    def to_yaml(self) -> str:
        """Convert to YAML string.

        Returns:
            YAML-formatted string for dataset.yaml.
        """
        lines = [
            f'path: {self.path}',
            f'train: {self.train}',
            f'val: {self.val}',
        ]
        if self.test:
            lines.append(f'test: {self.test}')
        lines.extend([
            '',
            f'nc: {self.nc}',
            f'names: {self.names}',
            '',
        ])
        return '\n'.join(lines)

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> YOLODatasetConfig:
        """Load from YAML file.

        Args:
            yaml_path: Path to dataset.yaml file.

        Returns:
            YOLODatasetConfig instance.
        """
        import yaml

        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        return cls(
            path=data.get('path', '.'),
            train=data.get('train', 'train/images'),
            val=data.get('val', 'valid/images'),
            test=data.get('test'),
            nc=data['nc'],
            names=data['names'],
        )


__all__ = ['YOLODatasetConfig']
