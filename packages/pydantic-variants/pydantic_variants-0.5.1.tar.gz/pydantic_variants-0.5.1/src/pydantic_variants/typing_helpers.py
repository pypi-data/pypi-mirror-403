"""Type stubs for variant type hints."""

from typing import TypeVar

from pydantic import BaseModel
from typing_extensions import ParamSpec

T_co = TypeVar("T_co", bound=BaseModel, covariant=True)
T = TypeVar("T", bound=BaseModel)
P = ParamSpec("P")


class VariantClass(BaseModel):
    """Protocol for a variant class with builder methods.

    Variant classes created by AttachBuilders have:
    - from_main(instance): Classmethod to create variant from main model instance
    - to_main(): Instance method to convert variant back to main model
    """

    @classmethod
    def from_main(cls: type[T], instance: BaseModel) -> T:
        """Create variant from main model instance."""
        ...

    def to_main(self) -> BaseModel:
        """Convert variant back to main model."""
        ...


class HasVariants:
    """Protocol for a class with dynamically created variants.

    This helps type checkers understand variant attributes.
    Classes decorated with @variants get variant classes attached.
    Each variant has from_main() and to_main() methods added by AttachBuilders.

    Example:
        @variants(basic_variant_pipeline('Public'))
        class User(BaseModel):
            name: str

        # Now type checkers understand:
        User.Public  # type: type[VariantClass]
        public = User.Public.from_main(user)  # Create Public from User
        user_back = public.to_main()  # Convert back to User
    """

    # Common variant names - add more as needed
    Create: type[VariantClass]
    Update: type[VariantClass]
    Public: type[VariantClass]
    Private: type[VariantClass]
    Team: type[VariantClass]
    MsgOutput: type[VariantClass]
    UserSide: type[VariantClass]
    ServiceSide: type[VariantClass]


def cast_variant_class(cls: type[T_co]) -> type[T_co]:
    """Helper to cast a variants-decorated class for type checking.

    Use this to help Pylance understand variant attributes:

    Example:
        User = cast_variant_class(User)
        public = User.Public.from_main(user)  # Now properly typed!
    """
    return cls
