"""
Integration tests for pipeline composition.
"""

from datetime import datetime
from pydantic import BaseModel

from pydantic_variants import variants, basic_variant_pipeline, VariantPipe, VariantContext
from pydantic_variants.transformers import (
    FilterFields,
    MakeOptional,
    RenameFields,
    ModifyFields,
    SetFields,
    BuildVariant,
    ConnectVariant,
    ModelDict,
)
from pydantic_variants.transformers.extract_variant import ExtractVariant


class TestPipelineComposition:
    """Tests for composing complex pipelines."""

    def test_multiple_pipelines_same_model(self):
        """Multiple pipelines create multiple variants on same model."""
        input_pipe = basic_variant_pipeline("Input", FilterFields(exclude=["id", "created_at"]))
        output_pipe = basic_variant_pipeline("Output", FilterFields(exclude=["password_hash"]))
        update_pipe = basic_variant_pipeline("Update", FilterFields(exclude=["id"]), MakeOptional(all=True))

        @variants(input_pipe, output_pipe, update_pipe)
        class User(BaseModel):
            id: int
            username: str
            email: str
            password_hash: str
            created_at: datetime

        # All three variants should exist
        assert hasattr(User, "Input")  # type: ignore[attr-defined]
        assert hasattr(User, "Output")  # type: ignore[attr-defined]
        assert hasattr(User, "Update")  # type: ignore[attr-defined]

        # Each should have correct fields
        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "created_at" not in User.Input.model_fields  # type: ignore[attr-defined]

        assert "password_hash" not in User.Output.model_fields  # type: ignore[attr-defined]
        assert "id" in User.Output.model_fields  # type: ignore[attr-defined]

        assert "id" not in User.Update.model_fields  # type: ignore[attr-defined]
        assert User.Update.model_fields["username"].default is None  # type: ignore[attr-defined]

    def test_pipeline_reuse_across_models(self):
        """Same pipeline can be applied to different models."""
        input_pipe = basic_variant_pipeline("Input", FilterFields(exclude=["id", "created_at"]), MakeOptional(all=True))

        @variants(input_pipe)
        class User(BaseModel):
            id: int
            name: str
            email: str
            created_at: datetime

        @variants(input_pipe)
        class Product(BaseModel):
            id: int
            name: str
            price: float
            created_at: datetime

        # Both should have Input variant with same behavior
        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert "id" not in Product.Input.model_fields  # type: ignore[attr-defined]

        assert User.Input.model_fields["name"].default is None  # type: ignore[attr-defined]
        assert Product.Input.model_fields["name"].default is None  # type: ignore[attr-defined]

    def test_chained_transformers_order(self):
        """Transformers execute in correct order."""
        # First filter, then make optional, then rename
        pipe = basic_variant_pipeline(
            "Test", FilterFields(exclude=["secret"]), MakeOptional(all=True), RenameFields(mapping={"user_name": "name"})
        )

        @variants(pipe)
        class User(BaseModel):
            id: int
            user_name: str
            secret: str

        # secret should be filtered out
        assert "secret" not in User.Test.model_fields  # type: ignore[attr-defined]
        # user_name should be renamed to name
        assert "name" in User.Test.model_fields  # type: ignore[attr-defined]
        assert "user_name" not in User.Test.model_fields  # type: ignore[attr-defined]
        # Should be optional
        assert User.Test.model_fields["name"].default is None  # type: ignore[attr-defined]

    def test_pipeline_with_all_transformer_types(self):
        """Pipeline using multiple transformer types together."""
        from pydantic.fields import FieldInfo

        pipe = basic_variant_pipeline(
            "Complete",
            FilterFields(exclude=["internal_id"]),
            MakeOptional(exclude=["id"]),
            RenameFields(mapping={"user_email": "email"}),
            ModifyFields(field_modifications={"name": {"description": "User's name"}}),
            SetFields({"version": FieldInfo(annotation=int, default=1)}),
            ModelDict(lambda c: {**c, "extra": "forbid"}),
        )

        @variants(pipe)
        class User(BaseModel):
            id: int
            name: str
            user_email: str
            internal_id: str

        fields = User.Complete.model_fields  # type: ignore[attr-defined]

        # Check all transformations applied
        assert "internal_id" not in fields  # FilterFields
        assert "id" in fields and fields["id"].is_required()  # MakeOptional exclude
        assert "name" in fields and fields["name"].default is None  # MakeOptional
        assert "email" in fields  # RenameFields
        assert fields["name"].description == "User's name"  # ModifyFields
        assert "version" in fields  # SetFields
        # ModelDict effect would be on config

    def test_pipeline_append_modify(self):
        """Can modify pipelines with append/insert/replace."""
        base_pipe = basic_variant_pipeline("Base", FilterFields(exclude=["id"]))

        # Create a modified pipeline
        extended_pipe = VariantPipe(
            VariantContext("Extended"),
            FilterFields(exclude=["id"]),
            MakeOptional(all=True),  # Added
            BuildVariant(),
            ConnectVariant(),
            ExtractVariant(),
        )

        @variants(base_pipe)
        class User1(BaseModel):
            id: int
            name: str

        @variants(extended_pipe)
        class User2(BaseModel):
            id: int
            name: str

        # Base variant should have required name
        assert User1.Base.model_fields["name"].is_required()  # type: ignore[attr-defined]
        # Extended variant should have optional name
        assert User2.Extended.model_fields["name"].default is None  # type: ignore[attr-defined]

    def test_custom_pipeline_without_helper(self):
        """Building pipeline manually without basic_variant_pipeline."""
        pipe = VariantPipe(
            VariantContext("Manual"),
            FilterFields(exclude=["password"]),
            MakeOptional(include_only=["bio"]),
            BuildVariant(),
            ConnectVariant(),
            ExtractVariant(),
        )

        @variants(pipe)
        class User(BaseModel):
            id: int
            name: str
            password: str
            bio: str

        fields = User.Manual.model_fields  # type: ignore[attr-defined]

        assert "password" not in fields
        assert fields["id"].is_required()
        assert fields["name"].is_required()
        assert fields["bio"].default is None  # Optional

    def test_reusable_transformer_components(self):
        """Can define reusable transformer lists."""
        # Reusable component lists
        api_input_transformers = [FilterFields(exclude=["id", "created_at", "updated_at"]), MakeOptional(exclude=["email"])]

        public_output_transformers = [FilterFields(exclude=["password_hash", "internal_notes"])]

        # Compose into pipelines
        user_input = basic_variant_pipeline("Input", *api_input_transformers)
        user_output = basic_variant_pipeline("Output", *public_output_transformers)

        @variants(user_input, user_output)
        class User(BaseModel):
            id: int
            email: str
            name: str
            password_hash: str
            internal_notes: str
            created_at: datetime
            updated_at: datetime

        # Input should exclude system fields, email required
        assert "id" not in User.Input.model_fields  # type: ignore[attr-defined]
        assert User.Input.model_fields["email"].is_required()  # type: ignore[attr-defined]
        assert User.Input.model_fields["name"].default is None  # type: ignore[attr-defined]

        # Output should exclude sensitive fields
        assert "password_hash" not in User.Output.model_fields  # type: ignore[attr-defined]
        assert "internal_notes" not in User.Output.model_fields  # type: ignore[attr-defined]
