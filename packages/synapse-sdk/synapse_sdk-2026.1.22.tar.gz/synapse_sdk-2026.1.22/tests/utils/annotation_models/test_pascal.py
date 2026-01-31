"""Tests for Pascal VOC annotation models."""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.pascal import (
    PascalAnnotation,
    PascalBndBox,
    PascalObject,
    PascalSize,
    PascalSource,
)


class TestPascalSize:
    """Tests for PascalSize model."""

    def test_create_size(self):
        """Test creating a Pascal size."""
        size = PascalSize(width=640, height=480, depth=3)
        assert size.width == 640
        assert size.height == 480
        assert size.depth == 3

    def test_default_depth(self):
        """Test default depth value."""
        size = PascalSize(width=1920, height=1080)
        assert size.depth == 3


class TestPascalBndBox:
    """Tests for PascalBndBox model."""

    def test_create_bbox(self):
        """Test creating a bounding box."""
        bbox = PascalBndBox(xmin=100, ymin=150, xmax=200, ymax=300)
        assert bbox.xmin == 100
        assert bbox.ymin == 150
        assert bbox.xmax == 200
        assert bbox.ymax == 300


class TestPascalSource:
    """Tests for PascalSource model."""

    def test_create_source(self):
        """Test creating a source."""
        source = PascalSource(database='VOC2012', annotation='manual', image='flickr')
        assert source.database == 'VOC2012'
        assert source.annotation == 'manual'
        assert source.image == 'flickr'

    def test_default_database(self):
        """Test default database value."""
        source = PascalSource()
        assert source.database == 'Unknown'


class TestPascalObject:
    """Tests for PascalObject model."""

    def test_create_object(self):
        """Test creating a Pascal object."""
        bbox = PascalBndBox(xmin=50, ymin=60, xmax=150, ymax=200)
        obj = PascalObject(
            name='person',
            pose='Frontal',
            truncated=0,
            difficult=0,
            bndbox=bbox,
        )
        assert obj.name == 'person'
        assert obj.pose == 'Frontal'
        assert obj.truncated == 0
        assert obj.difficult == 0
        assert obj.bndbox.xmin == 50

    def test_default_values(self):
        """Test default object values."""
        bbox = PascalBndBox(xmin=10, ymin=20, xmax=100, ymax=200)
        obj = PascalObject(name='car', bndbox=bbox)
        assert obj.pose == 'Unspecified'
        assert obj.truncated == 0
        assert obj.difficult == 0
        assert obj.occluded is None


