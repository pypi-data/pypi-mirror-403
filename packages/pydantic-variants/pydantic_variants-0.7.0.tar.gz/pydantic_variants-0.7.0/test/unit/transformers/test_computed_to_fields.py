"""
Tests for ComputedToFields transformer.
"""

import pytest
from pydantic import BaseModel, computed_field
from pydantic.fields import FieldInfo

from pydantic_variants.core import DecomposedModel, VariantContext, VariantPipe
from pydantic_variants.transformers import ComputedToFields, Tag, computed_with_tags, BuildVariant


INTERNAL = Tag("internal")
USER_PRIVATE = Tag("user_private")
ADMIN = Tag("admin")


class UserModel(BaseModel):
    """Test model with computed fields."""

    id: str
    pin_hash: str | None = None
    name: str = "test"

    @computed_with_tags(USER_PRIVATE)
    @property
    def has_pin(self) -> bool:
        """Check if user has a PIN set."""
        return self.pin_hash is not None

    @computed_with_tags(INTERNAL)
    @property
    def internal_value(self) -> str:
        """An internal computed value."""
        return f"internal_{self.id}"

    @computed_with_tags(USER_PRIVATE, INTERNAL)
    @property
    def multi_tag_value(self) -> int:
        """Value with multiple tags."""
        return 42

    @computed_field
    @property
    def untagged_computed(self) -> str:
        """A computed field without tags (uses @computed_field)."""
        return f"untagged_{self.id}"


def get_context(model_cls):
    """Helper to create a VariantContext for a model."""
    ctx = VariantContext("Test")
    return ctx(model_cls)


class TestComputedToFieldsBasic:
    """Basic functionality tests."""

    def test_convert_all_tagged_computed_fields(self):
        """Convert all computed fields when no filter specified."""
        context = get_context(UserModel)

        transformer = ComputedToFields()
        result = transformer(context)

        # All tagged computed fields should be converted to regular fields
        assert "has_pin" in result.current_variant.model_fields
        assert "internal_value" in result.current_variant.model_fields
        assert "multi_tag_value" in result.current_variant.model_fields
        # Untagged computed field should also be converted (no filter)
        assert "untagged_computed" in result.current_variant.model_fields

        # Original model fields should still exist
        assert "id" in result.current_variant.model_fields
        assert "pin_hash" in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_new_field_has_correct_type(self):
        """Converted field should have the computed field's return type."""
        context = get_context(UserModel)

        transformer = ComputedToFields()
        result = transformer(context)

        has_pin_field = result.current_variant.model_fields["has_pin"]
        assert has_pin_field.annotation is bool

        internal_field = result.current_variant.model_fields["internal_value"]
        assert internal_field.annotation is str

        multi_tag_field = result.current_variant.model_fields["multi_tag_value"]
        assert multi_tag_field.annotation is int

    def test_new_field_has_docstring_as_description(self):
        """Converted field should have the docstring as description."""
        context = get_context(UserModel)

        transformer = ComputedToFields()
        result = transformer(context)

        has_pin_field = result.current_variant.model_fields["has_pin"]
        assert has_pin_field.description == "Check if user has a PIN set."

        internal_field = result.current_variant.model_fields["internal_value"]
        assert internal_field.description == "An internal computed value."

    def test_new_field_has_none_default(self):
        """Converted field should default to None (output-only)."""
        context = get_context(UserModel)

        transformer = ComputedToFields()
        result = transformer(context)

        has_pin_field = result.current_variant.model_fields["has_pin"]
        assert has_pin_field.default is None


class TestComputedToFieldsTagFilters:
    """Tests for tag-based filtering."""

    def test_include_single_tag(self):
        """Only convert fields with the specified tag."""
        context = get_context(UserModel)

        transformer = ComputedToFields(include=USER_PRIVATE)
        result = transformer(context)

        # Only USER_PRIVATE tagged fields should be converted
        assert "has_pin" in result.current_variant.model_fields
        assert "multi_tag_value" in result.current_variant.model_fields

        # INTERNAL-only tagged field should remain computed
        decorators = result.current_variant._pydantic_decorators
        assert "internal_value" in decorators.computed_fields

    def test_include_string_tag(self):
        """Include filter accepts string tag keys."""
        context = get_context(UserModel)

        transformer = ComputedToFields(include="user_private")
        result = transformer(context)

        assert "has_pin" in result.current_variant.model_fields
        assert "multi_tag_value" in result.current_variant.model_fields

    def test_include_multiple_tags(self):
        """Convert fields matching any of the included tags."""
        context = get_context(UserModel)

        transformer = ComputedToFields(include=[USER_PRIVATE, INTERNAL])
        result = transformer(context)

        # All tagged fields should be converted
        assert "has_pin" in result.current_variant.model_fields
        assert "internal_value" in result.current_variant.model_fields
        assert "multi_tag_value" in result.current_variant.model_fields

        # Untagged should remain computed
        decorators = result.current_variant._pydantic_decorators
        assert "untagged_computed" in decorators.computed_fields

    def test_exclude_single_tag(self):
        """Exclude fields with the specified tag from conversion."""
        context = get_context(UserModel)

        transformer = ComputedToFields(exclude=INTERNAL)
        result = transformer(context)

        # USER_PRIVATE-only field should be converted
        assert "has_pin" in result.current_variant.model_fields
        assert "untagged_computed" in result.current_variant.model_fields

        # INTERNAL tagged fields should remain computed
        decorators = result.current_variant._pydantic_decorators
        assert "internal_value" in decorators.computed_fields
        assert "multi_tag_value" in decorators.computed_fields

    def test_include_and_exclude_together(self):
        """Exclude is applied after include filter."""
        context = get_context(UserModel)

        # Include USER_PRIVATE, but exclude INTERNAL
        transformer = ComputedToFields(include=USER_PRIVATE, exclude=INTERNAL)
        result = transformer(context)

        # has_pin: USER_PRIVATE only → converted
        assert "has_pin" in result.current_variant.model_fields

        # multi_tag_value: USER_PRIVATE and INTERNAL → excluded
        decorators = result.current_variant._pydantic_decorators
        assert "multi_tag_value" in decorators.computed_fields


