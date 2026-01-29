"""
Schema utility functions for Pydantic model variants.

This module contains helper functions for working with variant models.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel


def convert_to_variant(self: "BaseModel", variant_name: str) -> "BaseModel":
    """
    Convert an instance to one of its variant types.

    Args:
        self: The model instance to convert
        variant_name: Name of the variant to convert to

    Returns:
        New instance of the variant model

    Raises:
        AttributeError: If _variants dict doesn't exist
        KeyError: If variant_name not found in _variants

    Example:
        user = User(id=1, name="John", email="john@example.com")
        user_output = convert_to_variant(user, 'Output')
    """
    if not hasattr(self.__class__, "_variants"):
        raise AttributeError(f"{self.__class__.__name__} has no _variants attribute")

    variant_cls = self.__class__._variants.get(variant_name)  # type: ignore
    if variant_cls is None:
        raise KeyError(f"Variant '{variant_name}' not found in {self.__class__.__name__}._variants")

    return variant_cls(**self.model_dump())
