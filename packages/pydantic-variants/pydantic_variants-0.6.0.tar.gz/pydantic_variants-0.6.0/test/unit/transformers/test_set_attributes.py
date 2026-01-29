"""
Tests for SetAttribute transformer.
"""

import pytest
from pydantic import BaseModel

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import BuildVariant, SetAttribute


class TestSetAttribute:
    """Tests for SetAttribute transformer."""

    def get_built_context(self, model_cls, name="Test"):
        """Helper to create a built VariantContext for a model."""
        ctx = VariantContext(name)
        ctx(model_cls)
        build_op = BuildVariant()
        return build_op(ctx)

    def test_set_variant_attr(self):
        """Sets attribute on variant model."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute(variant_attrs={"_version": "1.0.0"})
        set_op(ctx)

        assert ctx.current_variant._version == "1.0.0"  # type: ignore[attr-defined]

    def test_set_root_attr(self):
        """Sets attribute on root model."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute(root_attrs={"_has_variants": True})
        set_op(ctx)

        assert User._has_variants is True  # type: ignore[attr-defined]

    def test_set_both_attrs(self):
        """Sets attributes on both variant and root."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute(variant_attrs={"_variant_version": "2.0"}, root_attrs={"_root_version": "1.0"})
        set_op(ctx)

        assert ctx.current_variant._variant_version == "2.0"  # type: ignore[attr-defined]
        assert User._root_version == "1.0"  # type: ignore[attr-defined]

    def test_set_callable_attr(self):
        """Can set callable attributes."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_built_context(User)

        def custom_func(self):
            return f"User: {self.name}"

        set_op = SetAttribute(variant_attrs={"describe": custom_func})
        set_op(ctx)

        assert ctx.current_variant.describe is custom_func  # type: ignore[attr-defined]

    def test_multiple_attrs_on_variant(self):
        """Sets multiple attributes on variant."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute(variant_attrs={"_schema_version": "2.1.0", "_is_input": True, "_validators_enabled": False})
        set_op(ctx)

        assert ctx.current_variant._schema_version == "2.1.0"  # type: ignore[attr-defined]
        assert ctx.current_variant._is_input is True  # type: ignore[attr-defined]
        assert ctx.current_variant._validators_enabled is False  # type: ignore[attr-defined]

    def test_error_variant_attrs_on_decomposed(self):
        """Raises error if variant_attrs used on DecomposedModel."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx(User)  # current_variant is DecomposedModel

        set_op = SetAttribute(variant_attrs={"_test": True})

        with pytest.raises(ValueError, match="requires built model"):
            set_op(ctx)

    def test_root_attrs_works_on_decomposed(self):
        """root_attrs works even before BuildVariant."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx(User)  # current_variant is DecomposedModel

        set_op = SetAttribute(root_attrs={"_test": True})
        set_op(ctx)  # Should not raise

        assert User._test is True  # type: ignore[attr-defined]

    def test_empty_attrs_no_error(self):
        """Empty attrs dicts don't cause errors."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute()  # Both default to None
        result = set_op(ctx)

        assert result is ctx  # Just passes through

    def test_returns_context(self):
        """Returns context for pipeline chaining."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User)
        set_op = SetAttribute(variant_attrs={"_test": True})
        result = set_op(ctx)

        assert result is ctx
