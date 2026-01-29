"""
Test that computed_with_tags works with FastAPI OpenAPI schema generation.

This test ensures that Tag instances stored on computed fields don't
cause Pydantic serialization errors during OpenAPI schema generation.
"""

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from pydantic import BaseModel

from pydantic_variants.transformers import Tag, computed_with_tags


INTERNAL = Tag("internal")
USER_PRIVATE = Tag("user_private")


class User(BaseModel):
    """Test model with tagged computed field."""

    id: str
    pin_hash: str | None = None

    @computed_with_tags(USER_PRIVATE, INTERNAL)
    @property
    def has_pin(self) -> bool:
        """Check if user has a PIN set."""
        return self.pin_hash is not None


def test_computed_with_tags_in_fastapi_openapi_generation():
    """Test that computed_with_tags doesn't break OpenAPI schema generation."""
    # Create a FastAPI app with the User model as response_model
    app = FastAPI()

    @app.get("/user", response_model=User)
    async def get_user():
        return User(id="1", pin_hash="hash")

    # This should not raise PydanticSerializationError about Tag serialization
    schema = app.openapi()

    # Verify the schema was generated successfully
    assert "components" in schema
    assert "schemas" in schema["components"]
    assert "User" in schema["components"]["schemas"]

    # Verify has_pin computed field appears in the schema
    user_schema = schema["components"]["schemas"]["User"]
    assert "properties" in user_schema
    assert "has_pin" in user_schema["properties"]

    # Verify has_pin is marked as readOnly (computed field behavior)
    has_pin_schema = user_schema["properties"]["has_pin"]
    assert has_pin_schema.get("readOnly") is True
    assert has_pin_schema.get("type") == "boolean"


def test_computed_with_tags_separate_input_output_schemas_false():
    """Test with separate_input_output_schemas=False (the problematic case)."""
    app = FastAPI(separate_input_output_schemas=False)

    @app.get("/user", response_model=User)
    async def get_user():
        return User(id="1", pin_hash="hash")

    # This previously raised PydanticSerializationError
    schema = app.openapi()

    # Verify schema generation succeeded
    assert "components" in schema
    user_schema = schema["components"]["schemas"]["User"]
    assert "has_pin" in user_schema["properties"]


def test_computed_with_tags_separate_input_output_schemas_true():
    """Test with separate_input_output_schemas=True."""
    app = FastAPI(separate_input_output_schemas=True)

    @app.get("/user", response_model=User)
    async def get_user():
        return User(id="1", pin_hash="hash")

    # Should work in both modes
    schema = app.openapi()

    assert "components" in schema
    user_schema = schema["components"]["schemas"]["User"]
    assert "has_pin" in user_schema["properties"]
