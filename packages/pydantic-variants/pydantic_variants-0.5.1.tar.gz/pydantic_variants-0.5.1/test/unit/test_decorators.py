"""
Tests for decorators module: @variants, basic_variant_pipeline
"""

import logging
from pydantic import BaseModel

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, MakeOptional


class TestBasicVariantPipeline:
    """Tests for basic_variant_pipeline helper function."""

    def test_creates_variant_with_name(self):
        """Creates a variant attached to model with given name."""
        pipeline = basic_variant_pipeline("Input")

        @variants(pipeline)
        class User(BaseModel):
            id: int
            name: str

        assert hasattr(User, "Input")
        assert User.Input.__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_applies_transformers(self):
        """Transformers are applied in order."""
        pipeline = basic_variant_pipeline("Input", FilterFields(exclude=["id"]), MakeOptional(all=True))

        @variants(pipeline)
        class User(BaseModel):
            id: int
            name: str
            email: str

        # id should be filtered out
        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        # name and email should be optional with None default
        assert User.Input.model_fields["name"].default is None  # type: ignore[attr-defined]
        assert User.Input.model_fields["email"].default is None  # type: ignore[attr-defined]

    def test_variant_stored_in_variants_dict(self):
        """Variant is also stored in _variants dict."""
        pipeline = basic_variant_pipeline("Input")

        @variants(pipeline)
        class User(BaseModel):
            id: int

        assert hasattr(User, "_variants")  # type: ignore[attr-defined]
        assert "Input" in User._variants  # type: ignore[attr-defined]
        assert User._variants["Input"] is User.Input  # type: ignore[attr-defined]

    def test_with_debug_logging(self, caplog):
        """Debug logging works when enabled."""
        logger = logging.getLogger("test_pipeline")
        logger.setLevel(logging.DEBUG)

        pipeline = basic_variant_pipeline("Input", FilterFields(exclude=["id"]), logger=logger, debug=True)

        with caplog.at_level(logging.DEBUG, logger="test_pipeline"):

            @variants(pipeline)
            class User(BaseModel):
                id: int
                name: str

        assert "Starting pipeline" in caplog.text


class TestVariantsDecorator:
    """Tests for @variants decorator."""

    def test_single_pipeline(self):
        """Single pipeline creates one variant."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            id: int
            name: str

        assert hasattr(User, "Input")

    def test_multiple_pipelines(self):
        """Multiple pipelines create multiple variants."""
        input_pipe = basic_variant_pipeline("Input", FilterFields(exclude=["id"]))
        output_pipe = basic_variant_pipeline("Output", FilterFields(exclude=["password"]))

        @variants(input_pipe, output_pipe)
        class User(BaseModel):
            id: int
            name: str
            password: str

        assert hasattr(User, "Input")  # type: ignore[attr-defined]
        assert hasattr(User, "Output")  # type: ignore[attr-defined]
        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "password" not in User.Output.model_fields  # type: ignore[attr-defined]

    def test_returns_original_class(self):
        """Decorator returns the original class."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            id: int
            name: str

        assert User.__name__ == "User"
        assert "id" in User.model_fields
        assert "name" in User.model_fields

    def test_delayed_build_true(self):
        """delayed_build=True attaches _build_variants method."""

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class User(BaseModel):
            id: int
            name: str

        # Variant should not exist yet
        assert not hasattr(User, "Input") or User.Input is None  # type: ignore[attr-defined]
        assert hasattr(User, "_build_variants")  # type: ignore[attr-defined]

        # Build variants
        User._build_variants()  # type: ignore[attr-defined]

        # Now variant should exist
        assert hasattr(User, "Input")
        assert User.Input.__name__ == "UserInput"  # type: ignore[attr-defined]

    def test_delayed_build_with_forward_refs(self):
        """delayed_build allows building after model_rebuild."""

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class Post(BaseModel):
            id: int
            title: str

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class User(BaseModel):
            id: int
            posts: list["Post"] = []

        # Rebuild to resolve forward refs
        User.model_rebuild()
        Post.model_rebuild()

        # Now build variants
        Post._build_variants()  # type: ignore[attr-defined]
        User._build_variants()  # type: ignore[attr-defined]

        assert hasattr(User, "Input")
        assert hasattr(Post, "Input")

    def test_debug_at_decorator_level(self, caplog):
        """Debug can be enabled at decorator level."""
        logger = logging.getLogger("test_decorator")
        logger.setLevel(logging.DEBUG)

        with caplog.at_level(logging.DEBUG, logger="test_decorator"):

            @variants(basic_variant_pipeline("Input"), logger=logger, debug=True)
            class User(BaseModel):
                id: int

        # Should have debug output
        assert len(caplog.records) > 0

    def test_variant_has_root_model_reference(self):
        """Variant has _root_model pointing to original."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            id: int

        assert hasattr(User.Input, "_root_model")  # type: ignore[attr-defined]
        assert User.Input._root_model is User  # type: ignore[attr-defined]

    def test_variant_is_valid_pydantic_model(self):
        """Generated variant is a valid, functional Pydantic model."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class User(BaseModel):
            id: int
            name: str
            email: str

        # Should be able to instantiate and validate
        user = User.Input(name="John", email="john@example.com")  # type: ignore[attr-defined]
        assert user.name == "John"
        assert user.email == "john@example.com"

        # Should produce valid dict
        data = user.model_dump()
        assert data == {"name": "John", "email": "john@example.com"}
