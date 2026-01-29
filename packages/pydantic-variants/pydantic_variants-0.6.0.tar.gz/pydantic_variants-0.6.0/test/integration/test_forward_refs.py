"""
Integration tests for forward references and delayed builds.
"""

from typing import List, Optional
from pydantic import BaseModel

from pydantic_variants import variants, basic_variant_pipeline
from pydantic_variants.transformers import FilterFields, SwitchVariant


class TestForwardRefs:
    """Tests for handling forward references."""

    def test_delayed_build_basic(self):
        """delayed_build=True delays variant creation."""

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class User(BaseModel):
            id: int
            name: str

        # Variant should not exist yet
        assert not hasattr(User, "Input") or not hasattr(User.Input, "model_fields")  # type: ignore[attr-defined]

        # Build should exist
        assert hasattr(User, "_build_variants")

        # After calling _build_variants
        User._build_variants()  # type: ignore[attr-defined]

        assert hasattr(User, "Input")
        assert "name" in User.Input.model_fields  # type: ignore[attr-defined]

    def test_forward_ref_circular(self):
        """Handles circular forward references."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"]), SwitchVariant("Input")), delayed_build=True)
        class Author(BaseModel):
            id: int
            name: str
            books: List["Book"] = []

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"]), SwitchVariant("Input")), delayed_build=True)
        class Book(BaseModel):
            id: int
            title: str
            author: "Author"

        # Rebuild to resolve forward refs
        Author.model_rebuild()
        Book.model_rebuild()

        # Build variants after resolution
        Author._build_variants()  # type: ignore[attr-defined]
        Book._build_variants()  # type: ignore[attr-defined]

        # Both variants should exist
        assert hasattr(Author, "Input")
        assert hasattr(Book, "Input")

        # Variants are functional even with forward refs
        author = Author.Input(name="John", books=[])  # type: ignore[attr-defined]
        book = Book.Input(title="Test", author=author)  # type: ignore[attr-defined]
        assert book.author.name == "John"

    def test_forward_ref_self(self):
        """Handles self-referencing forward refs."""

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")), delayed_build=True)
        class TreeNode(BaseModel):
            value: str
            children: List["TreeNode"] = []
            parent: Optional["TreeNode"] = None

        TreeNode.model_rebuild()
        TreeNode._build_variants()  # type: ignore[attr-defined]

        # Variant should exist and be functional
        assert hasattr(TreeNode, "Input")

        # Self-refs still point to original type, so we need to use original
        # for nested structures in delayed builds
        root = TreeNode.Input(value="root", children=[])  # type: ignore[attr-defined]
        # For self-referential types, use dicts or original type
        TreeNode(value="child", parent=None)  # Use original type

        # The variant is functional for its fields
        assert root.value == "root"
        assert root.children == []

    def test_multiple_models_forward_refs(self):
        """Multiple models with cross references."""

        @variants(basic_variant_pipeline("API"), delayed_build=True)
        class Comment(BaseModel):
            text: str
            author: "User"

        @variants(basic_variant_pipeline("API"), delayed_build=True)
        class Post(BaseModel):
            title: str
            comments: List["Comment"] = []
            author: "User"

        @variants(basic_variant_pipeline("API", SwitchVariant("API")), delayed_build=True)
        class User(BaseModel):
            name: str
            posts: List["Post"] = []

        # Rebuild all
        Comment.model_rebuild()
        Post.model_rebuild()
        User.model_rebuild()

        # Build variants in order
        Comment._build_variants()  # type: ignore[attr-defined]
        Post._build_variants()  # type: ignore[attr-defined]
        User._build_variants()  # type: ignore[attr-defined]

        assert hasattr(User, "API")
        assert hasattr(Post, "API")
        assert hasattr(Comment, "API")

    def test_delayed_build_preserves_model(self):
        """Original model still works after delayed_build."""

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class User(BaseModel):
            id: int
            name: str

        # Original should work before building variants
        user = User(id=1, name="John")
        assert user.id == 1
        assert user.name == "John"

        # Build variants
        User._build_variants()  # type: ignore[attr-defined]

        # Original should still work
        user2 = User(id=2, name="Jane")
        assert user2.id == 2

    def test_string_forward_reference(self):
        """Handles string forward references."""

        @variants(basic_variant_pipeline("Input", SwitchVariant("Input")), delayed_build=True)
        class Container(BaseModel):
            items: List["Item"]

        @variants(basic_variant_pipeline("Input"), delayed_build=True)
        class Item(BaseModel):
            name: str

        Container.model_rebuild()
        Item.model_rebuild()

        Item._build_variants()  # type: ignore[attr-defined]
        Container._build_variants()  # type: ignore[attr-defined]

        items_type = Container.Input.model_fields["items"].annotation  # type: ignore[attr-defined]
        assert items_type.__args__[0] is Item.Input  # type: ignore[attr-defined]

    def test_functional_after_delayed_build(self):
        """Variants are fully functional after delayed build."""

        @variants(basic_variant_pipeline("Input", FilterFields(exclude=["id"])), delayed_build=True)
        class User(BaseModel):
            id: int
            name: str
            email: str

        User._build_variants()  # type: ignore[attr-defined]

        # Should be able to instantiate
        user = User.Input(name="John", email="john@example.com")  # type: ignore[attr-defined]
        assert user.name == "John"

        # Should validate
        data = user.model_dump()
        assert data == {"name": "John", "email": "john@example.com"}
