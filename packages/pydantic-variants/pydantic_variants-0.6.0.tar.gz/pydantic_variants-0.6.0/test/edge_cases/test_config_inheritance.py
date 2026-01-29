"""
Tests for model_config and ConfigDict inheritance.
"""

import pytest
from pydantic import BaseModel, ConfigDict, Field

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import SetAttribute, ModelDict


class TestConfigDictInheritance:
    """Tests that model_config is properly inherited."""

    def test_config_preserved_in_variant(self):
        """Base model config is preserved in variants."""

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            model_config = ConfigDict(str_strip_whitespace=True, validate_default=True)

            name: str
            email: str

        # Config should be inherited
        assert User.Input.model_config.get("str_strip_whitespace") is True  # type: ignore[attr-defined]

        # Whitespace stripping should work
        user = User.Input(name="  John  ", email="test@example.com")  # type: ignore[attr-defined]
        assert user.name == "John"

    def test_frozen_config_preserved(self):
        """Frozen config is preserved in variants."""

        @variants(basic_variant_pipeline("Input"))
        class ImmutableData(BaseModel):
            model_config = ConfigDict(frozen=True)

            value: int

        data = ImmutableData.Input(value=42)  # type: ignore[attr-defined]

        with pytest.raises(Exception):
            data.value = 100

    def test_extra_forbid_preserved(self):
        """extra='forbid' is preserved."""

        @variants(basic_variant_pipeline("Input"))
        class Strict(BaseModel):
            model_config = ConfigDict(extra="forbid")

            name: str

        with pytest.raises(Exception):
            Strict.Input(name="test", unknown_field="value")  # type: ignore[attr-defined]

    def test_extra_allow_preserved(self):
        """extra='allow' is preserved."""

        @variants(basic_variant_pipeline("Input"))
        class Flexible(BaseModel):
            model_config = ConfigDict(extra="allow")

            name: str

        flex = Flexible.Input(name="test", extra_field="value")  # type: ignore[attr-defined]
        assert flex.name == "test"
        assert flex.extra_field == "value"

    def test_populate_by_name_preserved(self):
        """populate_by_name is preserved."""

        @variants(basic_variant_pipeline("Input"))
        class AliasModel(BaseModel):
            model_config = ConfigDict(populate_by_name=True)

            user_name: str = Field(alias="userName")

        # Can use either name
        m1 = AliasModel.Input(userName="John")  # type: ignore[attr-defined]
        m2 = AliasModel.Input(user_name="Jane")  # type: ignore[attr-defined]

        assert m1.user_name == "John"
        assert m2.user_name == "Jane"

    def test_config_can_be_modified_via_modeldict(self):
        """ModelDict can modify config."""

        @variants(basic_variant_pipeline("Input", ModelDict(lambda cfg: {**cfg, "frozen": True})))
        class MutableBase(BaseModel):
            model_config = ConfigDict(frozen=False)

            value: int

        # Base is mutable
        base = MutableBase(value=1)
        base.value = 2
        assert base.value == 2

        # Variant is frozen
        variant = MutableBase.Input(value=1)  # type: ignore[attr-defined]
        with pytest.raises(Exception):
            variant.value = 2

    def test_multiple_config_options_preserved(self):
        """Multiple config options are preserved together."""

        @variants(basic_variant_pipeline("Input"))
        class ComplexConfig(BaseModel):
            model_config = ConfigDict(
                str_strip_whitespace=True, str_to_lower=True, validate_default=True, from_attributes=True, strict=False
            )

            code: str

        config = ComplexConfig.Input.model_config  # type: ignore[attr-defined]

        assert config.get("str_strip_whitespace") is True
        assert config.get("str_to_lower") is True
        assert config.get("validate_default") is True
        assert config.get("from_attributes") is True

    def test_from_attributes_works_in_variant(self):
        """from_attributes works for constructing from objects."""

        class UserObj:
            def __init__(self, name, email):
                self.name = name
                self.email = email

        @variants(basic_variant_pipeline("Input"))
        class User(BaseModel):
            model_config = ConfigDict(from_attributes=True)

            name: str
            email: str

        obj = UserObj("John", "john@example.com")
        user = User.Input.model_validate(obj)  # type: ignore[attr-defined]

        assert user.name == "John"
        assert user.email == "john@example.com"

    def test_title_config_preserved(self):
        """title config is preserved."""

        @variants(basic_variant_pipeline("Input"))
        class MyModel(BaseModel):
            model_config = ConfigDict(title="My Custom Model")

            data: str

        schema = MyModel.Input.model_json_schema()  # type: ignore[attr-defined]
        assert schema.get("title") == "My Custom Model"


