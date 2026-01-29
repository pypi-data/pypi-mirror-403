"""
Tests for ModelDict transformer.
"""

import pytest
from pydantic import BaseModel

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import ModelDict
from pydantic_variants.transformers import BuildVariant


class TestModelDict:
    """Tests for ModelDict transformer."""

    def get_context(self, model_cls):
        """Helper to create a VariantContext for a model."""
        ctx = VariantContext("Test")
        return ctx(model_cls)

    def test_modify_config(self):
        """Modifies model config using function."""

        class User(BaseModel):
            id: int

        ctx = self.get_context(User)
        config_op = ModelDict(lambda config: {**config, "frozen": True})
        result = config_op(ctx)

        assert result.current_variant.model_config["frozen"] is True  # type: ignore[attr-defined]

    def test_add_multiple_config_options(self):
        """Adds multiple config options."""

        class User(BaseModel):
            id: int

        ctx = self.get_context(User)
        config_op = ModelDict(lambda config: {**config, "frozen": True, "extra": "forbid", "strict": True})
        result = config_op(ctx)

        config = result.current_variant.model_config  # type: ignore[attr-defined]
        assert config["frozen"] is True  # type: ignore[attr-defined]
        assert config["extra"] == "forbid"  # type: ignore[attr-defined]
        assert config["strict"] is True  # type: ignore[attr-defined]

    def test_replace_config_entirely(self):
        """Can replace config entirely (ignoring original)."""

        class User(BaseModel):
            model_config = {"extra": "allow", "frozen": False}
            id: int

        ctx = self.get_context(User)
        config_op = ModelDict(lambda config: {"strict": True})
        result = config_op(ctx)

        config = result.current_variant.model_config
        # Original config should be gone
        assert config.get("extra") is None
        assert config.get("frozen") is None
        assert config["strict"] is True  # type: ignore[attr-defined]

    def test_preserve_original_config(self):
        """Can preserve and extend original config."""

        class User(BaseModel):
            model_config = {"extra": "forbid", "populate_by_name": True}
            id: int

        ctx = self.get_context(User)
        config_op = ModelDict(lambda config: {**config, "frozen": True})
        result = config_op(ctx)

        config = result.current_variant.model_config
        assert config["extra"] == "forbid"  # type: ignore[attr-defined]
        assert config["populate_by_name"] is True  # type: ignore[attr-defined]
        assert config["frozen"] is True  # type: ignore[attr-defined]

    def test_conditional_config_modification(self):
        """Can conditionally modify config."""

        class User(BaseModel):
            model_config = {"extra": "allow"}
            id: int

        ctx = self.get_context(User)
        # Only add frozen if extra is allow
        config_op = ModelDict(lambda config: {**config, "frozen": True} if config.get("extra") == "allow" else config)
        result = config_op(ctx)

        assert result.current_variant.model_config["frozen"] is True  # type: ignore[attr-defined]

    def test_error_on_built_model(self):
        """Raises error when applied to built model."""

        class User(BaseModel):
            id: int

        ctx = VariantContext("Test")
        ctx.original_model = User
        ctx.current_variant = User  # Built model

        config_op = ModelDict(lambda config: {"frozen": True})

        with pytest.raises(ValueError, match="requires DecomposedModel"):
            config_op(ctx)

    def test_returns_context(self):
        """Returns context for pipeline chaining."""

        class User(BaseModel):
            id: int

        ctx = self.get_context(User)
        config_op = ModelDict(lambda config: config)
        result = config_op(ctx)

        assert result is ctx

    def test_config_applied_to_built_model(self):
        """Config is actually applied when model is built."""

        class User(BaseModel):
            id: int
            name: str

        ctx = self.get_context(User)
        ModelDict(lambda config: {**config, "frozen": True})(ctx)
        BuildVariant()(ctx)

        # Built model should have frozen config
        BuiltModel = ctx.current_variant  # type: ignore[attr-defined]

        instance = BuiltModel(id=1, name="John")  # type: ignore[attr-defined]
        with pytest.raises(Exception):  # ValidationError for frozen model
            instance.name = "Jane"  # type: ignore[attr-defined]
