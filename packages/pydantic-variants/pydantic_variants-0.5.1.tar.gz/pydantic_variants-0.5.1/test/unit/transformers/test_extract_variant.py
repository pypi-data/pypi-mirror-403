"""
Tests for ExtractVariant transformer.
"""

import pytest
from pydantic import BaseModel

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import BuildVariant
from pydantic_variants.transformers.extract_variant import ExtractVariant


class TestExtractVariant:
    """Tests for ExtractVariant transformer."""

    def test_returns_built_model(self):
        """Returns the built model from context."""

        class User(BaseModel):
            id: int
            name: str

        ctx = VariantContext("Input")
        ctx(User)
        BuildVariant()(ctx)

        extract_op = ExtractVariant()
        result = extract_op(ctx)

        assert issubclass(result, BaseModel)  # type: ignore[attr-defined]
        assert result.__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_error_on_decomposed_model(self):
        """Raises error if current_variant is still DecomposedModel."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx(User)  # current_variant is DecomposedModel

        extract_op = ExtractVariant()

        with pytest.raises(ValueError, match="requires built model"):
            extract_op(ctx)

    def test_returns_model_not_context(self):
        """Returns the model itself, not the context."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Input")
        ctx(User)
        BuildVariant()(ctx)

        extract_op = ExtractVariant()
        result = extract_op(ctx)

        # Should be the model, not the context
        assert result is ctx.current_variant
        assert not isinstance(result, VariantContext)

    def test_extracted_model_is_functional(self):
        """Extracted model can be instantiated."""

        class User(BaseModel):
            id: int
            name: str

        ctx = VariantContext("Input")
        ctx(User)
        BuildVariant()(ctx)

        ExtractedModel = ExtractVariant()(ctx)

        instance = ExtractedModel(id=1, name="John")
        assert instance.id == 1  # type: ignore[attr-defined]
        assert instance.name == "John"  # type: ignore[attr-defined]
