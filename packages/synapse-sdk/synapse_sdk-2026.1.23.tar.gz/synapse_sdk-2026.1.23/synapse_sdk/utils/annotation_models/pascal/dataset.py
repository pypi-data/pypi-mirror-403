"""Pascal VOC dataset model.

Main annotation model representing the Pascal VOC XML structure.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from pydantic import BaseModel, Field

from synapse_sdk.utils.annotation_models.pascal.annotation import (
    PascalBndBox,
    PascalObject,
    PascalSize,
    PascalSource,
)


class PascalAnnotation(BaseModel):
    """Pascal VOC annotation root structure.

    Represents the complete Pascal VOC XML annotation for one image.

    Attributes:
        folder: Folder name containing the image.
        filename: Image file name.
        path: Full path to the image file.
        source: Source metadata.
        size: Image size information.
        segmented: Whether image has segmentation (0 or 1).
        objects: List of object annotations.

    Example:
        >>> ann = PascalAnnotation(
        ...     folder='Images',
        ...     filename='image001.jpg',
        ...     path='/path/to/image001.jpg',
        ...     size=PascalSize(width=640, height=480, depth=3),
        ...     segmented=0,
        ...     objects=[
        ...         PascalObject(
        ...             name='person',
        ...             bndbox=PascalBndBox(xmin=100, ymin=100, xmax=200, ymax=300)
        ...         )
        ...     ],
        ... )
        >>> xml_str = ann.to_xml()
        >>> loaded = PascalAnnotation.from_xml(xml_str)
    """

    folder: str = 'Images'
    filename: str
    path: str | None = None
    source: PascalSource = Field(default_factory=PascalSource)
    size: PascalSize
    segmented: int = 0
    objects: list[PascalObject] = Field(default_factory=list)

    def to_xml(self, pretty: bool = True) -> str:
        """Convert to Pascal VOC XML string.

        Args:
            pretty: Whether to format with indentation.

        Returns:
            XML string representation.
        """
        root = ET.Element('annotation')

        # Basic info
        ET.SubElement(root, 'folder').text = self.folder
        ET.SubElement(root, 'filename').text = self.filename
        if self.path:
            ET.SubElement(root, 'path').text = self.path

        # Source
        source_elem = ET.SubElement(root, 'source')
        ET.SubElement(source_elem, 'database').text = self.source.database
        if self.source.annotation:
            ET.SubElement(source_elem, 'annotation').text = self.source.annotation
        if self.source.image:
            ET.SubElement(source_elem, 'image').text = self.source.image

        # Size
        size_elem = ET.SubElement(root, 'size')
        ET.SubElement(size_elem, 'width').text = str(self.size.width)
        ET.SubElement(size_elem, 'height').text = str(self.size.height)
        ET.SubElement(size_elem, 'depth').text = str(self.size.depth)

        # Segmented
        ET.SubElement(root, 'segmented').text = str(self.segmented)

        # Objects
        for obj in self.objects:
            obj_elem = ET.SubElement(root, 'object')
            ET.SubElement(obj_elem, 'name').text = obj.name
            ET.SubElement(obj_elem, 'pose').text = obj.pose
            ET.SubElement(obj_elem, 'truncated').text = str(obj.truncated)
            ET.SubElement(obj_elem, 'difficult').text = str(obj.difficult)
            if obj.occluded is not None:
                ET.SubElement(obj_elem, 'occluded').text = str(obj.occluded)

            # Bounding box
            bndbox_elem = ET.SubElement(obj_elem, 'bndbox')
            ET.SubElement(bndbox_elem, 'xmin').text = str(obj.bndbox.xmin)
            ET.SubElement(bndbox_elem, 'ymin').text = str(obj.bndbox.ymin)
            ET.SubElement(bndbox_elem, 'xmax').text = str(obj.bndbox.xmax)
            ET.SubElement(bndbox_elem, 'ymax').text = str(obj.bndbox.ymax)

        if pretty:
            self._indent_xml(root)

        return ET.tostring(root, encoding='unicode')

    @staticmethod
    def _indent_xml(elem: ET.Element, level: int = 0) -> None:
        """Add indentation to XML element for pretty printing."""
        indent = '\n' + '  ' * level
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + '  '
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                PascalAnnotation._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent

    def to_file(self, file_path: Path | str) -> None:
        """Save to XML file.

        Args:
            file_path: Path to output XML file.
        """
        Path(file_path).write_text(self.to_xml())

    @classmethod
    def from_xml(cls, xml_str: str) -> PascalAnnotation:
        """Parse from Pascal VOC XML string.

        Args:
            xml_str: XML string representation.

        Returns:
            PascalAnnotation instance.
        """
        root = ET.fromstring(xml_str)

        # Parse basic info
        folder = root.findtext('folder', 'Images')
        filename = root.findtext('filename', '')
        path = root.findtext('path')

        # Parse source
        source_elem = root.find('source')
        source = PascalSource()
        if source_elem is not None:
            source.database = source_elem.findtext('database', 'Unknown')
            source.annotation = source_elem.findtext('annotation')
            source.image = source_elem.findtext('image')

        # Parse size
        size_elem = root.find('size')
        if size_elem is None:
            raise ValueError('Missing size element in Pascal VOC XML')

        size = PascalSize(
            width=int(size_elem.findtext('width', '0')),
            height=int(size_elem.findtext('height', '0')),
            depth=int(size_elem.findtext('depth', '3')),
        )

        # Parse segmented
        segmented = int(root.findtext('segmented', '0'))

        # Parse objects
        objects = []
        for obj_elem in root.findall('object'):
            name = obj_elem.findtext('name', '')
            pose = obj_elem.findtext('pose', 'Unspecified')
            truncated = int(obj_elem.findtext('truncated', '0'))
            difficult = int(obj_elem.findtext('difficult', '0'))
            occluded_text = obj_elem.findtext('occluded')
            occluded = int(occluded_text) if occluded_text is not None else None

            # Parse bounding box
            bndbox_elem = obj_elem.find('bndbox')
            if bndbox_elem is None:
                continue

            bndbox = PascalBndBox(
                xmin=int(bndbox_elem.findtext('xmin', '0')),
                ymin=int(bndbox_elem.findtext('ymin', '0')),
                xmax=int(bndbox_elem.findtext('xmax', '0')),
                ymax=int(bndbox_elem.findtext('ymax', '0')),
            )

            objects.append(
                PascalObject(
                    name=name,
                    pose=pose,
                    truncated=truncated,
                    difficult=difficult,
                    bndbox=bndbox,
                    occluded=occluded,
                )
            )

        return cls(
            folder=folder,
            filename=filename,
            path=path,
            source=source,
            size=size,
            segmented=segmented,
            objects=objects,
        )

    @classmethod
    def from_file(cls, file_path: Path | str) -> PascalAnnotation:
        """Load from XML file.

        Args:
            file_path: Path to XML file.

        Returns:
            PascalAnnotation instance.
        """
        return cls.from_xml(Path(file_path).read_text())

    def to_dict(self) -> dict:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> PascalAnnotation:
        """Create from dictionary.

        Args:
            data: Dictionary with Pascal VOC data.

        Returns:
            PascalAnnotation instance.
        """
        return cls.model_validate(data)


__all__ = ['PascalAnnotation']
