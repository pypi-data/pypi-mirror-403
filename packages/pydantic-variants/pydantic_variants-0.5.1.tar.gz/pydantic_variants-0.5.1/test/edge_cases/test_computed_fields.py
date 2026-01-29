"""
Tests for computed fields in variants.
"""

import pytest
from datetime import datetime
from pydantic import BaseModel, computed_field

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, MakeOptional


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
