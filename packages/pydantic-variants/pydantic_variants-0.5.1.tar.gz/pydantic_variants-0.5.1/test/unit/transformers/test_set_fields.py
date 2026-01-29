"""
Tests for SetFields transformer.
"""

import pytest
from pydantic import BaseModel, Field
from pydantic.fields import FieldInfo

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import SetFields


class TestSetFields:
    """Tests for SetFields transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_add_new_field(self):
        """Adds a new field to the model."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        set_op = SetFields({"email": FieldInfo(annotation=str, default="user@example.com")})
        result = set_op(ctx)

        assert "email" in result.current_variant.model_fields
        assert result.current_variant.model_fields["email"].default == "user@example.com"

    def test_add_multiple_fields(self):
        """Adds multiple new fields."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        set_op = SetFields(
            {
                "email": FieldInfo(annotation=str, default=""),
                "age": FieldInfo(annotation=int, default=0),
                "active": FieldInfo(annotation=bool, default=True),
            }
        )
        result = set_op(ctx)

        fields = result.current_variant.model_fields
        assert "email" in fields
        assert "age" in fields
        assert "active" in fields
        assert fields["email"].annotation is str
        assert fields["age"].annotation is int
        assert fields["active"].annotation is bool

    def test_override_existing_field(self):
        """Overrides an existing field completely."""

        class User(BaseModel):
            id: int
            name: str = Field(default="Original", description="Original desc")

        ctx = self.get_context(User)
        set_op = SetFields({"name": FieldInfo(annotation=str, default="Overridden", description="New desc")})
        result = set_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.default == "Overridden"
        assert name_field.description == "New desc"

    def test_preserves_other_fields(self):
        """Other fields are not affected."""

        class User(BaseModel):
            id: int = Field(description="User ID")
            name: str

        ctx = self.get_context(User)
        set_op = SetFields({"email": FieldInfo(annotation=str, default="")})
        result = set_op(ctx)

        assert result.current_variant.model_fields["id"].description == "User ID"
        assert "name" in result.current_variant.model_fields

    def test_field_with_factory(self):
        """Fields with default_factory work."""
        from uuid import uuid4

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        set_op = SetFields({"id": FieldInfo(annotation=str, default_factory=lambda: str(uuid4()))})
        result = set_op(ctx)

        id_field = result.current_variant.model_fields["id"]
        assert id_field.default_factory is not None

    def test_required_field(self):
        """Can add required fields (no default)."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        set_op = SetFields(
            {
                "email": FieldInfo(annotation=str)  # No default = required
            }
        )
        result = set_op(ctx)

        email_field = result.current_variant.model_fields["email"]
        assert email_field.is_required()

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        set_op = SetFields({"new": FieldInfo(annotation=str)})

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            set_op(ctx)

    def test_field_with_metadata(self):
        """Fields with metadata are added correctly."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        # Create FieldInfo and assign metadata directly
        field_with_meta = FieldInfo(annotation=str)
        field_with_meta.metadata = ["custom_meta"]
        set_op = SetFields({"tagged": field_with_meta})
        result = set_op(ctx)

        assert "custom_meta" in result.current_variant.model_fields["tagged"].metadata

    def test_empty_fields_dict(self):
        """Empty fields dict makes no changes."""

        class User(BaseModel):
            name: str

        ctx = self.get_context(User)
        set_op = SetFields({})
        result = set_op(ctx)

        assert list(result.current_variant.model_fields.keys()) == ["name"]
