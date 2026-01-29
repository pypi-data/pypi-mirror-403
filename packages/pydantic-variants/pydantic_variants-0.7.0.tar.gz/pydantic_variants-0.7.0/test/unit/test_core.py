"""
Tests for core module: VariantPipe, VariantContext, DecomposedModel
"""

import logging
from pydantic import BaseModel

from pydantic_variants.core import VariantPipe, VariantContext, DecomposedModel


class TestVariantPipe:
    """Tests for VariantPipe class."""

    def test_empty_pipe_returns_input(self):
        """Empty pipeline returns input unchanged."""
        pipe = VariantPipe()
        assert pipe("test") == "test"

    def test_single_operation(self):
        """Single operation is executed."""
        pipe = VariantPipe(lambda x: x * 2)
        assert pipe(5) == 10

    def test_multiple_operations_execute_in_order(self):
        """Operations execute in the correct order."""
        pipe = VariantPipe(
            lambda x: x + 1,  # 5 -> 6
            lambda x: x * 2,  # 6 -> 12
            lambda x: x - 3,  # 12 -> 9
        )
        assert pipe(5) == 9

    def test_immutability_append(self):
        """append() returns a new instance, original unchanged."""
        pipe1 = VariantPipe(lambda x: x + 1)
        pipe2 = pipe1.append(lambda x: x * 2)

        assert len(pipe1) == 1
        assert len(pipe2) == 2
        assert pipe1(5) == 6
        assert pipe2(5) == 12

    def test_immutability_insert(self):
        """insert() returns a new instance, original unchanged."""
        pipe1 = VariantPipe(lambda x: x + 1, lambda x: x * 2)
        pipe2 = pipe1.insert(1, lambda x: x + 10)  # Insert between

        assert len(pipe1) == 2
        assert len(pipe2) == 3
        assert pipe1(5) == 12  # (5+1)*2 = 12
        assert pipe2(5) == 32  # (5+1+10)*2 = 32

    def test_immutability_replace(self):
        """replace() returns a new instance, original unchanged."""
        pipe1 = VariantPipe(lambda x: x + 1, lambda x: x * 2)
        pipe2 = pipe1.replace(0, lambda x: x + 100)

        assert pipe1(5) == 12  # (5+1)*2 = 12
        assert pipe2(5) == 210  # (5+100)*2 = 210

    def test_indexing_single(self):
        """Single index returns the operation."""

        def op1(x):
            return x + 1

        def op2(x):
            return x * 2

        pipe = VariantPipe(op1, op2)

        assert pipe[0] is op1
        assert pipe[1] is op2
        assert pipe[-1] is op2

    def test_slicing_returns_new_pipe(self):
        """Slicing returns a new VariantPipe."""
        pipe = VariantPipe(
            lambda x: x + 1,
            lambda x: x * 2,
            lambda x: x - 3,
        )
        sliced = pipe[1:]

        assert isinstance(sliced, VariantPipe)
        assert len(sliced) == 2
        assert sliced(5) == 7  # (5*2)-3 = 7

    def test_len(self):
        """len() returns number of operations."""
        assert len(VariantPipe()) == 0
        assert len(VariantPipe(lambda x: x)) == 1
        assert len(VariantPipe(lambda x: x, lambda x: x)) == 2

    def test_iteration(self):
        """Can iterate over operations."""
        ops = [lambda x: x + 1, lambda x: x * 2]
        pipe = VariantPipe(*ops)

        result = list(pipe)
        assert len(result) == 2
        assert result[0] is ops[0]
        assert result[1] is ops[1]

    def test_repr(self):
        """repr shows operation names."""

        def my_op(x):
            return x

        pipe = VariantPipe(my_op)
        assert "my_op" in repr(pipe)

    def test_with_debug_returns_new_pipe(self):
        """with_debug() returns a new pipeline with debug settings."""
        pipe1 = VariantPipe(lambda x: x)
        logger = logging.getLogger("test")
        pipe2 = pipe1.with_debug(logger, debug=True)

        assert pipe2._debug is True
        assert pipe2._logger is logger
        assert pipe1._debug is False

    def test_debug_logging(self, caplog):
        """Debug mode logs pipeline execution."""
        logger = logging.getLogger("test_debug")
        logger.setLevel(logging.DEBUG)

        pipe = VariantPipe(lambda x: x + 1, logger=logger, debug=True)

        with caplog.at_level(logging.DEBUG, logger="test_debug"):
            pipe(5)

        assert "Starting pipeline" in caplog.text
        assert "Executing" in caplog.text


