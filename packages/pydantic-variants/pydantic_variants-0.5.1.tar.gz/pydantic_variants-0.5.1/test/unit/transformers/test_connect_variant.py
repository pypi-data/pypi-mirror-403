"""
Tests for ConnectVariant transformer.
"""

import pytest
from pydantic import BaseModel

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import BuildVariant, ConnectVariant


class TestConnectVariant:
    """Tests for ConnectVariant transformer."""

    def get_built_context(self, model_cls, name="Test"):
        """Helper to create a built VariantContext for a model."""
        ctx = VariantContext(name)
        ctx(model_cls)
        build_op = BuildVariant()
        return build_op(ctx)

    def test_attaches_to_variants_dict(self):
        """Variant is added to _variants dict on original model."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        connect_op = ConnectVariant()
        connect_op(ctx)

        assert hasattr(User, "_variants")  # type: ignore[attr-defined]
        assert "Input" in User._variants  # type: ignore[attr-defined]
        assert User._variants["Input"].__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_attaches_directly_as_attribute(self):
        """Variant is attached as class attribute when attach_directly=True."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        connect_op = ConnectVariant(attach_directly=True)
        connect_op(ctx)

        assert hasattr(User, "Input")  # type: ignore[attr-defined]
        assert User.Input.__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_no_direct_attachment(self):
        """Variant is not attached as attribute when attach_directly=False."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Output")
        connect_op = ConnectVariant(attach_directly=False)
        connect_op(ctx)

        # Should be in _variants but not as direct attribute
        assert "Output" in User._variants  # type: ignore[attr-defined]
        assert not hasattr(User, "Output") or User.Output is None  # type: ignore[attr-defined]

    def test_attaches_root_model(self):
        """Variant has _root_model pointing to original when attach_root=True."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        connect_op = ConnectVariant(attach_root=True)
        connect_op(ctx)

        assert hasattr(User.Input, "_root_model")  # type: ignore[attr-defined]
        assert User.Input._root_model is User  # type: ignore[attr-defined]

    def test_no_root_attachment(self):
        """Variant does not have _root_model when attach_root=False."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        connect_op = ConnectVariant(attach_root=False)
        connect_op(ctx)

        assert not hasattr(User._variants["Input"], "_root_model")  # type: ignore[attr-defined]

    def test_multiple_variants_same_model(self):
        """Multiple variants can be attached to same model."""

        class User(BaseModel):
            id: int
            name: str

        # Attach Input variant
        ctx1 = self.get_built_context(User, "Input")
        ConnectVariant()(ctx1)

        # Attach Output variant
        ctx2 = self.get_built_context(User, "Output")
        ConnectVariant()(ctx2)

        assert "Input" in User._variants  # type: ignore[attr-defined]
        assert "Output" in User._variants  # type: ignore[attr-defined]
        assert hasattr(User, "Input")  # type: ignore[attr-defined]
        assert hasattr(User, "Output")  # type: ignore[attr-defined]

    def test_error_on_decomposed_model(self):
        """Raises error if current_variant is still DecomposedModel."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx(User)  # current_variant is DecomposedModel

        connect_op = ConnectVariant()

        with pytest.raises(ValueError, match="requires built model"):
            connect_op(ctx)

    def test_returns_context(self):
        """Returns the context for pipeline chaining."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        connect_op = ConnectVariant()
        result = connect_op(ctx)

        assert result is ctx

    def test_variant_is_same_instance_in_dict_and_attr(self):
        """Direct attribute and _variants dict entry are same instance."""

        class User(BaseModel):
            id: int

        ctx = self.get_built_context(User, "Input")
        ConnectVariant()(ctx)

        assert User.Input is User._variants["Input"]  # type: ignore[attr-defined]
