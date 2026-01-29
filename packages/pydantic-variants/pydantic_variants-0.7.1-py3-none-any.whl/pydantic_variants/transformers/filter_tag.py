from typing import Callable, Iterable, Union

from pydantic.fields import ComputedFieldInfo, FieldInfo
from pydantic import computed_field

from pydantic_variants.core import DecomposedModel, ModelTransformer, VariantContext


class Tag:
    """Tag class for marking fields with metadata keys.

    Can be used with Annotated or Field(metadata=[...]):
        - Annotated[int, Tag('internal')]  -> stored in field.metadata
        - Field(metadata=[Tag('internal')]) -> stored in json_schema_extra['metadata']

    Convenience constructors for semantic clarity:
        - Tag.exclude('internal') - create tag for exclusion filtering
        - Tag.include('public') - create tag for inclusion filtering
    """

    def __init__(self, key: str):
        self.key = key

    def __eq__(self, other):
        return isinstance(other, Tag) and self.key == other.key

    def __hash__(self):
        return hash(self.key)

    def __repr__(self):
        return f"Tag('{self.key}')"

    @classmethod
    def exclude(cls, key: str) -> "Tag":
        """Create a tag intended for exclusion filtering.

        This is semantically equivalent to Tag(key), but makes the intent clear.

        Example:
            exclude_input = Tag.exclude('exclude_from_input')
            class User(BaseModel):
                password: Annotated[str, exclude_input]  # Will be filtered out
        """
        return cls(key)

    @classmethod
    def include(cls, key: str) -> "Tag":
        """Create a tag intended for inclusion filtering.

        This is semantically equivalent to Tag(key), but makes the intent clear.

        Example:
            public_field = Tag.include('public')
            class User(BaseModel):
                name: Annotated[str, public_field]  # Will be included
        """
        return cls(key)

    def in_field(self, field: FieldInfo | ComputedFieldInfo) -> bool:
        """Check if this tag is present in the field's metadata.

        Handles both Annotated metadata and Field(metadata=[...]) which
        Pydantic stores in json_schema_extra['metadata'].

        For ComputedFieldInfo, checks for pv_tags in json_schema_extra.
        """
        # ComputedFieldInfo - check json_schema_extra['pv_tags'] (stored as strings)

        if isinstance(field, ComputedFieldInfo):
            if field.json_schema_extra and isinstance(field.json_schema_extra, dict):
                pv_tags = field.json_schema_extra.get("pv_tags", [])
                assert type(pv_tags) is list and all(isinstance(tag, str) for tag in pv_tags)
                return self.key in pv_tags
            return False

        # Check regular metadata (from Annotated)
        if hasattr(field, "metadata") and field.metadata:
            if any(isinstance(item, Tag) and item == self for item in field.metadata):
                return True

        # Check json_schema_extra['metadata'] (from Field(metadata=[...]))
        if field.json_schema_extra and isinstance(field.json_schema_extra, dict):
            extra_metadata = field.json_schema_extra.get("metadata", [])
            if any(isinstance(item, Tag) and item == self for item in extra_metadata):  # type: ignore[attr-defined]
                return True

        return False