class TestDecomposedModel:
    """Tests for DecomposedModel class."""

    def test_captures_model_fields(self):
        """DecomposedModel captures model fields."""

        class User(BaseModel):
            id: int
            name: str

        decomposed = DecomposedModel(User)

        assert "id" in decomposed.model_fields
        assert "name" in decomposed.model_fields
        assert len(decomposed.model_fields) == 2

    def test_fields_are_copied(self):
        """Fields dict is a copy, not a reference."""

        class User(BaseModel):
            id: int
            name: str

        decomposed = DecomposedModel(User)
        decomposed.model_fields.pop("id")

        # Original model should be unchanged
        assert "id" in User.model_fields

    def test_captures_model_config(self):
        """DecomposedModel captures model config."""

        class User(BaseModel):
            model_config = {"frozen": True, "extra": "forbid"}
            id: int

        decomposed = DecomposedModel(User)

        assert decomposed.model_config.get("frozen") is True
        assert decomposed.model_config.get("extra") == "forbid"

    def test_captures_docstring(self):
        """DecomposedModel captures model docstring."""

        class User(BaseModel):
            """User model documentation."""

            id: int

        decomposed = DecomposedModel(User)
        assert decomposed.model_doc == "User model documentation."

    def test_build_creates_new_model(self):
        """build() creates a new Pydantic model."""

        class User(BaseModel):
            id: int
            name: str

        decomposed = DecomposedModel(User)
        BuiltModel = decomposed.build("Input")

        assert BuiltModel.__name__ == "UserInput"
        assert issubclass(BuiltModel, BaseModel)
        assert "id" in BuiltModel.model_fields
        assert "name" in BuiltModel.model_fields

    def test_build_with_custom_base(self):
        """build() can use a custom base class."""

        class CustomBase(BaseModel):
            custom_field: str = "custom"

        class User(BaseModel):
            id: int

        decomposed = DecomposedModel(User)
        BuiltModel = decomposed.build("Input", base=CustomBase)

        assert issubclass(BuiltModel, CustomBase)
        assert "custom_field" in BuiltModel.model_fields
        assert "id" in BuiltModel.model_fields

    def test_build_preserves_module(self):
        """Built model has same __module__ as original."""

        class User(BaseModel):
            id: int

        decomposed = DecomposedModel(User)
        BuiltModel = decomposed.build("Input")

        assert BuiltModel.__module__ == User.__module__

    def test_build_preserves_docstring(self):
        """Built model has same docstring as original."""

        class User(BaseModel):
            """User documentation."""

            id: int

        decomposed = DecomposedModel(User)
        BuiltModel = decomposed.build("Input")

        assert BuiltModel.__doc__ == "User documentation."


class TestVariantContext:
    """Tests for VariantContext class."""

    def test_initialization_with_name(self):
        """Context initialized with name."""
        ctx = VariantContext("Input")
        assert ctx.name == "Input"
        assert ctx.metadata == {}

    def test_callable_with_model(self):
        """Context is callable with a model class."""

        class User(BaseModel):
            id: int
            name: str

        ctx = VariantContext("Input")
        result = ctx(User)

        assert result is ctx  # Returns self
        assert ctx.original_model is User
        assert isinstance(ctx.current_variant, DecomposedModel)

    def test_current_variant_has_fields(self):
        """After calling with model, current_variant has fields."""

        class User(BaseModel):
            id: int
            name: str

        ctx = VariantContext("Input")
        ctx(User)

        assert "id" in ctx.current_variant.model_fields
        assert "name" in ctx.current_variant.model_fields

    def test_metadata_can_be_modified(self):
        """Metadata dict can store arbitrary data."""
        ctx = VariantContext("Input")
        ctx.metadata["custom_key"] = "custom_value"

        assert ctx.metadata["custom_key"] == "custom_value"