class TestComputedToFieldsCallableFilter:
    """Tests for callable-based filtering."""

    def test_include_with_callable(self):
        """Use callable to filter which fields to convert."""
        context = get_context(UserModel)

        # Only convert fields starting with 'has_'
        transformer = ComputedToFields(include=lambda name, info: name.startswith("has_"))
        result = transformer(context)

        assert "has_pin" in result.current_variant.model_fields

        decorators = result.current_variant._pydantic_decorators
        assert "internal_value" in decorators.computed_fields
        assert "multi_tag_value" in decorators.computed_fields
        assert "untagged_computed" in decorators.computed_fields

    def test_exclude_with_callable(self):
        """Use callable to exclude fields from conversion."""
        context = get_context(UserModel)

        # Exclude fields with 'internal' in the name
        transformer = ComputedToFields(exclude=lambda name, info: "internal" in name)
        result = transformer(context)

        # All except internal_value should be converted
        assert "has_pin" in result.current_variant.model_fields
        assert "multi_tag_value" in result.current_variant.model_fields
        assert "untagged_computed" in result.current_variant.model_fields

        decorators = result.current_variant._pydantic_decorators
        assert "internal_value" in decorators.computed_fields


class TestComputedToFieldsWithPipeline:
    """Integration tests with variant pipelines."""

    def test_pipeline_with_computed_to_fields(self):
        """ComputedToFields works in a pipeline before BuildVariant."""
        ctx = VariantContext("user_view")
        ctx(UserModel)
        
        transformer1 = ComputedToFields(include=USER_PRIVATE)
        transformer2 = BuildVariant()
        
        ctx = transformer1(ctx)
        ctx = transformer2(ctx)
        
        UserView = ctx.current_variant

        # The built model should have has_pin as a regular field
        assert "has_pin" in UserView.model_fields
        field = UserView.model_fields["has_pin"]
        assert isinstance(field, FieldInfo)
        assert field.annotation is bool

    def test_built_model_can_be_instantiated(self):
        """Built model with converted fields can be instantiated."""
        ctx = VariantContext("user_view")
        ctx(UserModel)
        
        transformer1 = ComputedToFields(include=USER_PRIVATE)
        transformer2 = BuildVariant()
        
        ctx = transformer1(ctx)
        ctx = transformer2(ctx)
        
        UserView = ctx.current_variant

        # Create an instance
        instance = UserView(id="1", has_pin=True)
        assert instance.id == "1"
        assert instance.has_pin is True

    def test_serialization_of_built_model(self):
        """Built model can be serialized correctly."""
        ctx = VariantContext("user_view")
        ctx(UserModel)
        
        transformer1 = ComputedToFields(include=USER_PRIVATE)
        transformer2 = BuildVariant()
        
        ctx = transformer1(ctx)
        ctx = transformer2(ctx)
        
        UserView = ctx.current_variant

        instance = UserView(id="1", has_pin=True)
        data = instance.model_dump()

        assert data["id"] == "1"
        assert data["has_pin"] is True


class TestComputedToFieldsEdgeCases:
    """Edge case tests."""

    def test_requires_decomposed_model(self):
        """Transformer raises ValueError if not given DecomposedModel."""
        context = VariantContext("Test")
        context.original_model = UserModel
        context.current_variant = UserModel  # Not a DecomposedModel

        transformer = ComputedToFields()

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            transformer(context)

    def test_model_without_computed_fields(self):
        """Handles models without computed fields gracefully."""

        class SimpleModel(BaseModel):
            id: str
            name: str

        context = get_context(SimpleModel)

        transformer = ComputedToFields()
        result = transformer(context)

        # No changes, original fields remain
        assert "id" in result.current_variant.model_fields
        assert "name" in result.current_variant.model_fields

    def test_computed_field_without_docstring(self):
        """Handles computed fields without docstrings."""

        class NoDocModel(BaseModel):
            id: str

            @computed_with_tags(USER_PRIVATE)
            @property
            def computed_val(self) -> int:
                return 1

        context = get_context(NoDocModel)

        transformer = ComputedToFields()
        result = transformer(context)

        field = result.current_variant.model_fields["computed_val"]
        # Description is None when no docstring
        assert field.description is None
