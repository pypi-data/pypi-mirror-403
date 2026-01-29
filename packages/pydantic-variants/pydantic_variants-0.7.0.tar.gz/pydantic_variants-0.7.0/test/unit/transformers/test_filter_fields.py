"""
Tests for FilterFields transformer.
"""

import pytest
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import FilterFields


class TestFilterFields:
    """Tests for FilterFields transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_exclude_single_field(self):
        """Excludes a single field."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude=["id"])
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields
        assert "email" in result.current_variant.model_fields

    def test_exclude_multiple_fields(self):
        """Excludes multiple fields."""

        class User(BaseModel):
            id: int
            name: str
            email: str
            password: str

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude=["id", "password"])
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields
        assert "password" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields
        assert "email" in result.current_variant.model_fields

    def test_include_only_single(self):
        """Keeps only specified fields."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        filter_op = FilterFields(include_only=["name"])
        result = filter_op(ctx)

        assert list(result.current_variant.model_fields.keys()) == ["name"]

    def test_include_only_multiple(self):
        """Keeps only multiple specified fields."""

        class User(BaseModel):
            id: int
            name: str
            email: str
            password: str

        ctx = self.get_context(User)
        filter_op = FilterFields(include_only=["name", "email"])
        result = filter_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"name", "email"}

    def test_filter_func_custom_logic(self):
        """Custom filter function works."""

        class User(BaseModel):
            id: int
            name: str
            internal_id: str
            internal_notes: str

        ctx = self.get_context(User)
        # Filter out fields starting with "internal_"
        filter_op = FilterFields(filter_func=lambda name, field: name.startswith("internal_"))
        result = filter_op(ctx)

        assert "internal_id" not in result.current_variant.model_fields
        assert "internal_notes" not in result.current_variant.model_fields
        assert "id" in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_filter_func_by_annotation(self):
        """Can filter by field annotation type."""

        class User(BaseModel):
            id: int
            name: str
            count: int
            email: str

        ctx = self.get_context(User)
        # Filter out all int fields
        filter_op = FilterFields(filter_func=lambda name, field: field.annotation is int)
        result = filter_op(ctx)

        assert "id" not in result.current_variant.model_fields
        assert "count" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields
        assert "email" in result.current_variant.model_fields

    def test_preserves_field_metadata(self):
        """Field metadata is preserved after filtering."""

        class User(BaseModel):
            id: int
            name: str = Field(description="User's name", min_length=1)

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude=["id"])
        result = filter_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.description == "User's name"

    def test_empty_exclude_keeps_all(self):
        """Empty exclude list keeps all fields."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude=[])
        result = filter_op(ctx)

        assert len(result.current_variant.model_fields) == 2

    def test_nonexistent_field_in_exclude(self):
        """Excluding non-existent field is silently ignored."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude=["nonexistent", "also_missing"])
        result = filter_op(ctx)

        # All original fields should remain
        assert len(result.current_variant.model_fields) == 2

    def test_error_no_options(self):
        """Raises error when no filtering option provided."""
        with pytest.raises(ValueError, match="Must provide one of"):
            FilterFields()

    def test_error_multiple_options(self):
        """Raises error when multiple options provided."""
        with pytest.raises(ValueError, match="Must provide one of"):
            FilterFields(exclude=["id"], include_only=["name"])

    def test_error_on_built_model(self):
        """Raises error when applied to built model (not DecomposedModel)."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model, not DecomposedModel

        filter_op = FilterFields(exclude=["id"])

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            filter_op(ctx)

    def test_filter_with_sets(self):
        """Works with set input for exclude/include_only."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        filter_op = FilterFields(exclude={"id", "email"})  # Set instead of list
        result = filter_op(ctx)

        assert list(result.current_variant.model_fields.keys()) == ["name"]
