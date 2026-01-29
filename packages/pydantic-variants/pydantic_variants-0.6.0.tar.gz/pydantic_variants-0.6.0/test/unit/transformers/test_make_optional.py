"""
Tests for MakeOptional transformer.
"""

import pytest
from typing import Union, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import MakeOptional, DefaultFactoryTag


class TestMakeOptional:
    """Tests for MakeOptional transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_all_optional(self):
        """all=True makes all required fields optional."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True)
        result = optional_op(ctx)

        for field_name, field in result.current_variant.model_fields.items():
            assert field.default is None, f"{field_name} should have None default"

    def test_exclude_specific(self):
        """exclude prevents specific fields from becoming optional."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        optional_op = MakeOptional(exclude=["id"])
        result = optional_op(ctx)

        # id should remain required
        assert result.current_variant.model_fields["id"].is_required()
        # Others should be optional
        assert result.current_variant.model_fields["name"].default is None
        assert result.current_variant.model_fields["email"].default is None

    def test_include_only(self):
        """include_only makes only specified fields optional."""

        class User(BaseModel):
            id: int
            name: str
            email: str

        ctx = self.get_context(User)
        optional_op = MakeOptional(include_only=["name"])
        result = optional_op(ctx)

        # Only name should be optional
        assert result.current_variant.model_fields["name"].default is None
        # Others should remain required
        assert result.current_variant.model_fields["id"].is_required()
        assert result.current_variant.model_fields["email"].is_required()

    def test_custom_defaults_dict(self):
        """Custom defaults can be provided via dict."""

        class User(BaseModel):
            id: int
            name: str
            count: int

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True, defaults={"name": "Anonymous", "count": 0})
        result = optional_op(ctx)

        assert result.current_variant.model_fields["name"].default == "Anonymous"
        assert result.current_variant.model_fields["count"].default == 0
        assert result.current_variant.model_fields["id"].default is None

    def test_default_factory_tag(self):
        """DefaultFactoryTag provides factory functions."""

        class User(BaseModel):
            id: int
            created_at: datetime

        ctx = self.get_context(User)

        # Use a custom factory function for reliable testing
        def custom_factory():
            return datetime.now()

        optional_op = MakeOptional(
            optional_func=lambda name, field: (True, DefaultFactoryTag(custom_factory) if name == "created_at" else None)
        )
        result = optional_op(ctx)

        # created_at should have a default_factory
        created_field = result.current_variant.model_fields["created_at"]
        assert created_field.default_factory is custom_factory

    def test_already_optional_field(self):
        """Already optional fields remain unchanged."""

        class User(BaseModel):
            id: int
            name: str | None = None
            bio: Optional[str] = "Default bio"

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True)
        result = optional_op(ctx)

        # These were already optional, should keep their defaults
        assert result.current_variant.model_fields["name"].default is None
        assert result.current_variant.model_fields["bio"].default == "Default bio"
        # id becomes optional
        assert result.current_variant.model_fields["id"].default is None

    def test_union_none_not_duplicated(self):
        """Doesn't duplicate None in Union types."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True)
        result = optional_op(ctx)

        # Annotation should include None
        annotation = result.current_variant.model_fields["name"].annotation
        # Should be Union[str, None] or str | None, not Union[str, None, None]
        assert annotation == Union[str, None] or annotation == (str | None)

    def test_optional_func_custom_logic(self):
        """optional_func allows custom logic."""

        class User(BaseModel):
            user_id: int
            name: str
            email: str

        ctx = self.get_context(User)
        # Make optional all fields ending with _id
        optional_op = MakeOptional(optional_func=lambda name, field: (name.endswith("_id"), None))
        result = optional_op(ctx)

        assert result.current_variant.model_fields["user_id"].default is None
        assert result.current_variant.model_fields["name"].is_required()
        assert result.current_variant.model_fields["email"].is_required()

    def test_error_no_options(self):
        """Raises error when no option provided."""
        with pytest.raises(ValueError, match="Must provide one of"):
            MakeOptional()

    def test_error_multiple_options(self):
        """Raises error when multiple options provided."""
        with pytest.raises(ValueError, match="Must provide one of"):
            MakeOptional(all=True, exclude=["id"])

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        optional_op = MakeOptional(all=True)

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            optional_op(ctx)

    def test_preserves_other_field_attrs(self):
        """Other field attributes are preserved."""

        class User(BaseModel):
            name: str = Field(description="User name", min_length=1)

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True)
        result = optional_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.description == "User name"

    def test_with_complex_union_types(self):
        """Handles complex Union types correctly."""

        class User(BaseModel):
            data: int | str  # Already a union

        ctx = self.get_context(User)
        optional_op = MakeOptional(all=True)
        result = optional_op(ctx)

        # Should now allow None as well
        data_field = result.current_variant.model_fields["data"]
        assert data_field.default is None
