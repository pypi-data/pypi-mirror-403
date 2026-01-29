"""Tests for AttachBuilders transformer."""

import pytest
from pydantic import BaseModel, SerializationInfo, field_serializer

from pydantic_variants.core import VariantContext
from pydantic_variants.transformers import AttachBuilders, BuildVariant, ConnectVariant, FilterFields


class TestAttachBuilders:
    """Tests for AttachBuilders transformer."""

    def test_attach_builders_adds_from_main(self):
        """Test that from_main classmethod is added to variant."""

        class User(BaseModel):
            name: str
            email: str

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders()(ctx)

        assert hasattr(User.Public, "from_main")  # type: ignore[attr-defined]
        assert callable(getattr(User.Public, "from_main"))  # type: ignore[attr-defined]

    def test_attach_builders_adds_to_main(self):
        """Test that to_main instance method is added to variant."""

        class User(BaseModel):
            name: str
            email: str

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders()(ctx)

        user = User(name="John", email="john@example.com")
        public = User.Public.from_main(user)  # type: ignore[attr-defined]

        assert hasattr(public, "to_main")
        assert callable(getattr(public, "to_main"))

    def test_from_main_works(self):
        """Test that from_main classmethod creates correct variant."""

        class User(BaseModel):
            name: str
            password: str

        ctx = VariantContext("Public")(User)
        ctx = FilterFields(exclude=["password"])(ctx)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders()(ctx)

        user = User(name="John", password="secret")
        public = User.Public.from_main(user)  # type: ignore[attr-defined]

        assert public.name == "John"
        assert not hasattr(public, "password")
        assert type(public).__name__ == "UserPublic"

    def test_to_main_works(self):
        """Test that to_main instance method converts back to main."""

        class User(BaseModel):
            name: str
            email: str = "default@example.com"

        ctx = VariantContext("Public")(User)
        ctx = FilterFields(exclude=["email"])(ctx)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders()(ctx)

        user = User(name="John", email="john@example.com")
        public = User.Public.from_main(user)  # type: ignore[attr-defined]
        user_back = public.to_main()  # type: ignore[attr-defined]

        assert user_back.name == "John"
        assert user_back.email == "default@example.com"  # Uses default since filtered out
        assert isinstance(user_back, User)

    def test_context_contains_variant_name(self):
        """Test that model_dump context contains variant name."""
        context_captured = {}

        class User(BaseModel):
            name: str
            secret: str

            @field_serializer("secret")
            def hide_secret(self, value: str, info: SerializationInfo) -> str:
                if info.context:
                    context_captured.update(info.context)
                    if info.context.get("variant") == "Public":
                        return "***"
                return value

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders()(ctx)

        user = User(name="John", secret="password123")
        public = User.Public.from_main(user)  # type: ignore[attr-defined]

        assert context_captured.get("variant") == "Public"
        assert public.secret == "***"

    def test_error_on_decomposed(self):
        """Test error when used before BuildVariant."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Public")(User)
        # Not calling BuildVariant - still DecomposedModel

        with pytest.raises(ValueError, match="requires built model"):
            AttachBuilders()(ctx)

    def test_disable_from_main(self):
        """Test disabling from_main method."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders(add_from_main=False)(ctx)

        assert not hasattr(User.Public, "from_main")  # type: ignore[attr-defined]

    def test_disable_to_main(self):
        """Test disabling to_main method."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        ctx = AttachBuilders(add_to_main=False)(ctx)

        user = User(name="John")
        public = User.Public.from_main(user)  # type: ignore[attr-defined]
        assert not hasattr(public, "to_main")

    def test_returns_context(self):
        """Test that AttachBuilders returns the context."""

        class User(BaseModel):
            name: str

        ctx = VariantContext("Public")(User)
        ctx = BuildVariant()(ctx)
        ctx = ConnectVariant()(ctx)
        result = AttachBuilders()(ctx)

        assert result is ctx

    def test_multiple_variants(self):
        """Test multiple variants get their own methods."""

        class User(BaseModel):
            name: str
            email: str
            password: str

        # Create Public variant (no password)
        ctx1 = VariantContext("Public")(User)
        ctx1 = FilterFields(exclude=["password"])(ctx1)
        ctx1 = BuildVariant()(ctx1)
        ctx1 = ConnectVariant()(ctx1)
        ctx1 = AttachBuilders()(ctx1)

        # Create Private variant (all fields)
        ctx2 = VariantContext("Private")(User)
        ctx2 = BuildVariant()(ctx2)
        ctx2 = ConnectVariant()(ctx2)
        ctx2 = AttachBuilders()(ctx2)

        user = User(name="John", email="john@example.com", password="secret")

        public = User.Public.from_main(user)  # type: ignore[attr-defined]
        private = User.Private.from_main(user)  # type: ignore[attr-defined]

        assert not hasattr(public, "password")
        assert hasattr(private, "password")
        assert private.password == "secret"
