"""
Tests for field_ops module: modify_fieldinfo
"""

import pytest
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from pydantic_variants.field_ops import modify_fieldinfo


class TestModifyFieldinfo:
    """Tests for modify_fieldinfo function."""

    def test_creates_copy(self):
        """Returns a new FieldInfo, not the original."""
        original = FieldInfo(annotation=str, default="original")
        modified = modify_fieldinfo(original, default="modified")

        assert modified is not original
        assert original.default == "original"
        assert modified.default == "modified"

    def test_change_annotation(self):
        """Can change annotation type."""
        original = FieldInfo(annotation=str)
        modified = modify_fieldinfo(original, annotation=int)

        assert modified.annotation is int
        assert original.annotation is str

    def test_change_default(self):
        """Can change default value."""
        original = FieldInfo(annotation=str)
        modified = modify_fieldinfo(original, default="new_default")

        assert modified.default == "new_default"

    def test_change_default_factory(self):
        """Can change default_factory."""
        original = FieldInfo(annotation=list)
        modified = modify_fieldinfo(original, default_factory=list)

        assert modified.default_factory is list

    def test_change_multiple_attrs(self):
        """Can change multiple attributes at once."""
        original = FieldInfo(annotation=str, default="old")
        modified = modify_fieldinfo(original, annotation=int, default=42, description="New description")

        assert modified.annotation is int
        assert modified.default == 42
        assert modified.description == "New description"

    def test_invalid_attribute_raises_error(self):
        """Raises ValueError for invalid attributes."""
        original = FieldInfo(annotation=str)

        with pytest.raises(ValueError, match="Invalid FieldInfo attributes"):
            modify_fieldinfo(original, nonexistent_attr="value")

    def test_metadata_callback(self):
        """metadata_callback can transform metadata list."""
        original = FieldInfo(annotation=str)
        original.metadata = ["original"]  # Assign metadata directly
        modified = modify_fieldinfo(original, metadata_callback=lambda meta: meta + ["added"])

        assert "original" in modified.metadata
        assert "added" in modified.metadata

    def test_metadata_callback_replace(self):
        """metadata_callback can replace metadata entirely."""
        original = FieldInfo(annotation=str)
        original.metadata = ["original"]  # Assign metadata directly
        modified = modify_fieldinfo(original, metadata_callback=lambda meta: ["replaced"])

        assert modified.metadata == ["replaced"]

    def test_preserves_unmodified_attrs(self):
        """Unmodified attributes are preserved."""
        original = FieldInfo(annotation=str, default="default", description="Description", title="Title")
        modified = modify_fieldinfo(original, default="new_default")

        assert modified.description == "Description"
        assert modified.title == "Title"
        assert modified.default == "new_default"

    def test_with_field_from_model(self):
        """Works with FieldInfo extracted from a model."""

        class User(BaseModel):
            name: str = Field(default="Anonymous", description="User's name")

        original = User.model_fields["name"]
        modified = modify_fieldinfo(original, default="Modified")

        assert modified.default == "Modified"
        assert modified.description == "User's name"
