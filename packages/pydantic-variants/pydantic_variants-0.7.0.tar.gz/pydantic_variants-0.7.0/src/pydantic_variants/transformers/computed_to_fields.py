"""
Transformer to convert computed fields to regular fields for output models.

This is useful when:
- Computed fields depend on internal/excluded fields that won't be available in variants
- You want the computed value captured during serialization and included as a regular field
- The variant is for API responses where the value should be pre-computed
"""

from copy import copy
from typing import Callable, Iterable, Union

from pydantic.fields import ComputedFieldInfo, FieldInfo, Field

from pydantic_variants.core import DecomposedModel, ModelTransformer, VariantContext
from pydantic_variants.transformers.filter_tag import Tag


# Type for filter function: takes (name, info) and returns True if field should be converted
ComputedFilterFunc = Callable[[str, ComputedFieldInfo], bool]


class ComputedToFields(ModelTransformer):
    """
    Converts computed fields to regular fields in a DecomposedModel.
    
    This transformer removes selected computed fields and creates corresponding
    regular FieldInfo definitions. This is useful for output models where:
    - The computed field depends on internal fields that are excluded from the variant
    - You want the computed value as a regular serializable field
    
    The new field uses:
    - The computed field's return_type as annotation
    - The computed field's docstring (from wrapped_property) as description
    - Optional default value (typically None for output-only fields)
    
    Args:
        include: Tags, tag keys, or callable to filter which computed fields to convert.
                 If None, converts ALL computed fields.
        exclude: Tags, tag keys, or callable to exclude from conversion.
                 Applied after include filter.
    
    Raises:
        ValueError: If not operating on a DecomposedModel
    
    Example:
        # Convert all computed fields tagged with USER_PRIVATE
        ComputedToFields(include=USER_PRIVATE)
        
        # Convert all computed fields except those tagged INTERNAL
        ComputedToFields(exclude=INTERNAL)
        
        # Use callable for complex logic
        ComputedToFields(include=lambda name, info: name.startswith('has_'))
        
        # Convert ALL computed fields
        ComputedToFields()
    """

    def __init__(
        self,
        include: Union[Tag, str, Iterable[Union[Tag, str]], ComputedFilterFunc, None] = None,
        exclude: Union[Tag, str, Iterable[Union[Tag, str]], ComputedFilterFunc, None] = None,
    ):
        self.include_filter = self._make_filter(include) if include is not None else None
        self.exclude_filter = self._make_filter(exclude) if exclude is not None else None

    def _make_filter(
        self, 
        spec: Union[Tag, str, Iterable[Union[Tag, str]], ComputedFilterFunc]
    ) -> ComputedFilterFunc:
        """Convert various filter specifications to a callable."""
        if callable(spec) and not isinstance(spec, Tag):
            return spec
        
        # Build set of tag keys to match
        if isinstance(spec, (Tag, str)):
            keys = {spec.key if isinstance(spec, Tag) else spec}
        else:
            keys = {s.key if isinstance(s, Tag) else s for s in spec}
        
        def tag_filter(name: str, info: ComputedFieldInfo) -> bool:
            """Check if computed field has any of the specified tags."""
            if not info.json_schema_extra or not isinstance(info.json_schema_extra, dict):
                return False
            pv_tags = info.json_schema_extra.get('pv_tags', [])
            return any(tag_key in keys for tag_key in pv_tags)
        
        return tag_filter

    def _should_convert(self, name: str, info: ComputedFieldInfo) -> bool:
        """Determine if a computed field should be converted to a regular field."""
        # If include filter specified, field must pass it
        if self.include_filter is not None:
            if not self.include_filter(name, info):
                return False
        
        # If exclude filter specified, field must NOT match it
        if self.exclude_filter is not None:
            if self.exclude_filter(name, info):
                return False
        
        return True

    def __call__(self, context: VariantContext) -> VariantContext:
        if not isinstance(context.current_variant, DecomposedModel):
            raise ValueError("ComputedToFields transformer requires DecomposedModel, got built model")

        decorators = context.current_variant._pydantic_decorators
        computed_fields = copy(decorators.computed_fields)
        new_model_fields = copy(context.current_variant.model_fields)
        
        fields_to_remove = []
        
        for name, decorator in computed_fields.items():
            info = decorator.info
            
            if not self._should_convert(name, info):
                continue
            
            # Extract information from computed field
            return_type = info.return_type
            description = None
            
            # Try to get description from the wrapped property's docstring
            if info.wrapped_property and info.wrapped_property.fget:
                description = info.wrapped_property.fget.__doc__
            
            # Fall back to explicit description
            if not description and info.description:
                description = info.description
            
            # Create a new regular FieldInfo
            # Use None as default since this is an output-only field
            new_field = FieldInfo(
                default=None,
                annotation=return_type,
                description=description,
                alias=info.alias,
                title=info.title,
            )
            
            # Add to model fields
            new_model_fields[name] = new_field
            
            # Mark computed field for removal
            fields_to_remove.append(name)
        
        # Remove converted computed fields
        for name in fields_to_remove:
            del computed_fields[name]
        
        decorators.computed_fields = computed_fields
        context.current_variant.model_fields = new_model_fields
        
        return context
