"""
Tests for BuildVariant transformer.
"""

import pytest
from pydantic import BaseModel, Field

from pydantic_variants.core import VariantContext, DecomposedModel
from pydantic_variants.transformers import BuildVariant


class TestBuildVariant:
    """Tests for BuildVariant transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_builds_pydantic_model(self):
        """Builds a valid Pydantic model from DecomposedModel."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        # current_variant should now be a type, not DecomposedModel
        assert not isinstance(result.current_variant, DecomposedModel)  # type: ignore[attr-defined]
        assert issubclass(result.current_variant, BaseModel)

    def test_model_name_includes_context_name(self):
        """Built model name includes the context name."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Input")
        ctx(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        assert result.current_variant.__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_name_suffix_appended(self):
        """name_suffix is appended to model name."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("API")
        ctx(User)
        build_op = BuildVariant(name_suffix="V2")
        result = build_op(ctx)

        assert result.current_variant.__name__ == "UserAPIV2"  # type: ignore[attr-defined]

    def test_custom_docstring(self):
        """Custom doc is applied to built model."""

        class User(BaseModel):
            """Original doc."""

            id: int

        ctx = self.get_context(User)
        build_op = BuildVariant(doc="Custom documentation")
        result = build_op(ctx)

        assert result.current_variant.__doc__ == "Custom documentation"

    def test_preserves_original_docstring(self):
        """Original docstring is preserved if no custom doc."""

        class User(BaseModel):
            """Original documentation."""

            id: int

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        assert result.current_variant.__doc__ == "Original documentation."

    def test_custom_base_class(self):
        """Built model inherits from custom base."""

        class CustomBase(BaseModel):
            custom_field: str = "custom"

        class User(BaseModel):
            id: int

        ctx = self.get_context(User)
        build_op = BuildVariant(base=CustomBase)
        result = build_op(ctx)

        assert issubclass(result.current_variant, CustomBase)  # type: ignore[attr-defined]
        # Should have fields from both
        assert "id" in result.current_variant.model_fields  # type: ignore[attr-defined]
        assert "custom_field" in result.current_variant.model_fields  # type: ignore[attr-defined]

    def test_preserves_module(self):
        """Built model has same __module__ as original."""

        class User(BaseModel):
            id: int

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        assert result.current_variant.__module__ == User.__module__

    def test_built_model_is_functional(self):
        """Built model can be instantiated and validates."""

        class User(BaseModel):
            id: int
            name: str = Field(min_length=1)

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        # Should be able to create instances
        instance = result.current_variant(id=1, name="John")  # pyright: ignore[reportCallIssue]
        assert instance.id == 1  # type: ignore[attr-defined]
        assert instance.name == "John"  # type: ignore[attr-defined]

        # Should validate
        with pytest.raises(Exception):  # ValidationError
            result.current_variant(id=1, name="")  # pyright: ignore[reportCallIssue] # min_length=1

    def test_error_on_already_built_model(self):
        """Raises error if current_variant is already built."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Already a model, not DecomposedModel

        build_op = BuildVariant()

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            build_op(ctx)

    def test_preserves_field_annotations(self):
        """Field annotations are preserved in built model."""
        from typing import Optional, List

        class User(BaseModel):
            id: int
            tags: List[str]
            bio: Optional[str] = None

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        fields = result.current_variant.model_fields
        assert fields["id"].annotation is int
        assert fields["tags"].annotation is List[str]

    def test_preserves_field_defaults(self):
        """Field defaults are preserved in built model."""

        class User(BaseModel):
            name: str = "Anonymous"
            count: int = 0

        ctx = self.get_context(User)
        build_op = BuildVariant()
        result = build_op(ctx)

        fields = result.current_variant.model_fields
        assert fields["name"].default == "Anonymous"
        assert fields["count"].default == 0