class FilterTag(ModelTransformer):
    """
    Filters out fields that have Tag instances in their metadata matching the specified keys.

    Searches through field metadata for Tag instances and removes fields where any
    Tag.key matches the provided filter keys.

    Args:
        keys: Single key string, Tag instance, or iterable of key strings/Tags to filter out

    Raises:
        ValueError: If not operating on a DecomposedModel

    Example:
        # Filter fields tagged with 'internal' (string)
        FilterTag('internal')

        # Filter using Tag instance directly
        exclude_input = Tag('exclude_from_input')
        FilterTag(exclude_input)

        # Filter fields tagged with multiple keys
        FilterTag(['internal', 'deprecated', 'admin_only'])

        # Mix Tag instances and strings
        FilterTag([exclude_input, 'deprecated'])

        # Usage with Field metadata
        class User(BaseModel):
            id: int = Field(metadata=[Tag('internal')])
            name: str
            email: str = Field(metadata=[Tag('admin_only')])
    """

    def __init__(self, keys: Union[str, "Tag", Iterable[Union[str, "Tag"]]]):
        if isinstance(keys, str):
            self.filter_keys = {keys}
        elif isinstance(keys, Tag):
            self.filter_keys = {keys.key}
        else:
            # Iterable of strings or Tags
            self.filter_keys = {k.key if isinstance(k, Tag) else k for k in keys}

    def __call__(self, context: VariantContext) -> VariantContext:
        if not isinstance(context.current_variant, DecomposedModel):
            raise ValueError("FilterByTags transformer requires DecomposedModel, got built model")

        # Filter regular fields
        new_fields = {}
        for name, field in context.current_variant.model_fields.items():
            if not self._has_matching_tag(field):
                new_fields[name] = field

        context.current_variant.model_fields = new_fields

        # Filter computed fields
        decorators = context.current_variant._pydantic_decorators
        new_computed = {}
        for name, dec in decorators.computed_fields.items():
            if not self._computed_has_matching_tag(dec.info):
                new_computed[name] = dec

        decorators.computed_fields = new_computed
        return context

    def _has_matching_tag(self, field: FieldInfo) -> bool:
        """Check if field has any Tag in metadata that matches our filter keys.

        Handles both:
        - Annotated[int, Tag('x')] -> stored in field.metadata
        - Field(metadata=[Tag('x')]) -> stored in json_schema_extra['metadata']
        """
        # Check regular metadata (from Annotated)
        if field.metadata:
            for metadata_item in field.metadata:
                if isinstance(metadata_item, Tag) and metadata_item.key in self.filter_keys:
                    return True

        # Check json_schema_extra['metadata'] (from Field(metadata=[...]))
        if field.json_schema_extra and isinstance(field.json_schema_extra, dict):
            extra_metadata = field.json_schema_extra.get("metadata", [])
            for metadata_item in extra_metadata:  # type: ignore[attr-defined]
                if isinstance(metadata_item, Tag) and metadata_item.key in self.filter_keys:
                    return True

        return False

    def _computed_has_matching_tag(self, info: ComputedFieldInfo) -> bool:
        """Check if computed field has any tag matching our filter keys.

        Tags are stored in json_schema_extra['pv_tags'] as strings.
        """
        if not info.json_schema_extra or not isinstance(info.json_schema_extra, dict):
            return False

        pv_tags = info.json_schema_extra.get("pv_tags", [])
        assert type(pv_tags) is list and all(isinstance(tag, str) for tag in pv_tags)
        has_match = any(tag_key in self.filter_keys for tag_key in pv_tags)

        return has_match


def computed_with_tags(*tags: Tag, **kwargs) -> Callable[[property], property]:
    """Decorator helper for tagging computed fields with FilterTag-compatible tags.

    Wraps @computed_field to store tags in json_schema_extra['pv_tags'] for filtering.

    Args:
        *tags: One or more Tag instances to attach to the computed field
        **kwargs: Additional keyword arguments passed to @computed_field

    Returns:
        Decorator function for use with @property

    Raises:
        ValueError: If no tags are provided
        TypeError: If any tag is not a Tag instance, or decorator not applied to property

    Example:
        INTERNAL = Tag('internal')
        USER_PRIVATE = Tag('user_private')

        class User(BaseModel):
            name: str

            @computed_with_tags(INTERNAL)
            @property
            def debug_info(self) -> str:
                return f"Debug: {self.name}"

            @computed_with_tags(USER_PRIVATE, INTERNAL)
            @property
            def full_details(self) -> str:
                return self.name

    Note:
        Must be applied BEFORE @property:
            @computed_with_tags(INTERNAL)  # First
            @property                       # Second
            def my_field(self) -> str: ...
    """
    if not tags:
        raise ValueError("computed_with_tags requires at least one Tag instance")

    for tag in tags:
        if not isinstance(tag, Tag):
            raise TypeError("computed_with_tags expects Tag instances, not other types")

    def decorator(func: property) -> property:
        if not isinstance(func, property):
            raise TypeError("computed_with_tags must be applied to a property")

        # Store tag keys (not Tag objects) as strings for JSON serialization
        tag_keys = [tag.key for tag in tags]

        # Merge with any existing json_schema_extra kwargs
        schema_extra = kwargs.get("json_schema_extra", {})
        schema_extra["pv_tags"] = tag_keys
        kwargs["json_schema_extra"] = schema_extra

        # Apply @computed_field with json_schema_extra containing tag keys
        computed_prop = computed_field(**kwargs)(func)

        return computed_prop

    return decorator
