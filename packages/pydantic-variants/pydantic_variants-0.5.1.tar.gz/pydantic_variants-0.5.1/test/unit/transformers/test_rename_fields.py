"""
Tests for RenameFields transformer.
"""

import pytest
import re
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import RenameFields


class TestRenameFields:
    """Tests for RenameFields transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_rename_single_field(self):
        """Renames a single field."""

        class User(BaseModel):
            user_id: int
            name: str

        ctx = self.get_context(User)
        rename_op = RenameFields(mapping={"user_id": "id"})
        result = rename_op(ctx)

        assert "id" in result.current_variant.model_fields
        assert "user_id" not in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_rename_multiple_fields(self):
        """Renames multiple fields."""

        class User(BaseModel):
            user_id: int
            email_addr: str
            full_name: str

        ctx = self.get_context(User)
        rename_op = RenameFields(mapping={"user_id": "id", "email_addr": "email", "full_name": "name"})
        result = rename_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"id", "email", "name"}

    def test_rename_preserves_field_info(self):
        """Field metadata is preserved after rename."""

        class User(BaseModel):
            user_name: str = Field(description="User's name", min_length=1)

        ctx = self.get_context(User)
        rename_op = RenameFields(mapping={"user_name": "name"})
        result = rename_op(ctx)

        name_field = result.current_variant.model_fields["name"]
        assert name_field.description == "User's name"

    def test_rename_func_simple(self):
        """rename_func with simple transformation."""

        class User(BaseModel):
            user_id: int
            user_name: str
            user_email: str

        ctx = self.get_context(User)
        # Remove user_ prefix
        rename_op = RenameFields(rename_func=lambda name: name.replace("user_", ""))
        result = rename_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"id", "name", "email"}

    def test_rename_func_regex(self):
        """rename_func with regex pattern."""

        class User(BaseModel):
            user_id: int
            account_id: int
            name: str

        ctx = self.get_context(User)
        # Remove _id suffix
        rename_op = RenameFields(rename_func=lambda name: re.sub(r"_id$", "", name))
        result = rename_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"user", "account", "name"}

    def test_rename_func_camel_case(self):
        """rename_func converts snake_case to camelCase."""

        class User(BaseModel):
            first_name: str
            last_name: str
            email_address: str

        ctx = self.get_context(User)

        def to_camel(name: str) -> str:
            components = name.split("_")
            return components[0] + "".join(x.title() for x in components[1:])

        rename_op = RenameFields(rename_func=to_camel)
        result = rename_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"firstName", "lastName", "emailAddress"}

    def test_rename_func_returns_none_keeps_original(self):
        """When rename_func returns None, original name is kept."""

        class User(BaseModel):
            old_id: int
            name: str

        ctx = self.get_context(User)
        # Only rename fields starting with old_
        rename_op = RenameFields(rename_func=lambda name: name.replace("old_", "new_") if name.startswith("old_") else None)
        result = rename_op(ctx)

        assert "new_id" in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_error_no_options(self):
        """Raises error when neither mapping nor rename_func provided."""
        with pytest.raises(ValueError, match="Must provide either"):
            RenameFields()

    def test_error_both_options(self):
        """Raises error when both mapping and rename_func provided."""
        with pytest.raises(ValueError, match="Must provide either"):
            RenameFields(mapping={"a": "b"}, rename_func=lambda x: x)

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        rename_op = RenameFields(mapping={"id": "identifier"})

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            rename_op(ctx)

    def test_mapping_missing_field_ignored(self):
        """Mapping for non-existent field is silently ignored."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        rename_op = RenameFields(mapping={"id": "identifier", "nonexistent": "still_nonexistent"})
        result = rename_op(ctx)

        fields = set(result.current_variant.model_fields.keys())
        assert fields == {"identifier", "name"}

    def test_rename_preserves_field_order(self):
        """Field order is preserved after renaming."""

        class User(BaseModel):
            first: str
            second: str
            third: str

        ctx = self.get_context(User)
        rename_op = RenameFields(mapping={"second": "middle"})
        result = rename_op(ctx)

        fields = list(result.current_variant.model_fields.keys())
        assert fields == ["first", "middle", "third"]
