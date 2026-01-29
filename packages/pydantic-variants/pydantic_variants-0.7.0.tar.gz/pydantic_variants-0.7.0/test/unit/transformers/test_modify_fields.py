"""
Tests for ModifyFields transformer.
"""

import pytest
from typing import Annotated
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import ModifyFields, Tag


class TestModifyFields:
    """Tests for ModifyFields transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_modify_single_field(self):
        """Modifies a single field's attributes."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        modify_op = ModifyFields(field_modifications={"name": {"default": "Anonymous", "description": "User name"}})
        result = modify_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.default == "Anonymous"
        assert name_field.description == "User name"

    def test_modify_multiple_fields(self):
        """Modifies multiple fields."""

        class User(BaseModel):
            name: str
            email: str
            age: int

        ctx = self.get_context(User)
        modify_op = ModifyFields(
            field_modifications={"name": {"default": "Anonymous"}, "email": {"description": "Email address"}, "age": {"default": 0}}
        )
        result = modify_op(ctx)

        assert result.current_variant.model_fields["name"].default == "Anonymous"
        assert result.current_variant.model_fields["email"].description == "Email address"
        assert result.current_variant.model_fields["age"].default == 0

    def test_modify_annotation(self):
        """Can change field annotation."""

        class User(BaseModel):
            value: str

        ctx = self.get_context(User)
        modify_op = ModifyFields(field_modifications={"value": {"annotation": int}})
        result = modify_op(ctx)

        assert result.current_variant.model_fields["value"].annotation is int

    def test_modify_func_logic(self):
        """modify_func allows custom logic."""

        class User(BaseModel):
            name: str
            email: str
            password: str

        ctx = self.get_context(User)
        # Add description to all fields
        modify_op = ModifyFields(modify_func=lambda name, field: {"description": f"Field: {name}"})
        result = modify_op(ctx)

        assert result.current_variant.model_fields["name"].description == "Field: name"
        assert result.current_variant.model_fields["email"].description == "Field: email"
        assert result.current_variant.model_fields["password"].description == "Field: password"

    def test_modify_func_conditional(self):
        """modify_func can conditionally modify fields."""

        class User(BaseModel):
            public_name: str
            private_key: str

        ctx = self.get_context(User)
        # Only modify fields starting with public_
        modify_op = ModifyFields(modify_func=lambda name, field: {"title": "Public Field"} if name.startswith("public_") else None)
        result = modify_op(ctx)

        assert result.current_variant.model_fields["public_name"].title == "Public Field"
        assert result.current_variant.model_fields["private_key"].title is None

    def test_modify_with_metadata_callback(self):
        """metadata_callback can transform field metadata."""
        from typing import Annotated

        class User(BaseModel):
            name: Annotated[str, "original"]  # Use Annotated for proper metadata

        ctx = self.get_context(User)
        modify_op = ModifyFields(field_modifications={"name": {"metadata_callback": lambda meta: list(meta) + ["added"]}})
        result = modify_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert "original" in name_field.metadata
        assert "added" in name_field.metadata

    def test_tag_modifications(self):
        """tag_modifications modifies fields by tag."""

        class User(BaseModel):
            id: Annotated[int, Tag("internal")]
            secret: Annotated[str, Tag("internal")]
            name: str

        ctx = self.get_context(User)
        modify_op = ModifyFields(tag_modifications={Tag("internal"): {"description": "Internal field"}})
        result = modify_op(ctx)

        assert result.current_variant.model_fields["id"].description == "Internal field"
        assert result.current_variant.model_fields["secret"].description == "Internal field"
        assert result.current_variant.model_fields["name"].description is None

    def test_error_no_options(self):
        """Raises error when no option provided."""
        with pytest.raises(ValueError, match="Must provide either"):
            ModifyFields()

    def test_error_multiple_options(self):
        """Raises error when multiple options provided."""
        with pytest.raises(ValueError, match="Must provide either"):
            ModifyFields(field_modifications={"a": {}}, modify_func=lambda n, f: {})

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        modify_op = ModifyFields(field_modifications={"id": {"default": 0}})

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            modify_op(ctx)

    def test_preserves_unmodified_attrs(self):
        """Unmodified attributes are preserved."""

        class User(BaseModel):
            name: str = Field(description="Original", title="Name Field")

        ctx = self.get_context(User)
        modify_op = ModifyFields(field_modifications={"name": {"default": "Modified default"}})
        result = modify_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.description == "Original"
        assert name_field.title == "Name Field"
        assert name_field.default == "Modified default"

    def test_nonexistent_field_ignored(self):
        """Modifications for non-existent fields are ignored."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        modify_op = ModifyFields(field_modifications={"name": {"default": "Modified"}, "nonexistent": {"default": "Ignored"}})
        result = modify_op(ctx)

        # Should not raise, just modify existing fields
        assert result.current_variant.model_fields["name"].default == "Modified"
        assert "nonexistent" not in result.current_variant.model_fields
