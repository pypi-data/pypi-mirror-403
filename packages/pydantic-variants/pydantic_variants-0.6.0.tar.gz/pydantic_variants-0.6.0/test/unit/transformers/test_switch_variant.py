"""
Tests for SwitchVariant transformer.
"""

from typing import List, Optional, Union, Dict
from pydantic import BaseModel

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, SwitchVariant


class TestSwitchVariant:
    """Tests for SwitchVariant transformer."""

    def test_switch_simple_nested_model(self):
        """Switches a simple nested model to its variant."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class Address(BaseModel):
            id: int
            street: str
            city: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            name: str
            address: Address

        # User.Input.address should use Address.Input
        address_annotation = User.Input.model_fields["address"].annotation  # type: ignore[attr-defined]
        assert address_annotation is Address.Input  # type: ignore[attr-defined]

    def test_switch_list_of_models(self):
        """Switches List[Model] to List[Model.Variant]."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class Tag(BaseModel):
            id: int
            name: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Post(BaseModel):
            title: str
            tags: List[Tag]

        # Post.Input.tags should be List[Tag.Input]
        tags_annotation = Post.Input.model_fields["tags"].annotation  # type: ignore[attr-defined]
        assert tags_annotation.__origin__ is list
        assert tags_annotation.__args__[0] is Tag.Input  # type: ignore[attr-defined]

    def test_switch_optional_model(self):
        """Switches Optional[Model] correctly."""

        @variants(basic_variant_pipeline("Input"))
        class Profile(BaseModel):
            bio: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            name: str
            profile: Optional[Profile] = None

        # Should be Optional[Profile.Input]
        profile_annotation = User.Input.model_fields["profile"].annotation  # type: ignore[attr-defined]
        # Check that Profile.Input is in the union args
        args = getattr(profile_annotation, "__args__", ())
        assert Profile.Input in args  # type: ignore[attr-defined]

    def test_switch_union_with_model(self):
        """Switches Union types containing models."""

        @variants(basic_variant_pipeline("Input"))
        class Cat(BaseModel):
            meows: bool

        @variants(basic_variant_pipeline("Input"))
        class Dog(BaseModel):
            barks: bool

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Pet(BaseModel):
            animal: Union[Cat, Dog]

        # Should be Union[Cat.Input, Dog.Input]
        animal_annotation = Pet.Input.model_fields["animal"].annotation  # type: ignore[attr-defined]
        args = getattr(animal_annotation, "__args__", ())
        assert Cat.Input in args  # type: ignore[attr-defined]
        assert Dog.Input in args  # type: ignore[attr-defined]

    def test_switch_nested_list(self):
        """Switches nested generic types like List[List[Model]]."""

        @variants(basic_variant_pipeline("Input"))
        class Item(BaseModel):
            value: int

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Container(BaseModel):
            matrix: List[List[Item]]

        matrix_annotation = Container.Input.model_fields["matrix"].annotation  # type: ignore[attr-defined]
        # Should be List[List[Item.Input]]
        inner_list = matrix_annotation.__args__[0]
        assert inner_list.__args__[0] is Item.Input  # type: ignore[attr-defined]

    def test_switch_nonexistent_variant(self):
        """Models without the variant remain unchanged."""

        class NoVariants(BaseModel):
            value: int

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            data: NoVariants

        # Should remain as NoVariants (no Input variant exists)
        data_annotation = User.Input.model_fields["data"].annotation  # type: ignore[attr-defined]
        assert data_annotation is NoVariants

    def test_switch_exclude_fields(self):
        """Excluded fields are not switched."""

        @variants(basic_variant_pipeline("Input"))
        class Metadata(BaseModel):
            info: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input", exclude=["meta"])))
        class User(BaseModel):
            data: Metadata
            meta: Metadata

        # data should be switched, meta should not
        assert User.Input.model_fields["data"].annotation is Metadata.Input  # type: ignore[attr-defined]
        assert User.Input.model_fields["meta"].annotation is Metadata  # type: ignore[attr-defined]

    def test_switch_uses_context_name_if_none(self):
        """Uses context.name when variant_name is None."""

        @variants(basic_variant_pipeline("Output"))
        class Address(BaseModel):
            street: str

        # SwitchVariant() with no args uses the pipeline's context name
        @variants(basic_variant_pipeline("Output", SwitchVariant()))
        class User(BaseModel):
            address: Address

        # Should use Output variant (context name)
        assert User.Output.model_fields["address"].annotation is Address.Output  # type: ignore[attr-defined]

    def test_switch_dict_values(self):
        """Switches Dict values containing models."""

        @variants(basic_variant_pipeline("Input"))
        class Config(BaseModel):
            value: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Settings(BaseModel):
            configs: Dict[str, Config]

        configs_annotation = Settings.Input.model_fields["configs"].annotation  # type: ignore[attr-defined]
        # Should be Dict[str, Config.Input]
        assert configs_annotation.__args__[1] is Config.Input  # type: ignore[attr-defined]

    def test_switch_pipe_union_syntax(self):
        """Handles X | Y union syntax (types.UnionType)."""

        @variants(basic_variant_pipeline("Input"))
        class Option(BaseModel):
            value: int

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Container(BaseModel):
            data: Option | None

        data_annotation = Container.Input.model_fields["data"].annotation  # type: ignore[attr-defined]
        # Should include Option.Input
        args = getattr(data_annotation, "__args__", ())
        assert Option.Input in args  # type: ignore[attr-defined]

    def test_non_model_types_unchanged(self):
        """Non-BaseModel types are not affected."""

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            name: str
            age: int
            tags: List[str]

        assert User.Input.model_fields["name"].annotation is str  # type: ignore[attr-defined]
        assert User.Input.model_fields["age"].annotation is int  # type: ignore[attr-defined]
        # Check that the tags field still has a list of strings
        tags_annotation = User.Input.model_fields["tags"].annotation  # type: ignore[attr-defined]
        origin = getattr(tags_annotation, "__origin__", None)
        assert origin is list
        assert tags_annotation.__args__ == (str,)
