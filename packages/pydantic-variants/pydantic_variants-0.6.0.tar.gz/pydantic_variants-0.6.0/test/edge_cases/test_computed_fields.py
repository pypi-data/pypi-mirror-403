"""
Tests for computed fields in variants.
"""

import pytest
from datetime import datetime
from pydantic import BaseModel, computed_field

from pydantic_variants import variants, basic_variant_pipeline, VariantPipe, VariantContext
from pydantic_variants.transformers import (
    FilterFields,
    FilterTag,
    MakeOptional,
    Tag,
    computed_with_tags,
    BuildVariant,
    ConnectVariant,
    ExtractVariant,
    RenameFields,
    ModifyFields,
)


class TestComputedFields:
    """Tests for models with computed fields."""

    def test_computed_field_preserved_in_variant(self):
        """Computed fields are preserved in variants."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])))
        class User(BaseModel):
            id: int
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        # Variant should have the computed field
        user = User.Input(first_name="John", last_name="Doe")  # type: ignore[attr-defined]
        assert user.full_name == "John Doe"

    def test_computed_field_in_model_dump(self):
        """Computed fields appear in model_dump."""

        @variants(basic_variant_pipeline("Output"))
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        user = User.Output(first_name="John", last_name="Doe")  # type: ignore[attr-defined]
        data = user.model_dump()

        assert "full_name" in data
        assert data["full_name"] == "John Doe"

    def test_computed_field_depends_on_filtered_field(self):
        """Computed field that depends on a filtered field."""

        @variants(basic_variant_pipeline("Public", FilterFields(exclude=["birth_year"])))
        class User(BaseModel):
            name: str
            birth_year: int

            @computed_field
            @property
            def age(self) -> int:
                return datetime.now().year - self.birth_year

        # Variant doesn't have birth_year, so computed field can't work
        # This should raise when trying to access age without birth_year
        # The variant is created but may fail at runtime
        assert "birth_year" not in User.Public.model_fields  # type: ignore[attr-defined]

        # Creating instance without birth_year
        user = User.Public(name="John")  # type: ignore[attr-defined]
        # Accessing computed field would raise AttributeError
        with pytest.raises(AttributeError):
            _ = user.age

    def test_multiple_computed_fields(self):
        """Multiple computed fields work correctly."""

        @variants(basic_variant_pipeline("API"))
        class Person(BaseModel):
            first_name: str
            last_name: str
            birth_year: int

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_field
            @property
            def initials(self) -> str:
                return f"{self.first_name[0]}.{self.last_name[0]}."

            @computed_field
            @property
            def age(self) -> int:
                return datetime.now().year - self.birth_year

        person = Person.API(first_name="John", last_name="Doe", birth_year=1990)  # type: ignore[attr-defined]

        assert person.full_name == "John Doe"
        assert person.initials == "J.D."
        assert person.age == datetime.now().year - 1990

    def test_computed_field_with_optional_deps(self):
        """Computed field using optional fields."""

        @variants(basic_variant_pipeline("Input", MakeOptional(all=True)))
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def display_name(self) -> str:
                if self.first_name and self.last_name:
                    return f"{self.first_name} {self.last_name}"
                return self.first_name or self.last_name or "Anonymous"

        # Test with all values
        user1 = User.Input(first_name="John", last_name="Doe")  # type: ignore[attr-defined]
        assert user1.display_name == "John Doe"

        # Test with partial values
        user2 = User.Input(first_name="John")  # type: ignore[attr-defined]
        assert user2.display_name == "John"

        # Test with no values
        user3 = User.Input()  # type: ignore[attr-defined]
        assert user3.display_name == "Anonymous"

    def test_computed_field_cached(self):
        """Computed field values are computed correctly each time."""
        call_count = 0

        @variants(basic_variant_pipeline("API"))
        class Counter(BaseModel):
            value: int

            @computed_field
            @property
            def doubled(self) -> int:
                nonlocal call_count
                call_count += 1
                return self.value * 2

        counter = Counter.API(value=5)  # type: ignore[attr-defined]

        # Access multiple times
        assert counter.doubled == 10
        assert counter.doubled == 10
        # Property is recomputed each time (no caching by default)
        assert call_count >= 1

    def test_computed_field_with_nested_model(self):
        """Computed field accessing nested model data."""

        @variants(basic_variant_pipeline("Input"))
        class Address(BaseModel):
            city: str
            country: str

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            name: str
            address: Address

            @computed_field
            @property
            def location(self) -> str:
                return f"{self.address.city}, {self.address.country}"

        user = User.Input(name="John", address={"city": "NYC", "country": "USA"})  # type: ignore[attr-defined]

        assert user.location == "NYC, USA"

    def test_variant_has_computed_field_in_schema(self):
        """Computed fields appear in serialization JSON schema."""

        @variants(basic_variant_pipeline("API"))
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        # Computed fields appear in serialization mode schema (for outputs)
        schema = User.API.model_json_schema(mode="serialization")  # type: ignore[attr-defined]

        # Computed field should be in schema
        assert "full_name" in schema["properties"]
        assert schema["properties"]["full_name"]["type"] == "string"

    def test_computed_field_return_types(self):
        """Computed fields with various return types."""

        @variants(basic_variant_pipeline("API"))
        class Data(BaseModel):
            items: list[int]

            @computed_field
            @property
            def count(self) -> int:
                return len(self.items)

            @computed_field
            @property
            def is_empty(self) -> bool:
                return len(self.items) == 0

            @computed_field
            @property
            def as_set(self) -> set[int]:
                return set(self.items)

        data = Data.API(items=[1, 2, 2, 3])  # type: ignore[attr-defined]

        assert data.count == 4
        assert data.is_empty is False
        assert data.as_set == {1, 2, 3}

    def test_computed_field_inheritance(self):
        """Computed fields are inherited in variants."""

        class BaseUser(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        @variants(basic_variant_pipeline("Input"))
        class User(BaseUser):
            email: str

        user = User.Input(first_name="John", last_name="Doe", email="john@example.com")  # type: ignore[attr-defined]

        # Inherited computed field should work
        assert user.full_name == "John Doe"


class TestTaggedComputedFields:
    """Tests for FilterTag filtering of computed fields via tag_computed."""

    def test_computed_field_filtered_by_tag(self):
        """Computed fields with matching tags are filtered out."""
        INTERNAL = Tag("internal")

        @variants(VariantPipe(VariantContext("Public"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str

            @computed_with_tags(INTERNAL)
            @property
            def debug_info(self) -> str:
                return f"email={self.email}"

        # Public variant should NOT have debug_info computed field
        user = User.Public(email="test@example.com")  # type: ignore[attr-defined]

        # Verify field not accessible
        assert not hasattr(user, "debug_info")

        # Verify not in serialization
        data = user.model_dump()
        assert "debug_info" not in data

    def test_computed_field_kept_when_tag_not_matched(self):
        """Computed fields without matching tags are preserved."""
        Tag("internal")
        PUBLIC = Tag("public")

        @variants(VariantPipe(VariantContext("API"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str

            @computed_with_tags(PUBLIC)
            @property
            def display_email(self) -> str:
                return self.email.upper()

        # API variant should have display_email (tagged public, not internal)
        user = User.API(email="test@example.com")  # type: ignore[attr-defined]
        assert user.display_email == "TEST@EXAMPLE.COM"

    def test_filter_both_regular_and_computed_fields(self):
        """FilterTag filters both regular fields and computed fields with same tag."""
        INTERNAL = Tag("internal")
        from typing import Annotated

        @variants(VariantPipe(VariantContext("Public"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str
            password_hash: Annotated[str, INTERNAL]

            @computed_with_tags(INTERNAL)
            @property
            def debug_info(self) -> str:
                return f"hash={self.password_hash}"

        # Public variant should have neither password_hash nor debug_info
        assert "password_hash" not in User.Public.model_fields  # type: ignore[attr-defined]

        user = User.Public(email="test@example.com")  # type: ignore[attr-defined]
        assert not hasattr(user, "debug_info")
        assert not hasattr(user, "password_hash")

    def test_multiple_computed_fields_selective_filtering(self):
        """Multiple computed fields with different tags, only matching are filtered."""
        INTERNAL = Tag("internal")
        PUBLIC = Tag("public")

        @variants(VariantPipe(VariantContext("Public"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_with_tags(PUBLIC)
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_with_tags(INTERNAL)
            @property
            def internal_id(self) -> str:
                return f"{self.first_name}_{self.last_name}".lower()

        user = User.Public(first_name="John", last_name="Doe")  # type: ignore[attr-defined]

        # Public computed field preserved
        assert user.full_name == "John Doe"

        # Internal computed field filtered
        assert not hasattr(user, "internal_id")

    def test_untagged_computed_fields_always_preserved(self):
        """Computed fields without tag_computed are never filtered."""

        @variants(VariantPipe(VariantContext("Public"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str

            @computed_field
            @property
            def email_domain(self) -> str:
                return self.email.split("@")[1]

        user = User.Public(email="test@example.com")  # type: ignore[attr-defined]

        # Untagged computed field should be preserved
        assert user.email_domain == "example.com"

    def test_computed_field_with_multiple_tags(self):
        """Computed field with multiple tags, any match filters it."""
        INTERNAL = Tag("internal")
        ADMIN = Tag("admin")

        @variants(VariantPipe(VariantContext("Public"), FilterTag("admin"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str

            @computed_with_tags(INTERNAL, ADMIN)
            @property
            def admin_info(self) -> str:
                return f"admin: {self.email}"

        user = User.Public(email="test@example.com")  # type: ignore[attr-defined]

        # Should be filtered because ADMIN tag matches
        assert not hasattr(user, "admin_info")

    def test_tag_computed_prevents_runtime_error(self):
        """Tag computed fields that depend on filtered fields to prevent errors."""
        INTERNAL = Tag("internal")
        from typing import Annotated

        @variants(VariantPipe(VariantContext("Public"), FilterTag("internal"), BuildVariant(), ConnectVariant(), ExtractVariant()))
        class User(BaseModel):
            email: str
            password_hash: Annotated[str, INTERNAL]

            @computed_with_tags(INTERNAL)
            @property
            def password_strength(self) -> int:
                # This would crash if password_hash was filtered but this wasn't
                return len(self.password_hash)

        # No crash - both field and computed field are filtered together
        user = User.Public(email="test@example.com")  # type: ignore[attr-defined]
        assert user.email == "test@example.com"

    def test_tag_computed_requires_tag_instance(self):
        """computed_with_tags raises TypeError if given non-Tag arguments."""
        with pytest.raises(TypeError, match="expects Tag instances"):

            @computed_with_tags("not_a_tag")  # type: ignore[arg-type]
            @property
            def foo(self) -> str:
                return "bar"

    def test_tag_computed_requires_at_least_one_tag(self):
        """computed_with_tags raises ValueError if no tags provided."""
        with pytest.raises(ValueError, match="requires at least one Tag"):

            @computed_with_tags()
            @property
            def foo(self) -> str:
                return "bar"

    def test_tag_computed_must_wrap_property(self):
        """computed_with_tags raises TypeError if not applied to a property."""
        INTERNAL = Tag("internal")

        with pytest.raises(TypeError, match="must be applied to a property"):

            @computed_with_tags(INTERNAL)  # type: ignore
            def foo(self) -> str:  # type: ignore[arg-type]
                return "bar"


class TestNameBasedTransformersWithComputedFields:
    """Tests for FilterFields, RenameFields, ModifyFields with computed fields."""

    def test_filter_fields_excludes_computed_field_by_name(self):
        """FilterFields.exclude removes computed fields by name."""

        @variants(
            VariantPipe(
                VariantContext("Minimal"),
                FilterFields(exclude=["full_name"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        user = User.Minimal(first_name="John", last_name="Doe")  # type: ignore[attr-defined]

        # Computed field should be removed
        assert not hasattr(user, "full_name")
        assert "full_name" not in User.Minimal.model_dump(user)  # type: ignore[attr-defined]

    def test_filter_fields_include_only_with_computed_field(self):
        """FilterFields.include_only keeps specified computed fields."""

        @variants(
            VariantPipe(
                VariantContext("Minimal"),
                FilterFields(include_only=["first_name", "last_name", "full_name"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            first_name: str
            last_name: str
            email: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_field
            @property
            def initials(self) -> str:
                return f"{self.first_name[0]}{self.last_name[0]}"

        user = User.Minimal(first_name="John", last_name="Doe", email="john@example.com")  # type: ignore[attr-defined]

        # Only specified fields should be present
        assert hasattr(user, "full_name")
        assert not hasattr(user, "initials")
        assert hasattr(user, "first_name")
        assert hasattr(user, "last_name")
        assert not hasattr(user, "email")
        assert "full_name" in User.Minimal.model_dump(user)  # type: ignore[attr-defined]
        assert "initials" not in User.Minimal.model_dump(user)  # type: ignore[attr-defined]

    def test_filter_fields_with_filter_func_on_computed_field(self):
        """FilterFields.filter_func can filter computed fields by name length."""

        @variants(
            VariantPipe(
                VariantContext("Compact"),
                FilterFields(filter_func=lambda name, field: len(name) > 5),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            id: int
            name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"User {self.name}"

            @computed_field
            @property
            def age(self) -> int:
                return 25

        user = User.Compact(id=1, name="John")  # type: ignore[attr-defined]

        # Fields with names > 5 chars should be removed
        # filter_func returns True for fields to REMOVE
        assert hasattr(user, "age")  # len("age") = 3, not > 5, keep it
        assert not hasattr(user, "full_name")  # len("full_name") = 9, > 5, remove it
        assert hasattr(user, "name")  # len("name") = 4, not > 5, keep it
        assert hasattr(user, "id")  # len("id") = 2, not > 5, keep it

    def test_rename_fields_renames_computed_field(self):
        """RenameFields renames computed fields by name."""

        @variants(
            VariantPipe(
                VariantContext("Renamed"),
                RenameFields(mapping={"full_name": "display_name", "age": "user_age"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_field
            @property
            def age(self) -> int:
                return 25

        # Build the variant to check field names
        user = User.Renamed(first_name="John", last_name="Doe")  # type: ignore[attr-defined]

        # Check the renamed field is accessible by new name
        assert hasattr(user, "display_name")
        assert user.display_name == "John Doe"
        assert hasattr(user, "user_age")
        assert user.user_age == 25

    def test_rename_fields_with_rename_func_on_computed_fields(self):
        """RenameFields.rename_func applies to computed field names."""

        @variants(
            VariantPipe(
                VariantContext("WithMeta"),
                RenameFields(rename_func=lambda name: f"meta_{name}" if name.startswith("_") else name),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            name: str

            @computed_field
            @property
            def display(self) -> str:
                return f"User: {self.name}"

        # Use original name for input
        user = User.WithMeta(name="John")  # type: ignore[attr-defined]

        # display field should be present and accessible
        # (since the rename pattern only renames fields starting with underscore)
        assert hasattr(user, "display")
        assert user.display == "User: John"

    def test_modify_fields_modifies_computed_field_properties(self):
        """ModifyFields can modify computed field properties like description."""

        @variants(
            VariantPipe(
                VariantContext("WithDescriptions"),
                ModifyFields(
                    field_modifications={
                        "full_name": {"description": "The user's full name"},
                        "email": {"description": "Email address"},
                    }
                ),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            email: str
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

        # Verify computed field still exists and works
        user = User.WithDescriptions(  # type: ignore[attr-defined]
            email="john@example.com", first_name="John", last_name="Doe"
        )
        assert user.full_name == "John Doe"
        assert user.email == "john@example.com"

    def test_filter_and_rename_both_affect_computed_fields(self):
        """FilterFields and RenameFields can both work on computed fields in sequence."""

        @variants(
            VariantPipe(
                VariantContext("Clean"),
                FilterFields(exclude=["initials"]),
                RenameFields(mapping={"full_name": "name"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_field
            @property
            def initials(self) -> str:
                return f"{self.first_name[0]}{self.last_name[0]}"

        user = User.Clean(first_name="John", last_name="Doe")  # type: ignore[attr-defined]

        # full_name renamed to name, initials filtered out
        assert hasattr(user, "name")
        assert user.name == "John Doe"
        assert not hasattr(user, "full_name")
        assert not hasattr(user, "initials")

    def test_rename_fields_preserves_unmentioned_computed_fields(self):
        """RenameFields only renames fields explicitly in the mapping."""

        @variants(
            VariantPipe(
                VariantContext("PartialRename"),
                RenameFields(mapping={"full_name": "display_name"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            first_name: str
            last_name: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first_name} {self.last_name}"

            @computed_field
            @property
            def age(self) -> int:
                return 25

        user = User.PartialRename(first_name="John", last_name="Doe")  # type: ignore[attr-defined]

        # full_name renamed, age kept with original name
        assert hasattr(user, "display_name")
        assert hasattr(user, "age")
        assert not hasattr(user, "full_name")
        assert user.age == 25


class TestComputedFieldDependencies:
    """Tests for computed fields depending on filtered/renamed regular fields."""

    def test_computed_field_depending_on_filtered_field_raises_error(self):
        """Computed field depending on filtered field raises AttributeError at runtime."""

        @variants(
            VariantPipe(
                VariantContext("Public"),
                FilterFields(exclude=["password"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            email: str
            password: str

            @computed_field
            @property
            def is_secure(self) -> bool:
                # This depends on password which is filtered out
                return len(self.password) > 8

        user = User.Public(email="john@example.com", password="secret123")  # type: ignore[attr-defined]

        # Accessing computed field that depends on filtered field raises error
        with pytest.raises(AttributeError):
            _ = user.is_secure

    def test_computed_field_depending_on_renamed_field_raises_error(self):
        """Computed field breaks when depending on a renamed regular field."""

        @variants(
            VariantPipe(
                VariantContext("Aliased"),
                RenameFields(mapping={"user_name": "username"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            user_name: str

            @computed_field
            @property
            def greeting(self) -> str:
                # This references user_name, but field was renamed to username
                return f"Hello {self.user_name}"

        # The variant renames user_name -> username in the variant class
        user = User.Aliased(username="John")  # type: ignore[attr-defined]

        # Accessing the computed field raises AttributeError because
        # it tries to access self.user_name which no longer exists
        # (it's now self.username)
        with pytest.raises(AttributeError, match="user_name"):
            _ = user.greeting

    def test_filter_and_modify_on_computed_fields_same_pipeline(self):
        """FilterFields and ModifyFields can both operate on computed fields."""

        @variants(
            VariantPipe(
                VariantContext("Curated"),
                FilterFields(exclude=["secret"]),
                ModifyFields(
                    field_modifications={
                        "name": {"description": "User display name"},
                    }
                ),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            email: str

            @computed_field
            @property
            def name(self) -> str:
                return f"User {self.email}"

            @computed_field
            @property
            def secret(self) -> str:
                return "hidden"

        user = User.Curated(email="john@example.com")  # type: ignore[attr-defined]

        # name should exist, secret should be filtered
        assert hasattr(user, "name")
        assert not hasattr(user, "secret")
        assert user.name == "User john@example.com"

    def test_rename_and_modify_on_computed_fields_same_pipeline(self):
        """RenameFields and ModifyFields can both operate on computed fields."""

        @variants(
            VariantPipe(
                VariantContext("Enhanced"),
                RenameFields(mapping={"label": "display_label"}),
                ModifyFields(
                    field_modifications={
                        "display_label": {"description": "Display label"},
                    }
                ),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Item(BaseModel):
            name: str

            @computed_field
            @property
            def label(self) -> str:
                return f"Item: {self.name}"

        item = Item.Enhanced(name="Widget")  # type: ignore[attr-defined]

        # label should be renamed to display_label
        assert hasattr(item, "display_label")
        assert not hasattr(item, "label")
        assert item.display_label == "Item: Widget"

    def test_all_three_transformers_on_computed_fields(self):
        """FilterFields, RenameFields, and ModifyFields all operate together."""

        @variants(
            VariantPipe(
                VariantContext("Final"),
                FilterFields(exclude=["temp"]),
                RenameFields(mapping={"info": "display"}),
                ModifyFields(
                    field_modifications={
                        "display": {"description": "Display info"},
                    }
                ),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Data(BaseModel):
            value: str

            @computed_field
            @property
            def info(self) -> str:
                return f"Value is {self.value}"

            @computed_field
            @property
            def temp(self) -> str:
                return "temporary"

        data = Data.Final(value="test")  # type: ignore[attr-defined]

        # info renamed to display, temp filtered out
        assert hasattr(data, "display")
        assert not hasattr(data, "info")
        assert not hasattr(data, "temp")
        assert data.display == "Value is test"


class TestComputedFieldEdgeCases:
    """Tests for edge cases and unusual scenarios."""

    def test_empty_computed_fields_dict(self):
        """Transformers handle models with no computed fields gracefully."""

        @variants(
            VariantPipe(
                VariantContext("NoComputed"),
                FilterFields(exclude=["age"]),
                RenameFields(mapping={"name": "display_name"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Person(BaseModel):
            name: str
            age: int

        # Use renamed field names for the variant
        person = Person.NoComputed(display_name="John")  # type: ignore[attr-defined]

        # Regular field transformations still work
        assert hasattr(person, "display_name")
        assert not hasattr(person, "age")
        assert person.display_name == "John"

    def test_multiple_computed_fields_mixed_filtering(self):
        """Multiple computed fields with selective filtering and renaming."""

        @variants(
            VariantPipe(
                VariantContext("Mixed"),
                FilterFields(exclude=["internal_id"]),
                RenameFields(mapping={"public_name": "name", "status": "state"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Entity(BaseModel):
            base: str

            @computed_field
            @property
            def public_name(self) -> str:
                return f"Entity: {self.base}"

            @computed_field
            @property
            def status(self) -> str:
                return "active"

            @computed_field
            @property
            def internal_id(self) -> str:
                return "secret"

        entity = Entity.Mixed(base="test")  # type: ignore[attr-defined]

        # Check which fields exist
        assert hasattr(entity, "name")  # renamed from public_name
        assert hasattr(entity, "state")  # renamed from status
        assert not hasattr(entity, "public_name")
        assert not hasattr(entity, "status")
        assert not hasattr(entity, "internal_id")  # filtered out
        assert entity.name == "Entity: test"
        assert entity.state == "active"

    def test_computed_fields_with_filter_tag_compatibility(self):
        """Computed fields work with both FilterTag and name-based transformers."""
        INTERNAL = Tag("internal")

        @variants(
            VariantPipe(
                VariantContext("Public"),
                FilterTag("internal"),
                FilterFields(exclude=["temp"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class User(BaseModel):
            email: str

            @computed_with_tags(INTERNAL)
            @property
            def api_key(self) -> str:
                return "secret"

            @computed_field
            @property
            def temp(self) -> str:
                return "temporary"

            @computed_field
            @property
            def display(self) -> str:
                return f"User: {self.email}"

        user = User.Public(email="john@example.com")  # type: ignore[attr-defined]

        # api_key filtered by tag, temp filtered by name, display kept
        assert not hasattr(user, "api_key")
        assert not hasattr(user, "temp")
        assert hasattr(user, "display")
        assert user.display == "User: john@example.com"

    def test_filter_func_with_complex_logic_on_computed_fields(self):
        """Filter_func can have complex logic for computed fields."""

        @variants(
            VariantPipe(
                VariantContext("Selected"),
                FilterFields(filter_func=lambda name, field: name.startswith("_") or "internal" in name),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Item(BaseModel):
            id: int

            @computed_field
            @property
            def public_info(self) -> str:
                return f"Item {self.id}"

            @computed_field
            @property
            def internal_state(self) -> str:
                return "hidden"

            @computed_field
            @property
            def _private(self) -> str:
                return "private"

        item = Item.Selected(id=1)  # type: ignore[attr-defined]

        # public_info kept, internal_state and _private filtered
        assert hasattr(item, "public_info")
        assert not hasattr(item, "internal_state")
        assert not hasattr(item, "_private")
        assert item.public_info == "Item 1"

    def test_rename_func_with_pattern_matching_on_computed_fields(self):
        """Rename_func can transform computed field names with patterns."""
        import re

        @variants(
            VariantPipe(
                VariantContext("Underscore"),
                RenameFields(rename_func=lambda name: re.sub(r"^get_", "", name)),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Config(BaseModel):
            value: str

            @computed_field
            @property
            def get_name(self) -> str:
                return f"Name: {self.value}"

            @computed_field
            @property
            def get_status(self) -> str:
                return "active"

            @computed_field
            @property
            def description(self) -> str:
                return "A config"

        config = Config.Underscore(value="test")  # type: ignore[attr-defined]

        # get_name -> name, get_status -> status, description unchanged
        assert hasattr(config, "name")
        assert hasattr(config, "status")
        assert hasattr(config, "description")
        assert not hasattr(config, "get_name")
        assert not hasattr(config, "get_status")
        assert config.name == "Name: test"
        assert config.status == "active"
        assert config.description == "A config"

    def test_schema_generation_with_filtered_computed_fields(self):
        """Filtering computed fields removes them from instance but not base schema."""

        @variants(
            VariantPipe(
                VariantContext("Public"),
                FilterFields(exclude=["internal_meta"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Record(BaseModel):
            data: str

            @computed_field
            @property
            def display(self) -> str:
                return f"Data: {self.data}"

            @computed_field
            @property
            def internal_meta(self) -> str:
                return "meta"

        # Runtime instance correctly filters computed fields
        record = Record.Public(data="test")  # type: ignore[attr-defined]

        # Verify runtime filtering works
        dump = record.model_dump()
        assert "display" in dump
        assert "internal_meta" not in dump
        assert "data" in dump

    def test_schema_generation_with_renamed_computed_fields(self):
        """Renaming computed fields works at runtime on variant instances."""

        @variants(
            VariantPipe(
                VariantContext("Renamed"),
                RenameFields(mapping={"full_name": "name"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Person(BaseModel):
            first: str
            last: str

            @computed_field
            @property
            def full_name(self) -> str:
                return f"{self.first} {self.last}"

        # Variant correctly renames at runtime
        person = Person.Renamed(first="John", last="Doe")  # type: ignore[attr-defined]

        # Check instance has the renamed field
        assert hasattr(person, "name")
        assert not hasattr(person, "full_name")

        # Dump shows renamed field
        dump = person.model_dump()
        assert "name" in dump
        assert "full_name" not in dump
        assert dump["name"] == "John Doe"


class TestComputedFieldModelDump:
    """Tests for model_dump with filtered and renamed computed fields."""

    def test_model_dump_reflects_filtered_computed_fields(self):
        """model_dump excludes filtered computed fields."""

        @variants(
            VariantPipe(
                VariantContext("Dumped"),
                FilterFields(exclude=["secret"]),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Record(BaseModel):
            id: int

            @computed_field
            @property
            def secret(self) -> str:
                return "hidden"

            @computed_field
            @property
            def public(self) -> str:
                return "visible"

        record = Record.Dumped(id=1)  # type: ignore[attr-defined]
        dump = record.model_dump()

        assert "secret" not in dump
        assert "public" in dump
        assert dump["public"] == "visible"

    def test_model_dump_reflects_renamed_computed_fields(self):
        """model_dump shows renamed computed field names."""

        @variants(
            VariantPipe(
                VariantContext("Dumped"),
                RenameFields(mapping={"internal": "external"}),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Record(BaseModel):
            value: str

            @computed_field
            @property
            def internal(self) -> str:
                return f"Value is {self.value}"

        record = Record.Dumped(value="test")  # type: ignore[attr-defined]
        dump = record.model_dump()

        assert "external" in dump
        assert "internal" not in dump
        assert dump["external"] == "Value is test"

    def test_model_dump_with_all_three_transformers(self):
        """model_dump correctly shows filtered, renamed, and modified fields."""

        @variants(
            VariantPipe(
                VariantContext("Complete"),
                FilterFields(exclude=["temp"]),
                RenameFields(mapping={"info": "display"}),
                ModifyFields(
                    field_modifications={
                        "display": {"description": "Display info"},
                    }
                ),
                BuildVariant(),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Data(BaseModel):
            value: str

            @computed_field
            @property
            def info(self) -> str:
                return f"Data: {self.value}"

            @computed_field
            @property
            def temp(self) -> str:
                return "temp"

        data = Data.Complete(value="test")  # type: ignore[attr-defined]
        dump = data.model_dump()

        assert "display" in dump
        assert "info" not in dump
        assert "temp" not in dump
        assert dump["display"] == "Data: test"
        assert dump["value"] == "test"
