"""
Pydantic variants library

A library for creating model variants with transformation pipelines.

Basic Usage:
    ```python
    from pydantic_variants import variants, basic_variant_pipeline
    from pydantic_variants.transformers import FilterFields, MakeOptional

    @variants(
        basic_variant_pipeline('Input',
            FilterFields(exclude=['id']),
            MakeOptional(all=True)
        )
    )
    class User(BaseModel):
        id: int
        name: str
        email: str
    ```

Factory Pattern (recommended for common cases):
    ```python
    from pydantic_variants import create_variant_pipeline, variants

    input_pipe = create_variant_pipeline(
        'Input',
        exclude_fields=['id', 'created_at'],
        exclude_tags=['exclude_from_input'],
    )

    update_pipe = create_variant_pipeline(
        'Update',
        exclude_fields=['id'],
        make_optional=True,
    )

    @variants(input_pipe, update_pipe)
    class User(BaseModel):
        id: int
        name: str
    ```

Forward References:
    ```python
    from pydantic_variants import variants, rebuild_with_variants

    @variants(input_pipe, output_pipe, delayed_build=True)
    class User(BaseModel):
        service: Link['Service']

    # After Service is defined:
    rebuild_with_variants(User, {'_types_namespace': {'Service': Service}})
    ```

Advanced Usage:
    ```python
    from pydantic_variants import VariantPipe, VariantContext
    from pydantic_variants.transformers import *

    custom_pipeline = VariantPipe(
        VariantContext('Custom'),
        FilterFields(exclude=['internal']),
        BuildVariant(),
        ConnectVariant()
    )
    ```
"""

from pydantic_variants.core import VariantContext, VariantPipe
from pydantic_variants.decorators import (
    basic_variant_pipeline,
    create_variant_pipeline,
    rebuild_with_variants,
    variants,
)

__all__ = [
    "VariantContext",
    "VariantPipe",
    "basic_variant_pipeline",
    "create_variant_pipeline",
    "rebuild_with_variants",
    "variants",
]
