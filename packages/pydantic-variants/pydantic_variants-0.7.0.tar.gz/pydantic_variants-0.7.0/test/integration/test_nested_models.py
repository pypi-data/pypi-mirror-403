"""
Integration tests for nested models and SwitchVariant.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, SwitchVariant


class TestNestedModels:
    """Tests for nested model variant switching."""

    def test_simple_nested_variant_switch(self):
        """Simple nested model gets switched to variant."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class Address(BaseModel):
            id: int
            street: str
            city: str

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"]), SwitchVariant("Input")))
        class User(BaseModel):
            id: int
            name: str
            address: Address

        # User.Input.address should be Address.Input
        assert User.Input.model_fields["address"].annotation is Address.Input  # type: ignore[attr-defined]

        # Should be functional
        user = User.Input(name="John", address={"street": "Main St", "city": "NYC"})  # type: ignore[attr-defined]
        assert user.name == "John"
        assert user.address.street == "Main St"

    def test_three_level_nesting(self):
        """Handles three levels of nesting."""

        @variants(basic_variant_pipeline("Input"))
        class Country(BaseModel):
            name: str
            code: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Address(BaseModel):
            street: str
            country: Country

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            name: str
            address: Address

        # Check all levels switched
        assert User.Input.model_fields["address"].annotation is Address.Input  # type: ignore[attr-defined]
        assert Address.Input.model_fields["country"].annotation is Country.Input  # type: ignore[attr-defined]

        # Should be functional
        user = User.Input(name="John", address={"street": "Main St", "country": {"name": "USA", "code": "US"}})  # type: ignore[attr-defined]
        assert user.address.country.name == "USA"

    def test_list_of_nested_models(self):
        """List[Model] gets switched to List[Model.Variant]."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class Tag(BaseModel):
            id: int
            name: str

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"]), SwitchVariant("Input")))
        class Post(BaseModel):
            id: int
            title: str
            tags: List[Tag]

        # Post.Input.tags should be List[Tag.Input]
        tags_type = Post.Input.model_fields["tags"].annotation  # type: ignore[attr-defined]
        assert tags_type.__origin__ is list
        assert tags_type.__args__[0] is Tag.Input  # type: ignore[attr-defined]

        # Should be functional
        post = Post.Input(title="Hello", tags=[{"name": "python"}, {"name": "coding"}])  # type: ignore[attr-defined]
        assert len(post.tags) == 2
        assert post.tags[0].name == "python"

    def test_optional_nested_model(self):
        """Optional[Model] gets switched correctly."""

        @variants(basic_variant_pipeline("Input"))
        class Profile(BaseModel):
            bio: str
            website: Optional[str] = None

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            name: str
            profile: Optional[Profile] = None

        # Should use Profile.Input
        profile_type = User.Input.model_fields["profile"].annotation  # type: ignore[attr-defined]
        args = getattr(profile_type, "__args__", ())
        assert Profile.Input in args  # type: ignore[attr-defined]

        # Should work with and without profile
        user1 = User.Input(name="John")  # type: ignore[attr-defined]
        assert user1.profile is None

        user2 = User.Input(name="Jane", profile={"bio": "Developer"})  # type: ignore[attr-defined]
        assert user2.profile.bio == "Developer"

    def test_dict_with_model_values(self):
        """Dict[str, Model] gets switched."""

        @variants(basic_variant_pipeline("Input"))
        class Setting(BaseModel):
            value: str
            enabled: bool = True

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class Config(BaseModel):
            settings: Dict[str, Setting]

        settings_type = Config.Input.model_fields["settings"].annotation  # type: ignore[attr-defined]
        assert settings_type.__args__[1] is Setting.Input  # type: ignore[attr-defined]

        # Functional test
        config = Config.Input(settings={"theme": {"value": "dark"}, "lang": {"value": "en", "enabled": False}})  # type: ignore[attr-defined]
        assert config.settings["theme"].value == "dark"
        assert config.settings["lang"].enabled is False

    def test_self_reference(self):
        """Handles self-referential models."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"]), SwitchVariant("Input")), delayed_build=True)
        class Employee(BaseModel):
            id: int
            name: str
            manager: Optional["Employee"] = None

        Employee.model_rebuild()
        Employee._build_variants()  # type: ignore[attr-defined]

        # Variant should exist and work
        assert hasattr(Employee, "Input")

        # For self-referential types with forward refs, use dicts
        emp = Employee.Input(name="John", manager={"id": 1, "name": "Jane", "manager": None})  # type: ignore[attr-defined]
        assert emp.manager.name == "Jane"

    def test_variant_consistency_across_hierarchy(self):
        """All nested variants use same variant name."""

        @variants(basic_variant_pipeline("API"))
        class Item(BaseModel):
            name: str

        @variants(basic_variant_pipeline("API", SwitchVariant("API")))
        class Category(BaseModel):
            name: str
            items: List[Item]

        @variants(basic_variant_pipeline("API", SwitchVariant("API")))
        class Store(BaseModel):
            name: str
            categories: List[Category]

        # All should use API variant
        assert Store.API.model_fields["categories"].annotation.__args__[0] is Category.API  # type: ignore[attr-defined]
        assert Category.API.model_fields["items"].annotation.__args__[0] is Item.API  # type: ignore[attr-defined]

    def test_mixed_switched_and_unswitched(self):
        """Some nested models switched, others not."""

        @variants(basic_variant_pipeline("Input"))
        class Address(BaseModel):
            street: str

        class NoVariants(BaseModel):
            value: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")))
        class User(BaseModel):
            address: Address
            meta: NoVariants

        # Address should be switched, NoVariants should not
        assert User.Input.model_fields["address"].annotation is Address.Input  # type: ignore[attr-defined]
        assert User.Input.model_fields["meta"].annotation is NoVariants  # type: ignore[attr-defined]

    def test_exclude_specific_nested_fields(self):
        """SwitchVariant can exclude specific fields."""

        @variants(basic_variant_pipeline("Input"))
        class Metadata(BaseModel):
            info: str

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input", exclude=["audit_meta"])))
        class Record(BaseModel):
            data_meta: Metadata
            audit_meta: Metadata

        # data_meta switched, audit_meta not
        assert Record.Input.model_fields["data_meta"].annotation is Metadata.Input  # type: ignore[attr-defined]
        assert Record.Input.model_fields["audit_meta"].annotation is Metadata  # type: ignore[attr-defined]