class TestConfigOverrides:
    """Tests for config overrides via transformers."""

    def test_modeldict_adds_new_config(self):
        """ModelDict can add new config options."""

        @variants(
            basic_variant_pipeline("Output", ModelDict(lambda cfg: {**cfg, "json_schema_extra": {"examples": [{"name": "Example"}]}}))
        )
        class Simple(BaseModel):
            name: str

        schema = Simple.Output.model_json_schema()  # type: ignore[attr-defined]
        assert "examples" in schema

    def test_modeldict_overrides_existing(self):
        """ModelDict overrides existing config."""

        @variants(basic_variant_pipeline("Output", ModelDict(lambda cfg: {**cfg, "extra": "allow"})))
        class Strict(BaseModel):
            model_config = ConfigDict(extra="forbid")

            name: str

        # Original is strict
        with pytest.raises(Exception):
            Strict(name="test", extra="value")  # type: ignore[attr-defined]

        # Variant allows extra
        out = Strict.Output(name="test", extra="value")  # type: ignore[attr-defined]
        assert out.extra == "value"

    def test_set_attribute_on_variant(self):
        """SetAttribute can modify variant model attributes."""
        from pydantic_variants import VariantPipe
        from pydantic_variants.transformers import BuildVariant, ConnectVariant, ExtractVariant
        from pydantic_variants.core import VariantContext

        # SetAttribute must be used after BuildVariant
        @variants(
            VariantPipe(
                VariantContext("Input"),
                BuildVariant(),
                SetAttribute(variant_attrs={"__doc__": "Modified docstring"}),
                ConnectVariant(),
                ExtractVariant(),
            )
        )
        class Documented(BaseModel):
            model_config = ConfigDict(title="Original Title")
            """Original docstring."""

            value: str

        # Config title unchanged
        schema = Documented.Input.model_json_schema()  # type: ignore[attr-defined]
        assert schema.get("title") == "Original Title"

        # But doc was modified
        assert Documented.Input.__doc__ == "Modified docstring"  # type: ignore[attr-defined]


class TestConfigWithInheritance:
    """Tests for config inheritance across model hierarchies."""

    def test_child_model_config_in_variant(self):
        """Child model config is preserved in variants."""

        class BaseUser(BaseModel):
            model_config = ConfigDict(str_strip_whitespace=True)
            name: str

        @variants(basic_variant_pipeline("Input"))
        class AdminUser(BaseUser):
            model_config = ConfigDict(
                str_strip_whitespace=True,  # Inherited
                extra="forbid",  # New
            )
            role: str = "admin"

        # Both configs should apply
        admin = AdminUser.Input(name="  Admin  ", role="superadmin")  # type: ignore[attr-defined]
        assert admin.name == "Admin"

        with pytest.raises(Exception):
            AdminUser.Input(name="Admin", role="admin", unknown="value")  # type: ignore[attr-defined]

    def test_config_merge_in_hierarchy(self):
        """Config is properly merged in model hierarchy."""

        class Level1(BaseModel):
            model_config = ConfigDict(validate_default=True)
            a: str = "default"

        class Level2(Level1):
            model_config = ConfigDict(validate_default=True, str_strip_whitespace=True)
            b: str = "  "

        @variants(basic_variant_pipeline("Input"))
        class Level3(Level2):
            c: str

        # All configs should be active
        item = Level3.Input(c="test")  # type: ignore[attr-defined]
        assert item.a == "default"
        # strip_whitespace affects b's default
        assert item.b.strip() == ""
