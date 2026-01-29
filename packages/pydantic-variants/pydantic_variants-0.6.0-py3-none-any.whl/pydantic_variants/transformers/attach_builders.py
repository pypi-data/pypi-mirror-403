"""Attach standard builder methods to variant class.

This transformer attaches two methods to the variant class:
- `from_main(instance)`: Classmethod to create variant from main model instance
- `to_main()`: Instance method to convert variant back to main model

The methods use the variant name as context when calling model_dump, allowing
serializers to check which variant is being built.
"""

from typing import Self

from pydantic import BaseModel

from pydantic_variants.core import DecomposedModel, ModelTransformer, VariantContext


def _make_from_main(variant_name: str, main_class: type[BaseModel]):
    """Create a from_main classmethod for the variant."""

    @classmethod
    def from_main(cls, instance: BaseModel) -> Self:
        """Create variant instance from main model instance.

        Uses model_dump with context={'variant': 'VariantName'} to allow
        serializers to conditionally include/exclude fields.
        """
        data = instance.model_dump(context={"variant": variant_name})
        return cls.model_validate(data)

    from_main.__func__.__name__ = "from_main"
    from_main.__func__.__doc__ = f"Create {variant_name} from {main_class.__name__} instance."
    return from_main


def _make_to_main(variant_name: str, main_class: type[BaseModel]):
    """Create a to_main instance method for the variant."""

    def to_main(self) -> BaseModel:
        """Convert variant instance back to main model.

        Uses model_dump with context={'variant': 'VariantName'} to allow
        serializers to conditionally include/exclude fields.
        """
        data = self.model_dump(context={"variant": variant_name})
        return main_class.model_validate(data)

    to_main.__name__ = "to_main"
    to_main.__doc__ = f"Convert {variant_name} back to {main_class.__name__}."
    return to_main


class AttachBuilders(ModelTransformer):
    """
    Attaches standard builder methods to variant class.

    After BuildVariant, this transformer attaches to the variant class:
    - `VariantClass.from_main(instance)`: Create variant from main model instance
    - `variant_instance.to_main()`: Convert variant back to main model

    Both methods call model_dump with context={'variant': 'VariantName'},
    allowing serializers/validators to check which variant is being built.

    Args:
        add_from_main: Whether to add from_main classmethod (default: True)
        add_to_main: Whether to add to_main instance method (default: True)

    Raises:
        ValueError: If current_variant is not yet built (use after BuildVariant)

    Example:
        VariantPipe(
            VariantContext("Public"),
            FilterTag([INTERNAL, USER_PRIVATE]),
            BuildVariant(),
            ConnectVariant(),
            AttachBuilders(),  # Adds Public.from_main() and public.to_main()
            ExtractVariant(),
        )

        # Usage:
        user = User(name="John", password="secret")
        public = User.Public.from_main(user)  # Create Public from User
        user_back = public.to_main()  # Convert back to User
    """

    def __init__(
        self,
        *,
        add_from_main: bool = True,
        add_to_main: bool = True,
    ):
        self.add_from_main = add_from_main
        self.add_to_main = add_to_main

    def __call__(self, context: VariantContext) -> VariantContext:
        if isinstance(context.current_variant, DecomposedModel):
            raise ValueError("AttachBuilders requires built model. Use BuildVariant before AttachBuilders.")

        variant_name = context.name
        variant_class = context.current_variant
        main_class = context.original_model

        # Attach from_main() classmethod to variant class
        if self.add_from_main:
            from_method = _make_from_main(variant_name, main_class)
            setattr(variant_class, "from_main", from_method)

        # Attach to_main() instance method to variant class
        if self.add_to_main:
            to_method = _make_to_main(variant_name, main_class)
            setattr(variant_class, "to_main", to_method)

        return context

        return context
