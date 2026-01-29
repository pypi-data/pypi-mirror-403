"""
Tests for FilterTag transformer and Tag class.
"""

import pytest
from typing import Annotated
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import FilterTag, Tag


class TestTag:
    """Tests for Tag class."""

    def test_tag_equality_same_key(self):
        """Tags with same key are equal."""
        tag1 = Tag("internal")
        tag2 = Tag("internal")

        assert tag1 == tag2

    def test_tag_equality_different_key(self):
        """Tags with different keys are not equal."""
        tag1 = Tag("internal")
        tag2 = Tag("admin")

        assert tag1 != tag2

    def test_tag_hash(self):
        """Tags with same key have same hash."""
        tag1 = Tag("internal")
        tag2 = Tag("internal")

        assert hash(tag1) == hash(tag2)
        # Can be used in sets
        assert len({tag1, tag2}) == 1

    def test_tag_repr(self):
        """Tag repr shows the key."""
        tag = Tag("internal")
        assert repr(tag) == "Tag('internal')"

    def test_in_field_with_annotated(self):
        """Tag.in_field works with Annotated metadata."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            name: str

        internal_tag = Tag("internal")
        id_field = User.model_fields["id"]
        name_field = User.model_fields["name"]

        assert internal_tag.in_field(id_field) is True
        assert internal_tag.in_field(name_field) is False

    def test_in_field_with_field_metadata(self):
        """Tag.in_field works with Field(metadata=[...])."""

        class User(BaseModel):
            id: int = Field(metadata=[Tag("internal")])  # type: ignore[attr-defined]
            name: str

        internal_tag = Tag("internal")
        id_field = User.model_fields["id"]
        name_field = User.model_fields["name"]

        # This tests the fix for json_schema_extra['metadata']
        assert internal_tag.in_field(id_field) is True
        assert internal_tag.in_field(name_field) is False

    def test_in_field_no_metadata(self):
        """Returns False for fields without metadata."""

        class User(BaseModel):
            id: int
            name: str

        tag = Tag("any")

        assert tag.in_field(User.model_fields["id"]) is False
        assert tag.in_field(User.model_fields["name"]) is False

    def test_in_field_different_tag(self):
        """Returns False when tag key doesn't match."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]

        admin_tag = Tag("admin")

        assert admin_tag.in_field(User.model_fields["id"]) is False

    def test_in_field_multiple_tags(self):
        """Works with multiple tags on same field."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal"), Tag("admin")]

        internal_tag = Tag("internal")
        admin_tag = Tag("admin")
        other_tag = Tag("other")

        id_field = User.model_fields["id"]

        assert internal_tag.in_field(id_field) is True
        assert admin_tag.in_field(id_field) is True
        assert other_tag.in_field(id_field) is False


class TestFilterTag:
    """Tests for FilterTag transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_filter_single_tag_annotated(self):
        """Filters field with single tag (Annotated)."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            name: str

        ctx = self.get_context(User)
        filter_op = FilterTag("internal")
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_filter_single_tag_field_metadata(self):
        """Filters field with single tag (Field metadata)."""

        class User(BaseModel):
            id: int = Field(metadata=[Tag("internal")])  # type: ignore[attr-defined]
            name: str

        ctx = self.get_context(User)
        filter_op = FilterTag("internal")
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_filter_multiple_tags(self):
        """Filters fields matching any of multiple tag keys."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            password: Annotated[str, Tag("secret")]
            name: str

        ctx = self.get_context(User)
        filter_op = FilterTag(["internal", "secret"])
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields  # type: ignore[attr-defined]
        assert "password" not in result.current_variant.model_fields  # type: ignore[attr-defined]
        assert "name" in result.current_variant.model_fields  # type: ignore[attr-defined]

    def test_filter_no_matching_tags(self):
        """No fields filtered when no tags match."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        filter_op = FilterTag("internal")
        result = filter_op(ctx)

        assert len(result.current_variant.model_fields) == 2

    def test_filter_all_fields_with_tag(self):
        """Filters all fields if all have matching tag."""

        class User(BaseModel):
            id: Annotated[int, Tag("remove")]
            name: Annotated[str, Tag("remove")]

        ctx = self.get_context(User)
        filter_op = FilterTag("remove")
        result = filter_op(ctx)

        assert len(result.current_variant.model_fields) == 0

    def test_mixed_annotated_and_field_metadata(self):
        """Works with mix of Annotated and Field metadata."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            secret: str = Field(metadata=[Tag("internal")])  # type: ignore[attr-defined]
            name: str

        ctx = self.get_context(User)
        filter_op = FilterTag("internal")
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields  # type: ignore[attr-defined]
        assert "secret" not in result.current_variant.model_fields  # type: ignore[attr-defined]
        assert "name" in result.current_variant.model_fields  # type: ignore[attr-defined]

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        filter_op = FilterTag("internal")

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            filter_op(ctx)

    def test_preserves_untagged_field_metadata(self):
        """Preserves metadata on fields that aren't filtered."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            name: str = Field(description="User name", min_length=1)

        ctx = self.get_context(User)
        filter_op = FilterTag("internal")
        result = filter_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.description == "User name"
