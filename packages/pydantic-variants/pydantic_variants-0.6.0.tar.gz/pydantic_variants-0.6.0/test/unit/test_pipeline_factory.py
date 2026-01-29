"""Tests for create_variant_pipeline and rebuild_with_variants functions."""

import pytest
from pydantic import BaseModel
from typing import Annotated

from pydantic_variants import create_variant_pipeline, rebuild_with_variants, variants
from pydantic_variants.transformers import Tag, ModifyFields


class TestCreateVariantPipeline:
    """Tests for the pipeline factory function."""

    def test_basic_pipeline(self):
        """Test creating a basic pipeline with just a name."""
        pipe = create_variant_pipeline("Input")

        @variants(pipe)
        class User(BaseModel):
            id: int
            name: str

        assert hasattr(User, "Input")  # type: ignore[attr-defined]
        assert "id" in User.Input.model_fields  # type: ignore[attr-defined]
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_exclude_fields(self):
        """Test excluding specific fields."""
        pipe = create_variant_pipeline("Input", exclude_fields=["id", "created_at"])

        @variants(pipe)
        class User(BaseModel):
            id: int
            name: str
            created_at: str

        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "created_at" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_exclude_tags(self):
        """Test excluding fields by tag."""
        exclude_input = Tag("exclude_from_input")
        pipe = create_variant_pipeline("Input", exclude_tags=["exclude_from_input"])

        @variants(pipe)
        class User(BaseModel):
            id: Annotated[int, exclude_input]
            name: str
            password: Annotated[str, exclude_input]

        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "password" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_make_optional(self):
        """Test making all fields optional."""
        pipe = create_variant_pipeline("Update", make_optional=True)

        @variants(pipe)
        class User(BaseModel):
            name: str
            email: str

        # Fields should be optional in the variant
        assert User.Update.model_fields["name"].is_required() is False  # type: ignore[attr-defined]
        assert User.Update.model_fields["email"].is_required() is False  # type: ignore[attr-defined]

    def test_make_optional_with_exclude(self):
        """Test making fields optional except specified ones."""
        pipe = create_variant_pipeline("Update", make_optional=True, optional_exclude=("name",))

        @variants(pipe)
        class User(BaseModel):
            name: str
            email: str

        # name should stay required, email should be optional
        assert User.Update.model_fields["name"].is_required() is True  # type: ignore[attr-defined]
        assert User.Update.model_fields["email"].is_required() is False  # type: ignore[attr-defined]

    def test_with_build_method(self):
        """Test attaching a build method."""

        def build_output(self):
            return {"output": True, "name": self.name}

        pipe = create_variant_pipeline("Output", build_method=("build_output", build_output))

        @variants(pipe)
        class User(BaseModel):
            name: str

        assert hasattr(User, "build_output")  # type: ignore[attr-defined]
        user = User(name="John")
        result = user.build_output()  # type: ignore[attr-defined]
        assert result == {"output": True, "name": "John"}

    def test_extra_transformers(self):
        """Test adding extra transformers."""

        def add_prefix(name, field):
            if name == "email":
                return {"alias": "contact_email"}
            return None

        pipe = create_variant_pipeline("Output", extra_transformers=[ModifyFields(modify_func=add_prefix)])

        @variants(pipe)
        class User(BaseModel):
            name: str
            email: str

        assert User.Output.model_fields["email"].alias == "contact_email"  # type: ignore[attr-defined]

    def test_combined_options(self):
        """Test combining multiple options."""
        exclude_input = Tag("exclude")

        pipe = create_variant_pipeline(
            "Update", exclude_fields=["id"], exclude_tags=["exclude"], make_optional=True, optional_exclude=("name",)
        )

        @variants(pipe)
        class User(BaseModel):
            id: int
            name: str
            email: str
            password: Annotated[str, exclude_input]

        fields = User.Update.model_fields  # type: ignore[attr-defined]
        assert "id" not in fields  # excluded by name
        assert "password" not in fields  # excluded by tag
        assert "name" in fields
        assert "email" in fields
        assert fields["name"].is_required() is True  # excluded from optional
        assert fields["email"].is_required() is False  # made optional


class TestRebuildWithVariants:
    """Tests for rebuild_with_variants function."""

    def test_rebuild_with_delayed_variants(self):
        """Test rebuilding model with delayed variant building."""

        # Create a forward reference scenario
        class Address(BaseModel):
            street: str

        pipe = create_variant_pipeline("Input")

        @variants(pipe, delayed_build=True)
        class User(BaseModel):
            name: str
            address: "Address"

        # Variants should not exist yet
        assert not hasattr(User, "Input") or User.Input is None or isinstance(User.Input, str)  # type: ignore[attr-defined]

        # Rebuild with variants
        rebuild_with_variants(User, {"_types_namespace": {"Address": Address}})

        # Now variants should exist
        assert hasattr(User, "Input")
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_rebuild_without_namespace(self):
        """Test rebuilding without type namespace."""
        pipe = create_variant_pipeline("Input")

        @variants(pipe, delayed_build=True)
        class User(BaseModel):
            name: str
            age: int

        rebuild_with_variants(User)

        assert hasattr(User, "Input")
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_rebuild_error_without_delayed_build(self):
        """Test error when model doesn't have _build_variants."""
        pipe = create_variant_pipeline("Input")

        @variants(pipe)  # Not delayed
        class User(BaseModel):
            name: str

        # Should raise because _build_variants doesn't exist (variants already built)
        with pytest.raises(AttributeError, match="does not have _build_variants"):
            rebuild_with_variants(User)


class TestTagConvenienceMethods:
    """Tests for Tag.exclude() and Tag.include() methods."""

    def test_tag_exclude_creates_tag(self):
        """Test that Tag.exclude() creates a valid Tag."""
        tag = Tag.exclude("internal")
        assert isinstance(tag, Tag)
        assert tag.key == "internal"

    def test_tag_include_creates_tag(self):
        """Test that Tag.include() creates a valid Tag."""
        tag = Tag.include("public")
        assert isinstance(tag, Tag)
        assert tag.key == "public"

    def test_tag_exclude_equals_regular_tag(self):
        """Test that Tag.exclude() is equivalent to Tag()."""
        tag1 = Tag.exclude("test")
        tag2 = Tag("test")
        assert tag1 == tag2
        assert hash(tag1) == hash(tag2)

    def test_tag_include_equals_regular_tag(self):
        """Test that Tag.include() is equivalent to Tag()."""
        tag1 = Tag.include("test")
        tag2 = Tag("test")
        assert tag1 == tag2

    def test_tag_in_filter_tag(self):
        """Test using Tag instance directly in FilterTag."""

        exclude_input = Tag.exclude("exclude_from_input")

        @variants(create_variant_pipeline("Input", exclude_tags=[exclude_input.key]))
        class User(BaseModel):
            name: str
            password: Annotated[str, exclude_input]

        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]
        assert "password" not in User.Input.model_fields  # type: ignore[attr-defined]
