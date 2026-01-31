"""Tests for DataMaker common models (DMAttribute, DMVersion)."""

from __future__ import annotations

from synapse_sdk.utils.annotation_models.dm import DMAttribute, DMVersion


class TestDMVersion:
    """Tests for DMVersion enum."""

    def test_version_values(self):
        """Test DMVersion enum values."""
        assert DMVersion.V1 == 'v1'
        assert DMVersion.V2 == 'v2'

    def test_version_members(self):
        """Test all DMVersion members exist."""
        assert set(DMVersion) == {DMVersion.V1, DMVersion.V2}


class TestDMAttribute:
    """Tests for DMAttribute model."""

    def test_create_string_attribute(self):
        """Test creating attribute with string value."""
        attr = DMAttribute(name='color', value='red')
        assert attr.name == 'color'
        assert attr.value == 'red'

    def test_create_int_attribute(self):
        """Test creating attribute with integer value."""
        attr = DMAttribute(name='count', value=42)
        assert attr.name == 'count'
        assert attr.value == 42

    def test_create_float_attribute(self):
        """Test creating attribute with float value."""
        attr = DMAttribute(name='confidence', value=0.95)
        assert attr.name == 'confidence'
        assert attr.value == 0.95

    def test_create_bool_attribute(self):
        """Test creating attribute with boolean value."""
        attr = DMAttribute(name='visible', value=True)
        assert attr.name == 'visible'
        assert attr.value is True

    def test_create_list_attribute(self):
        """Test creating attribute with list value."""
        attr = DMAttribute(name='tags', value=['person', 'adult', 'standing'])
        assert attr.name == 'tags'
        assert attr.value == ['person', 'adult', 'standing']

    def test_serialization(self):
        """Test attribute serialization to dict."""
        attr = DMAttribute(name='color', value='blue')
        data = attr.model_dump()
        assert data == {'name': 'color', 'value': 'blue'}

    def test_deserialization(self):
        """Test attribute deserialization from dict."""
        data = {'name': 'size', 'value': 'large'}
        attr = DMAttribute.model_validate(data)
        assert attr.name == 'size'
        assert attr.value == 'large'
