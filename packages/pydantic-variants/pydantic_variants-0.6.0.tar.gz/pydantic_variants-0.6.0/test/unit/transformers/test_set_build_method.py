"""Tests for SetBuildMethod transformer."""

import pytest
from pydantic import BaseModel

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import BuildVariant, SetBuildMethod


class TestSetBuildMethod:
    """Tests for SetBuildMethod transformer."""

    def test_set_build_method_basic(self):
        """Test setting a basic build method."""

        class User(BaseModel):
            name: str
            email: str

        def build_output(self):
            return self.Output.model_validate(self.model_dump())

        ctx = VariantContext("Output")(User)
        ctx = BuildVariant()(ctx)
        ctx = SetBuildMethod("build_output", build_output)(ctx)

        assert hasattr(User, "build_output")
        assert User.build_output == build_output  # type: ignore[attr-defined]

    def test_set_build_method_lambda(self):
        """Test setting a lambda as build method."""

        class User(BaseModel):
            name: str

        build_fn = lambda self: {"name": self.name}  # noqa: E731

        ctx = VariantContext("Output")(User)
        ctx = BuildVariant()(ctx)
        ctx = SetBuildMethod("build_output", build_fn)(ctx)

        assert hasattr(User, "build_output")  # type: ignore[attr-defined]

    def test_set_build_method_error_on_decomposed(self):
        """Test error when used before BuildVariant."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Output")(User)
        # Not calling BuildVariant - still DecomposedModel

        with pytest.raises(ValueError, match="requires built model"):
            SetBuildMethod("build_output", lambda self: None)(ctx)

    def test_set_build_method_callable(self):
        """Test that the method is actually callable on instances."""

        class User(BaseModel):
            name: str
            email: str

        def build_output(self):
            # Return a simple dict representation
            return {"name": self.name}

        ctx = VariantContext("Output")(User)
        ctx = BuildVariant()(ctx)
        ctx = SetBuildMethod("build_output", build_output)(ctx)

        # Create an instance and call the method
        user = User(name="John", email="john@example.com")
        result = user.build_output()  # type: ignore[attr-defined]

        assert result == {"name": "John"}

    def test_set_build_method_returns_context(self):
        """Test that SetBuildMethod returns the context."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Output")(User)
        ctx = BuildVariant()(ctx)
        result = SetBuildMethod("build_output", lambda self: None)(ctx)

        assert isinstance(result, VariantContext)
