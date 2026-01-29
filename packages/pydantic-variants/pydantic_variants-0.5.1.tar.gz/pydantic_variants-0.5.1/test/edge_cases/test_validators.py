"""
Tests for validators in variants.
"""

import pytest
from pydantic import BaseModel, Field, field_validator, model_validator

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, MakeOptional


class TestValidators:
    """Tests for models with validators."""

    def test_field_validator_inherited(self):
        """Field validators are inherited by variants."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            name: str
            email: str

            @field_validator("name")
            @classmethod
            def validate_name(cls, v):
                if not v.strip():
                    raise ValueError("Name cannot be empty")
                return v.title()

            @field_validator("email")
            @classmethod
            def validate_email(cls, v):
                if "@" not in v:
                    raise ValueError("Invalid email format")
                return v.lower()

        # Validators should work on variant
        user = User.Input(name="john doe", email="JOHN@EXAMPLE.COM")  # type: ignore[attr-defined]
        assert user.name == "John Doe"  # title() applied
        assert user.email == "john@example.com"  # lower() applied

        # Validation errors should also work
        with pytest.raises(Exception):  # ValidationError
            User.Input(name="", email="test@example.com")  # type: ignore[attr-defined]

    def test_model_validator_inherited(self):
        """Model validators are inherited by variants."""

        @variants(basic_variant_pipeline("Input"))
        class PasswordForm(BaseModel):
            password: str
            confirm_password: str

            @model_validator(mode="after")
            def validate_passwords_match(self):
                if self.password != self.confirm_password:
                    raise ValueError("Passwords do not match")
                return self

        # Should pass when passwords match
        form = PasswordForm.Input(password="secret123", confirm_password="secret123")  # type: ignore[attr-defined]
        assert form.password == "secret123"

        # Should fail when passwords don't match
        with pytest.raises(Exception):  # ValidationError
            PasswordForm.Input(password="secret123", confirm_password="different")  # type: ignore[attr-defined]

    def test_validator_on_filtered_field_not_called(self):
        """Validator for filtered field doesn't break variant."""
        validator_called = False

        @variants(basic_variant_pipeline("Public", FilterFields(exclude=["internal_id"])))
        class User(BaseModel):
            name: str
            internal_id: str

            @field_validator("internal_id")
            @classmethod
            def validate_internal_id(cls, v):
                nonlocal validator_called
                validator_called = True
                if not v.startswith("INT-"):
                    raise ValueError("Internal ID must start with INT-")
                return v

        # Creating variant without internal_id should work
        user = User.Public(name="John")  # type: ignore[attr-defined]
        assert user.name == "John"
        assert not validator_called  # Validator not called for filtered field

    def test_validator_with_optional_field(self):
        """Validators work with fields made optional."""

        @variants(basic_variant_pipeline("Update", MakeOptional(all=True)))
        class User(BaseModel):
            name: str
            age: int

            @field_validator("name")
            @classmethod
            def validate_name(cls, v):
                if v is not None and len(v) < 2:
                    raise ValueError("Name too short")
                return v

            @field_validator("age")
            @classmethod
            def validate_age(cls, v):
                if v is not None and v < 0:
                    raise ValueError("Age cannot be negative")
                return v

        # Should accept None values
        user = User.Update()  # type: ignore[attr-defined]
        assert user.name is None
        assert user.age is None

        # Should validate when value provided
        user2 = User.Update(name="Jo", age=25)  # type: ignore[attr-defined]
        assert user2.name == "Jo"

        with pytest.raises(Exception):  # ValidationError
            User.Update(age=-5)  # type: ignore[attr-defined]

    def test_before_validator(self):
        """Before validators work on variants."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            tags: list[str]

            @field_validator("tags", mode="before")
            @classmethod
            def parse_tags(cls, v):
                if isinstance(v, str):
                    return [t.strip() for t in v.split(",")]
                return v

        # Should parse comma-separated string
        user = User.Input(tags="python, coding, test")  # type: ignore[attr-defined]
        assert user.tags == ["python", "coding", "test"]

        # Should also accept list directly
        user2 = User.Input(tags=["a", "b"])  # type: ignore[attr-defined]
        assert user2.tags == ["a", "b"]

    def test_multiple_field_validators(self):
        """Multiple validators on same field work."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            email: str

            @field_validator("email")
            @classmethod
            def lowercase(cls, v):
                return v.lower()

            @field_validator("email")
            @classmethod
            def strip_whitespace(cls, v):
                return v.strip()

        user = User.Input(email="  JOHN@EXAMPLE.COM  ")  # type: ignore[attr-defined]
        assert user.email == "john@example.com"

    def test_validator_with_field_info(self):
        """Validators work alongside field constraints."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            score: int = Field(ge=0, le=100)

            @field_validator("score")
            @classmethod
            def double_score(cls, v):
                # This runs after field constraints pass
                return v * 2 if v <= 50 else v  # Only double if <= 50

        user = User.Input(score=50)  # Within constraints  # type: ignore[attr-defined]
        assert user.score == 100  # Doubled by validator

        # Field constraints are validated first, so this works
        user2 = User.Input(score=75)  # Within constraints but > 50  # type: ignore[attr-defined]
        assert user2.score == 75  # Not doubled

    def test_wrap_validator(self):
        """Wrap mode validators work."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            value: int

            @field_validator("value", mode="wrap")
            @classmethod
            def wrap_value(cls, v, handler):
                # Add custom logic before/after standard validation
                result = handler(v)
                return result * 2

        user = User.Input(value=5)  # type: ignore[attr-defined]
        assert user.value == 10