class TestPascalAnnotation:
    """Tests for PascalAnnotation model."""

    def test_create_empty_annotation(self):
        """Test creating an annotation without objects."""
        size = PascalSize(width=640, height=480, depth=3)
        ann = PascalAnnotation(
            filename='image001.jpg',
            size=size,
        )
        assert ann.filename == 'image001.jpg'
        assert ann.size.width == 640
        assert len(ann.objects) == 0
        assert ann.folder == 'Images'
        assert ann.segmented == 0

    def test_create_annotation_with_objects(self):
        """Test creating an annotation with objects."""
        size = PascalSize(width=640, height=480, depth=3)
        bbox = PascalBndBox(xmin=100, ymin=100, xmax=200, ymax=250)
        obj = PascalObject(name='person', bndbox=bbox)

        ann = PascalAnnotation(
            filename='test.jpg',
            size=size,
            objects=[obj],
        )
        assert len(ann.objects) == 1
        assert ann.objects[0].name == 'person'

    def test_to_xml(self):
        """Test converting annotation to XML string."""
        size = PascalSize(width=640, height=480, depth=3)
        bbox = PascalBndBox(xmin=50, ymin=60, xmax=150, ymax=200)
        obj = PascalObject(name='car', bndbox=bbox)

        ann = PascalAnnotation(
            folder='JPEGImages',
            filename='000001.jpg',
            path='/data/000001.jpg',
            size=size,
            segmented=0,
            objects=[obj],
        )

        xml_str = ann.to_xml()
        assert isinstance(xml_str, str)
        assert '<annotation>' in xml_str
        assert '<filename>000001.jpg</filename>' in xml_str
        assert '<width>640</width>' in xml_str
        assert '<name>car</name>' in xml_str
        assert '<xmin>50</xmin>' in xml_str

    def test_from_xml(self):
        """Test parsing annotation from XML string."""
        xml_str = """<annotation>
    <folder>Images</folder>
    <filename>test.jpg</filename>
    <path>/data/test.jpg</path>
    <source>
        <database>VOC2012</database>
    </source>
    <size>
        <width>640</width>
        <height>480</height>
        <depth>3</depth>
    </size>
    <segmented>0</segmented>
    <object>
        <name>person</name>
        <pose>Frontal</pose>
        <truncated>0</truncated>
        <difficult>0</difficult>
        <bndbox>
            <xmin>100</xmin>
            <ymin>150</ymin>
            <xmax>200</xmax>
            <ymax>300</ymax>
        </bndbox>
    </object>
</annotation>"""

        ann = PascalAnnotation.from_xml(xml_str)
        assert ann.filename == 'test.jpg'
        assert ann.folder == 'Images'
        assert ann.path == '/data/test.jpg'
        assert ann.size.width == 640
        assert ann.size.height == 480
        assert ann.segmented == 0
        assert len(ann.objects) == 1
        assert ann.objects[0].name == 'person'
        assert ann.objects[0].bndbox.xmin == 100

    def test_to_dict(self):
        """Test converting annotation to dictionary."""
        size = PascalSize(width=640, height=480, depth=3)
        ann = PascalAnnotation(filename='test.jpg', size=size)

        data = ann.to_dict()
        assert isinstance(data, dict)
        assert data['filename'] == 'test.jpg'
        assert data['size']['width'] == 640

    def test_from_dict(self):
        """Test creating annotation from dictionary."""
        data = {
            'folder': 'Images',
            'filename': 'test.jpg',
            'path': None,
            'source': {'database': 'Unknown', 'annotation': None, 'image': None},
            'size': {'width': 640, 'height': 480, 'depth': 3},
            'segmented': 0,
            'objects': [
                {
                    'name': 'car',
                    'pose': 'Left',
                    'truncated': 0,
                    'difficult': 0,
                    'bndbox': {'xmin': 50, 'ymin': 60, 'xmax': 150, 'ymax': 200},
                    'occluded': None,
                }
            ],
        }

        ann = PascalAnnotation.from_dict(data)
        assert ann.filename == 'test.jpg'
        assert len(ann.objects) == 1
        assert ann.objects[0].name == 'car'

    def test_roundtrip_xml(self):
        """Test XML serialization roundtrip."""
        # Create annotation
        size = PascalSize(width=800, height=600, depth=3)
        bbox1 = PascalBndBox(xmin=100, ymin=100, xmax=200, ymax=250)
        bbox2 = PascalBndBox(xmin=300, ymin=150, xmax=400, ymax=300)
        obj1 = PascalObject(name='person', pose='Frontal', bndbox=bbox1)
        obj2 = PascalObject(name='car', pose='Left', truncated=1, bndbox=bbox2)

        original = PascalAnnotation(
            folder='JPEGImages',
            filename='image.jpg',
            size=size,
            objects=[obj1, obj2],
        )

        # Convert to XML and back
        xml_str = original.to_xml()
        reconstructed = PascalAnnotation.from_xml(xml_str)

        # Verify
        assert reconstructed.filename == original.filename
        assert reconstructed.size.width == original.size.width
        assert len(reconstructed.objects) == len(original.objects)
        assert reconstructed.objects[0].name == 'person'
        assert reconstructed.objects[1].name == 'car'
        assert reconstructed.objects[1].truncated == 1
